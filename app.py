import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai
import traceback
import sys

# Load environment variables
load_dotenv()

# Print all environment variables (excluding sensitive values)
print("=== Environment Variables ===")
for key in os.environ:
    if 'KEY' in key or 'SECRET' in key:
        print(f"{key}: {'*' * 8}")
    else:
        print(f"{key}: {os.environ[key]}")

app = Flask(__name__)

# Initialize OpenAI
api_key = os.getenv('OPENAI_API_KEY')
print("\n=== OpenAI Configuration ===")
print("API Key present:", bool(api_key))
if not api_key:
    print("ERROR: OPENAI_API_KEY environment variable is not set!")
    print("Please set OPENAI_API_KEY in your Render environment variables")
else:
    print(f"API Key found: {api_key[:8]}...")

openai.api_key = api_key

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not openai.api_key:
            raise ValueError("OpenAI API key is not set")
            
        print(f"\n=== Processing Message ===")
        print(f"Message: {user_message}")
        print(f"Using API key: {openai.api_key[:8]}...")
        
        # Get response from OpenAI
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=== Starting Server ===")
    print(f"Port: {port}")
    app.run(host='0.0.0.0', port=port) 