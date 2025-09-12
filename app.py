import os
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
import openai
import httpx
import traceback
import sys
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

# Print key runtime info (without leaking secrets)
print("=== Runtime Info ===")
print("Working Dir:", os.getcwd())
print("Python:", sys.version.split(" ")[0])

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")


def init_db():
    try:
        db_path = os.getenv("DB_PATH", "jarvis.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Try to add is_admin column if missing
        try:
            cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            conn.commit()
        except Exception:
            pass
        conn.commit()
    except Exception as e:
        print("DB init error:", e)
    finally:
        try:
            conn.close()
        except Exception:
            pass


init_db()
def ensure_admin_user():
    try:
        uname = os.getenv("ADMIN_USERNAME", "admin")
        pwd = os.getenv("ADMIN_PASSWORD", "Rebel_0102")
        if not uname or not pwd:
            return
        db_path = os.getenv("DB_PATH", "jarvis.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username = ?', (uname,))
        row = cur.fetchone()
        pwd_hash = generate_password_hash(pwd)
        if row:
            cur.execute('UPDATE users SET password_hash = ?, is_admin = 1 WHERE id = ?', (pwd_hash, row[0]))
        else:
            cur.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)', (uname, pwd_hash))
        conn.commit()
    except Exception as e:
        print('Admin seed error:', e)
    finally:
        try:
            conn.close()
        except Exception:
            pass

ensure_admin_user()

# Provider selection and configuration
provider = os.getenv("LLM_PROVIDER", "openai").lower()
model_name = os.getenv("MODEL_NAME")  # optional override
allowed_models_env = os.getenv("COPILOT_ALLOWED_MODELS")  # comma-separated or '*'

print("\n=== LLM Provider Configuration ===")
print("Provider:", provider)

if provider == "copilot":
    # GitHub Models via Azure AI Inference (OpenAI-compatible-ish)
    # Use direct HTTP calls; endpoint typically doesn't include `/v1` and uses Bearer token.
    copilot_token = os.getenv("GITHUB_TOKEN") or os.getenv("COPILOT_TOKEN")
    copilot_api_base = os.getenv("COPILOT_API_BASE", "https://models.inference.ai.azure.com")
    # No default model: require explicit selection per request or via env var
    effective_model = model_name or os.getenv("COPILOT_MODEL")
    print("Using Copilot (GitHub Models)")
    print("API key present:", bool(copilot_token))
    print("API base:", copilot_api_base)
    # Build allowed models list for UI population
    default_model_list = [
        "gpt-4o",
        "gpt-4o-mini",
        "o4-mini",
        "o3-mini",
        "Llama-3.1-8B-Instruct",
        "Llama-3.1-70B-Instruct",
        "Mistral-large",
        "Phi-4-mini",
    ]
    if allowed_models_env:
        if allowed_models_env.strip() == "*":
            allowed_models = default_model_list
        else:
            allowed_models = [m.strip() for m in allowed_models_env.split(",") if m.strip()]
    else:
        allowed_models = default_model_list
else:
    # Default: OpenAI platform
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # api_base can be overridden for Azure OpenAI or proxies
    if os.getenv("OPENAI_API_BASE"):
        openai.api_base = os.getenv("OPENAI_API_BASE")
    # No default model: require explicit selection per request or via env var
    effective_model = model_name or os.getenv("OPENAI_MODEL")
    print("Using OpenAI Platform")
    print("API key present:", bool(openai.api_key))
    print("API base:", getattr(openai, "api_base", "default"))
    allowed_models = []  # not used for OpenAI path

@app.route('/')
def home():
    return render_template('home.html')

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/chat', methods=['GET', 'POST', 'OPTIONS'])
def chat():
    if request.method == 'GET':
        if not session.get('user_id'):
            return redirect(url_for('login_page'))
        return render_template('index.html')
    if request.method == 'OPTIONS':
        return ('', 204)
    try:
        if not session.get('user_id'):
            return jsonify({'status': 'error', 'error': 'Unauthorized'}), 401
        data = request.json
        user_message = data.get('message', '')
        requested_model = data.get('model') if isinstance(data, dict) else None
        
        if provider == "copilot":
            if not (os.getenv("GITHUB_TOKEN") or os.getenv("COPILOT_TOKEN")):
                raise ValueError("Copilot token not set. Define GITHUB_TOKEN or COPILOT_TOKEN")
        else:
            if not openai.api_key:
                raise ValueError("OpenAI API key not set. Define OPENAI_API_KEY")
            
        print(f"\n=== Processing Message ===")
        print(f"Message: {user_message}")
        if provider != "copilot" and isinstance(openai.api_key, str) and len(openai.api_key) >= 8:
            print(f"Using API key: {openai.api_key[:8]}...")
        # Model selection: request override > env
        selected_model = requested_model or effective_model
        if not selected_model:
            return jsonify({
                'error': 'No model selected. Please choose a model before sending.',
                'allowed_models': allowed_models if provider == 'copilot' else None,
                'status': 'error'
            }), 400
        if provider == "copilot" and allowed_models_env and allowed_models_env.strip() != "*":
            if selected_model not in allowed_models:
                return jsonify({
                    'error': f"Model '{selected_model}' not in allowed set.",
                    'allowed_models': allowed_models,
                    'status': 'error'
                }), 400
        print(f"Provider: {provider} | Model: {selected_model}")
        
        # Get response from selected provider
        try:
            if provider == "copilot":
                # POST to /chat/completions with Bearer token
                url = f"{copilot_api_base.rstrip('/')}/chat/completions"
                token = (os.getenv('GITHUB_TOKEN') or os.getenv('COPILOT_TOKEN'))
                auth_scheme = os.getenv('COPILOT_AUTH_SCHEME', 'bearer').lower()
                if auth_scheme == 'api-key':
                    headers = {
                        "api-key": token,
                        "Content-Type": "application/json",
                    }
                else:
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                base_payload = {
                    "model": selected_model,
                    "messages": [
                        {"role": "system", "content": "You are Jarvis, a helpful AI assistant."},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.7,
                }
                # Choose token param based on model or override
                token_param = os.getenv('COPILOT_TOKEN_PARAM')
                if not token_param:
                    sml = selected_model.lower()
                    token_param = 'max_completion_tokens' if (sml.startswith('o3') or sml.startswith('o4')) else 'max_tokens'

                def build_payload(tp):
                    p = dict(base_payload)
                    p[tp] = 512
                    return p

                with httpx.Client(timeout=60) as client:
                    r = client.post(url, headers=headers, json=build_payload(token_param))
                    if r.status_code == 400 and 'max_tokens' in r.text and token_param == 'max_tokens':
                        # Retry with alternate key for O-models
                        r = client.post(url, headers=headers, json=build_payload('max_completion_tokens'))
                    elif r.status_code == 400 and 'max_completion_tokens' in r.text and token_param == 'max_completion_tokens':
                        # Retry fallback to classic key
                        r = client.post(url, headers=headers, json=build_payload('max_tokens'))

                if r.status_code >= 400:
                    raise RuntimeError(f"Copilot API error {r.status_code}: {r.text}")
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                return jsonify({"response": content, "status": "success"})
            else:
                response = openai.ChatCompletion.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are Jarvis, a helpful AI assistant."},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=512,
                    temperature=0.7
                )
                return jsonify({
                    'response': response.choices[0].message.content,
                    'status': 'success'
                })
        except openai.error.AuthenticationError as e:
            print("Authentication Error:", str(e))
            raise
        except openai.error.APIError as e:
            print("API Error:", str(e))
            raise
        except Exception as e:
            print("Unexpected OpenAI Error:", str(e))
            raise
            
    except Exception as e:
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)  # Print to stderr for better visibility in logs
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/models', methods=['GET', 'OPTIONS'])
def models():
    if request.method == 'OPTIONS':
        return ('', 204)
    return jsonify({
        'provider': provider,
        'allowed_models': allowed_models if provider == 'copilot' else None,
        'note': "Allowed models list is indicative; actual access is governed by your GitHub token permissions.",
    })

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')
    # POST
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''
    if not username or not password:
        return render_template('login.html', error='Username and password are required.')
    try:
        conn = sqlite3.connect('jarvis.db')
        cur = conn.cursor()
        cur.execute('SELECT id, password_hash, COALESCE(is_admin, 0) FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
    finally:
        conn.close()
    if not row or not check_password_hash(row[1], password):
        return render_template('login.html', error='Invalid username or password.')
    session['user_id'] = row[0]
    session['username'] = username
    session['is_admin'] = bool(row[2])
    return redirect(url_for('chat'))

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'GET':
        return render_template('signup.html')
    # POST
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''
    confirm = request.form.get('confirm') or ''
    if not username or not password:
        return render_template('signup.html', error='Username and password are required.')
    if password != confirm:
        return render_template('signup.html', error='Passwords do not match.')
    try:
        conn = sqlite3.connect('jarvis.db')
        cur = conn.cursor()
        is_admin = 1 if username.lower() == 'admin' else 0
        cur.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)', (username, generate_password_hash(password), is_admin))
        conn.commit()
        cur.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cur.fetchone()
    except sqlite3.IntegrityError:
        return render_template('signup.html', error='Username already exists.')
    finally:
        conn.close()
    session['user_id'] = user[0]
    session['username'] = username
    session['is_admin'] = bool(is_admin)
    return redirect(url_for('chat'))

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('home'))

# -------- Admin Dashboard --------
def _ensure_admin():
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    return None

@app.route('/admin')
def admin_root():
    guard = _ensure_admin()
    if guard:
        return guard
    return redirect(url_for('admin_users'))

@app.route('/admin/users')
def admin_users():
    guard = _ensure_admin()
    if guard:
        return guard
    db_path = os.getenv("DB_PATH", "jarvis.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT id, username, COALESCE(is_admin,0), created_at FROM users ORDER BY id ASC')
    users = [
        { 'id': r[0], 'username': r[1], 'is_admin': bool(r[2]), 'created_at': r[3] }
        for r in cur.fetchall()
    ]
    conn.close()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/<int:user_id>', methods=['GET', 'POST'])
def admin_edit_user(user_id: int):
    guard = _ensure_admin()
    if guard:
        return guard
    db_path = os.getenv("DB_PATH", "jarvis.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    if request.method == 'POST':
        new_username = (request.form.get('username') or '').strip()
        new_password = request.form.get('password') or ''
        is_admin_flag = 1 if request.form.get('is_admin') == 'on' else 0
        if not new_username:
            conn.close()
            return render_template('admin_edit_user.html', error='Username is required.', user={'id': user_id, 'username': new_username, 'is_admin': bool(is_admin_flag)})
        try:
            if new_password:
                cur.execute('UPDATE users SET username = ?, password_hash = ?, is_admin = ? WHERE id = ?',
                            (new_username, generate_password_hash(new_password), is_admin_flag, user_id))
            else:
                cur.execute('UPDATE users SET username = ?, is_admin = ? WHERE id = ?',
                            (new_username, is_admin_flag, user_id))
            conn.commit()
            # If editing current user, sync session
            if session.get('user_id') == user_id:
                session['username'] = new_username
                session['is_admin'] = bool(is_admin_flag)
            conn.close()
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('admin_edit_user.html', error='Username already exists.', user={'id': user_id, 'username': new_username, 'is_admin': bool(is_admin_flag)})
    # GET
    cur.execute('SELECT id, username, COALESCE(is_admin,0) FROM users WHERE id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return redirect(url_for('admin_users'))
    user = { 'id': row[0], 'username': row[1], 'is_admin': bool(row[2]) }
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
def admin_delete_user(user_id: int):
    guard = _ensure_admin()
    if guard:
        return guard
    db_path = os.getenv("DB_PATH", "jarvis.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Prevent deleting the last admin account
    cur.execute('SELECT COUNT(*) FROM users WHERE COALESCE(is_admin,0)=1')
    admin_count = cur.fetchone()[0]
    cur.execute('SELECT COALESCE(is_admin,0) FROM users WHERE id = ?', (user_id,))
    row = cur.fetchone()
    is_target_admin = bool(row[0]) if row else False
    if is_target_admin and admin_count <= 1:
        conn.close()
        return redirect(url_for('admin_users'))
    cur.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    if session.get('user_id') == user_id:
        session.clear()
        return redirect(url_for('home'))
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=== Starting Server ===")
    print(f"Port: {port}")
    app.run(host='0.0.0.0', port=port) 