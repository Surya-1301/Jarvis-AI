# Jarvis 2025

A modern voice-controlled AI assistant built with Python, featuring hotword detection, OpenAI integration, and a web-based interface.

## Features

- Voice activation with hotword detection ("jarvis" or "alexa")
- OpenAI GPT integration for natural language processing
- Web-based user interface
- WhatsApp integration for messaging and calls
- YouTube video playback
- System command execution
- Contact management

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Picovoice access key
- PyAudio
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Jarvis-2025.git
cd Jarvis-2025
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your API keys:
- Add your OpenAI API key in the appropriate configuration file
- Add your Picovoice access key for hotword detection

## Usage

1. Start the assistant:
```bash
python backend/feature.py
```

2. Activate the assistant by saying "jarvis" or "alexa"

3. Give voice commands or use the web interface

## Project Structure

```
Jarvis-2025/
├── backend/
│   ├── feature.py      # Main functionality
│   ├── command.py      # Command processing
│   ├── config.py       # Configuration
│   └── helper.py       # Helper functions
├── frontend/
│   ├── assets/         # Static assets
│   └── index.html      # Web interface
└── requirements.txt    # Dependencies
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT integration
- Picovoice for hotword detection
- All contributors and users of the project 