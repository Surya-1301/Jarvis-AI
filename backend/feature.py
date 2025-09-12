import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import time
import atexit
import sqlite3
import pygame
import webbrowser
import subprocess
from datetime import datetime
from backend.command import speak
from backend.config import ASSISTANT_NAME
from backend.helper import extract_yt_term, remove_words
import pyautogui
import pywhatkit as kit
import pvporcupine
import pyaudio
import struct
import hugchat
import eel
import openai
import httpx

# Initialize pygame mixer
pygame.mixer.init()

# SQLite connection
conn = sqlite3.connect("jarvis.db")
cursor = conn.cursor()

# Register cleanup function
def cleanup():
    if conn:
        conn.close()
    if pygame.mixer.get_init():
        pygame.mixer.quit()

atexit.register(cleanup)

# Define the function to play sound
@eel.expose
def play_assistant_sound():
    try:
        sound_file = r"/Users/shubham/Jarvis-2025-master/frontend/assets/audio/start_sound.mp3"
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing sound: {e}")

# Function to open commands (apps or websites)
def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")
    query = query.lower().strip()

    if not query:
        speak("Please specify what to open")
        return

    try:
        cursor.execute('SELECT path FROM sys_command WHERE name IN (?)', (query,))
        results = cursor.fetchall()

        if results:
            speak(f"Opening {query}")
            os.system(f'open "{results[0][0]}"')
            return

        cursor.execute('SELECT url FROM web_command WHERE name IN (?)', (query,))
        results = cursor.fetchall()

        if results:
            speak(f"Opening {query}")
            webbrowser.open(results[0][0])
            return

        speak(f"Opening {query}")
        try:
            os.system(f'open {query}')
        except FileNotFoundError:
            speak(f"Could not find {query}")
        except PermissionError:
            speak(f"Permission denied to open {query}")
        except Exception as e:
            speak(f"Error opening {query}: {str(e)}")

    except sqlite3.Error as e:
        speak("Database error occurred")
        print(f"Database error: {e}")
    except Exception as e:
        speak("An unexpected error occurred")
        print(f"Error: {e}")

# Function to play YouTube videos based on query
def PlayYoutube(query):
    try:
        search_term = extract_yt_term(query)
        speak(f"Playing {search_term} on YouTube")
        kit.playonyt(search_term)
    except Exception as e:
        speak("Error playing YouTube video")
        print(f"YouTube error: {e}")

# Function to listen for hotword ("jarvis" or "alexa")
def hotword():
    porcupine = None
    paud = None
    audio_stream = None
    
    try:
        # Replace 'YOUR_ACCESS_KEY' with your actual Picovoice access key
        porcupine = pvporcupine.create(
            access_key='ZiS8TaEHPkh0pJfCJcPLheyG+UMIhoJZccxPRyK8bJrUnvNzJiK3zA==',
            keywords=["jarvis", "alexa"]
        )
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
            input_device_index=None,  # Use default input device
            stream_callback=None,     # No callback
            start=False              # Don't start immediately
        )
        
        # Start the stream
        audio_stream.start_stream()

        while True:
            try:
                keyword = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)
                keyword_index = porcupine.process(keyword)

                if keyword_index >= 0:
                    print("Hotword detected")
                    pyautogui.keyDown("win")
                    pyautogui.press("j")
                    time.sleep(2)
                    pyautogui.keyUp("win")
            except IOError as e:
                if e.errno == -9981:  # Input overflow
                    print("Audio buffer overflow, continuing...")
                    continue
                else:
                    raise
                
    except Exception as e:
        print(f"Error in hotword detection: {e}")
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.stop_stream()
            audio_stream.close()
        if paud is not None:
            paud.terminate()

# Function to find contact from the contacts database
def findContact(query):
    words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'whatsapp', 'video']
    query = remove_words(query, words_to_remove)

    try:
        query = query.strip().lower()
        cursor.execute("SELECT Phone FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
        results = cursor.fetchall()

        if results:
            mobile_number_str = str(results[0][0])
            if not mobile_number_str.startswith('+91'):
                mobile_number_str = '+91' + mobile_number_str
            return mobile_number_str, query
        else:
            speak('Contact not found.')
            return None, None
    except sqlite3.Error as e:
        speak('Database error occurred while searching for contact.')
        print(f"Database error: {e}")
        return None, None
    except Exception as e:
        speak('An error occurred while searching for contact.')
        print(f"Error: {e}")
        return None, None

# Function to send WhatsApp message or make a call
def whatsApp(Phone, message, flag, name):
    try:
        if not Phone:
            speak("No phone number provided")
            return

        if flag == 'message':
            target_tab = 12
            jarvis_message = f"Message sent successfully to {name}"
            # TODO: Implement actual WhatsApp message sending
            speak(jarvis_message)

        elif flag == 'call':
            target_tab = 7
            message = ''
            jarvis_message = f"Calling {name}"
            # TODO: Implement actual WhatsApp calling
            speak(jarvis_message)
        else:
            speak("Invalid flag provided")
    except Exception as e:
        speak("Error in WhatsApp operation")
        print(f"WhatsApp error: {e}")

class OpenAIChat:
    def __init__(self, api_key: str | None = None, model: str = "gpt-3.5-turbo"):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = model
        if self.provider == "copilot":
            self.token = os.getenv("GITHUB_TOKEN") or os.getenv("COPILOT_TOKEN")
            self.api_base = os.getenv("COPILOT_API_BASE", "https://models.inference.ai.azure.com")
            if model == "gpt-3.5-turbo":
                # Default to a reasonable Copilot model if caller uses old default
                self.model = os.getenv("COPILOT_MODEL", "gpt-4o-mini")
        else:
            # OpenAI path
            if api_key:
                openai.api_key = api_key
            elif os.getenv("OPENAI_API_KEY"):
                openai.api_key = os.getenv("OPENAI_API_KEY")
            if os.getenv("OPENAI_API_BASE"):
                openai.api_base = os.getenv("OPENAI_API_BASE")

    def chat(self, user_message: str, system_prompt: str = "You are a helpful assistant."):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        try:
            if self.provider == "copilot":
                if not self.token:
                    return "Error: Copilot token not set (GITHUB_TOKEN or COPILOT_TOKEN)."
                url = f"{self.api_base.rstrip('/')}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 512,
                    "temperature": 0.7,
                }
                with httpx.Client(timeout=60) as client:
                    r = client.post(url, headers=headers, json=payload)
                if r.status_code >= 400:
                    return f"Error: Copilot API {r.status_code}: {r.text}"
                data = r.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=512,
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {e}"

if __name__ == "__main__":
    # Example: test hotword detection
    hotword()

    # Example: test chat functionality
    provider = os.getenv('LLM_PROVIDER', 'openai')
    print(f"Testing provider: {provider}")
    chat = OpenAIChat(api_key=os.getenv('OPENAI_API_KEY'))
    response = chat.chat("Hello, how are you?")
    print(response)
