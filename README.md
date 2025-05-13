# Music Transcriber & SATB Parts Converter

A web application that provides two main capabilities:  
1. Convert MP3 files into SATB (Soprano, Alto, Tenor, Bass) music parts with browser-based playback  
2. Record audio and identify matching songs via Spotify

## Features

- SATB Part Generation:  
  - Upload an MP3 and automatically transcribe it into four-part harmony (Soprano, Alto, Tenor, Bass)  
  - Export the transcription to MusicXML or MIDI  
  - Convert MusicXML to audio files for easy playback  

- Music Recognition:  
  - Press "Record" to capture short audio using your microphone  
  - Transcribe recorded audio automatically  
  - Search for the recognized music on Spotify  

- Web Interface:  
  - Flask-based server with a user-friendly interface  
  - Support for simultaneous playback of multiple parts  

- Command Line Tools (CLI):  
  - Script-based SATB generation  
  - Part playback utilities  
  - Audio recording helper scripts  

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/parts-of-music-transcriber.git
   cd parts-of-music-transcriber
   ```
2. Create & activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. (Optional) Install system dependencies (Linux example):
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-dev python3-tk portaudio19-dev fluidsynth \
       libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
       libfreetype6-dev libportmidi-dev ffmpeg
   ```
5. Configure environment variables in env_setup.sh or a .env file:
   ```bash
   export CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID'
   export CLIENT_SECRET='YOUR_SPOTIFY_CLIENT_SECRET'
   export API_KEY='YOUR_API_KEY'
   ```

## Usage

### Running the Web App
