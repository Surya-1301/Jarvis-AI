import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        # Get response from OpenAI
        response = client.chat.completions.create(
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
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 