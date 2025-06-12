import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("WARNING: OPENAI_API_KEY environment variable is not set!")
else:
    print(f"OpenAI API Key found: {api_key[:8]}...")  # Print first 8 chars for verification
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
            
        print(f"Processing message: {user_message}")
        
        # Get response from OpenAI
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
    except Exception as e:
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # Print full error with traceback
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 