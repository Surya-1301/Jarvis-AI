import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Assistant Configuration
ASSISTANT_NAME = os.getenv('ASSISTANT_NAME', 'jarvis')

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PICOVOICE_ACCESS_KEY = os.getenv('PICOVOICE_ACCESS_KEY')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///jarvis.db')

# Audio Configuration
AUDIO_DEVICE_INDEX = int(os.getenv('AUDIO_DEVICE_INDEX', '0'))
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', '16000'))
CHANNELS = int(os.getenv('CHANNELS', '1'))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'jarvis.log')