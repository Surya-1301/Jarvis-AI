import time
from feature import OpenAIChat, hotword
import threading

def test_openai_chat():
    print("\nTesting OpenAI Chat...")
    try:
        # TODO: Replace this with your actual OpenAI API key
        # Get your API key from: https://platform.openai.com/account/api-keys
        chat = OpenAIChat(api_key="org-H1hlyH0mn7JA90dokUXtQvJg")  # Replace this line with your actual API key
        
        # Test a simple message
        response = chat.chat("Hello, this is a test message.")
        print("OpenAI Response:", response)
        print("OpenAI Chat Test: PASSED\n")
    except Exception as e:
        print("OpenAI Chat Test: FAILED")
        print(f"Error: {e}\n")

def test_hotword():
    print("Testing Hotword Detection...")
    print("Say 'jarvis' or 'alexa' to test...")
    print("Press Ctrl+C to stop the test")
    
    try:
        hotword()
    except KeyboardInterrupt:
        print("\nHotword Test: STOPPED by user")
    except Exception as e:
        print("Hotword Test: FAILED")
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting Feature Tests...")
    
    # Test OpenAI Chat in a separate thread
    chat_thread = threading.Thread(target=test_openai_chat)
    chat_thread.start()
    chat_thread.join()
    
    # Test Hotword Detection
    test_hotword() 