#!/usr/bin/env python3

import os
import subprocess
import sys

def install_system_dependencies():
    print("Installing system dependencies...")
    
    try:
        subprocess.check_call(["sudo", "apt-get", "update"])
        subprocess.check_call([
            "sudo", "apt-get", "install", "-y",
            "python3-dev", "python3-tk", "portaudio19-dev", "fluidsynth",
            "libsdl2-dev", "libsdl2-image-dev", "libsdl2-mixer-dev", "libsdl2-ttf-dev",
            "libfreetype6-dev", "libportmidi-dev", "ffmpeg"
        ])
        print("System dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing system dependencies: {e}")
        print("Please try installing them manually.")
        return False
    
    return True

def install_python_dependencies():
    print("Installing Python dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "wheel"])
        
        # Install core dependencies first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sounddevice"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "werkzeug"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        
        # Install librosa (which can be tricky)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "librosa"])
        
        # Install music21 and soundfile
        subprocess.check_call([sys.executable, "-m", "pip", "install", "music21"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "soundfile"])
        
        print("Python dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Python dependencies: {e}")
        print("Please try installing them manually.")
        return False
    
    return True

def create_required_directories():
    print("Creating required directories...")
    
    try:
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results'), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio'), exist_ok=True)
        print("Directories created successfully.")
    except Exception as e:
        print(f"Error creating directories: {e}")
        return False
    
    return True

def create_audio_converter():
    print("Creating audio_converter.py...")
    
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio_converter.py')
    
    if os.path.exists(script_path):
        print("audio_converter.py already exists.")
        return True
    
    try:
        with open(script_path, 'w') as f:
            f.write("""
import os
import subprocess
import tempfile
from music21 import converter

def convert_musicxml_to_midi(musicxml_file, midi_file=None):
    \"\"\"
    Convert MusicXML file to MIDI format
    
    Args:
        musicxml_file (str): Path to MusicXML file
        midi_file (str): Path to output MIDI file (optional)
        
    Returns:
        str: Path to the MIDI file
    \"\"\"
    if midi_file is None:
        midi_file = os.path.splitext(musicxml_file)[0] + '.mid'
    
    # Load the MusicXML file with music21
    score = converter.parse(musicxml_file)
    
    # Write to MIDI
    score.write('midi', fp=midi_file)
    
    return midi_file

def convert_midi_to_audio(midi_file, audio_file=None, format='wav', soundfont=None):
    \"\"\"
    Convert MIDI file to audio using FluidSynth
    
    Args:
        midi_file (str): Path to MIDI file
        audio_file (str): Path to output audio file (optional)
        format (str): Output format (wav or mp3)
        soundfont (str): Path to soundfont file
        
    Returns:
        str: Path to the audio file
    \"\"\"
    if audio_file is None:
        audio_file = os.path.splitext(midi_file)[0] + f'.{format}'
    
    # Default soundfont paths to try
    soundfont_paths = [
        soundfont,
        '/usr/share/sounds/sf2/FluidR3_GM.sf2',
        '/usr/share/soundfonts/FluidR3_GM.sf2',
        '/usr/share/sounds/sf2/default.sf2'
    ]
    
    # Find the first available soundfont
    sf_path = None
    for path in soundfont_paths:
        if path and os.path.exists(path):
            sf_path = path
            break
    
    if not sf_path:
        # If no soundfont is found, download a free soundfont
        sf_path = download_soundfont()
    
    # Convert MIDI to audio using FluidSynth
    if format.lower() == 'wav':
        cmd = ['fluidsynth', '-ni', '-g', '1', sf_path, midi_file, '-F', audio_file]
    else:  # mp3
        # FluidSynth can't output MP3 directly, so we create a WAV first
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        cmd_wav = ['fluidsynth', '-ni', '-g', '1', sf_path, midi_file, '-F', temp_wav]
        
        try:
            subprocess.run(cmd_wav, check=True)
            
            # Convert WAV to MP3 using FFmpeg
            cmd = ['ffmpeg', '-i', temp_wav, '-q:a', '2', audio_file]
            subprocess.run(cmd, check=True)
            
            # Remove temporary WAV file
            os.unlink(temp_wav)
        except subprocess.CalledProcessError as e:
            if os.path.exists(temp_wav):
                os.unlink(temp_wav)
            raise RuntimeError(f"Error converting MIDI to MP3: {e}")
        
        return audio_file
    
    try:
        subprocess.run(cmd, check=True)
        return audio_file
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error converting MIDI to audio: {e}")

def download_soundfont():
    \"\"\"
    Download a free soundfont file for MIDI rendering
    
    Returns:
        str: Path to the downloaded soundfont
    \"\"\"
    import requests
    
    # Create directory for soundfonts if it doesn't exist
    soundfont_dir = os.path.join(os.path.expanduser('~'), '.soundfonts')
    os.makedirs(soundfont_dir, exist_ok=True)
    
    soundfont_path = os.path.join(soundfont_dir, 'FluidR3_GM.sf2')
    
    # Only download if it doesn't exist
    if not os.path.exists(soundfont_path):
        print("Downloading soundfont...")
        url = "https://archive.org/download/FluidR3GM/FluidR3GM.sf2"
        
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(soundfont_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"Soundfont downloaded to: {soundfont_path}")
    
    return soundfont_path

def convert_musicxml_to_audio(musicxml_file, audio_file=None, format='mp3'):
    \"\"\"
    Convert MusicXML file directly to audio
    
    Args:
        musicxml_file (str): Path to MusicXML file
        audio_file (str): Path to output audio file (optional)
        format (str): Output format (wav or mp3)
        
    Returns:
        str: Path to the audio file
    \"\"\"
    if audio_file is None:
        audio_file = os.path.splitext(musicxml_file)[0] + f'.{format}'
    
    # First convert to MIDI
    midi_file = convert_musicxml_to_midi(musicxml_file)
    
    # Then convert MIDI to audio
    audio_file = convert_midi_to_audio(midi_file, audio_file, format)
    
    return audio_file
""")
        print("audio_converter.py created successfully.")
    except Exception as e:
        print(f"Error creating audio_converter.py: {e}")
        return False
    
    return True

def create_app_py():
    print("Creating app.py...")
    
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
    
    if os.path.exists(script_path):
        print("app.py already exists.")
        return True
    
    try:
        with open(script_path, 'w') as f:
            f.write("""
from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from werkzeug.utils import secure_filename
from SATB_generator import generate_satb_parts
from audio_converter import convert_musicxml_to_audio

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
AUDIO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB max upload

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file.filename.lower().endswith('.mp3'):
        return jsonify({'error': 'Only MP3 files are supported'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Generate MusicXML for SATB parts
            result_files = generate_satb_parts(
                file_path, 
                output_dir=app.config['RESULTS_FOLDER'], 
                output_format='musicxml',
                export_audio=True
            )
            
            # Convert MusicXML to audio files
            audio_files = {}
            for part, xml_path in result_files.items():
                if part.endswith('_midi'):
                    continue
                
                try:
                    if xml_path.endswith('.musicxml'):
                        audio_path = convert_musicxml_to_audio(
                            xml_path, 
                            os.path.join(app.config['AUDIO_FOLDER'], f"{os.path.splitext(os.path.basename(xml_path))[0]}.mp3"),
                            'mp3'
                        )
                        audio_files[f"{part}_audio"] = os.path.basename(audio_path)
                except Exception as e:
                    print(f"Error converting {part} to audio: {e}")
            
            # Add audio files to result
            result_files.update(audio_files)
            
            # Create response with file paths
            return jsonify({
                'message': 'File processed successfully',
                'files': result_files,
                'basename': os.path.splitext(filename)[0]
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File processing failed'}), 500

@app.route('/results/<filename>')
def serve_results(filename):
    return send_file(os.path.join(app.config['RESULTS_FOLDER'], filename))

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(os.path.join(app.config['AUDIO_FOLDER'], filename))

if __name__ == '__main__':
    app.run(debug=True)
""")
        print("app.py created successfully.")
    except Exception as e:
        print(f"Error creating app.py: {e}")
        return False
    
    return True

def main():
    print("Setting up Parts of Music Transcriber...")
    
    if not install_system_dependencies():
        print("Warning: Failed to install system dependencies. Continuing...")
    
    if not install_python_dependencies():
        print("Failed to install Python dependencies. Exiting.")
        return False
    
    if not create_required_directories():
        print("Failed to create required directories. Exiting.")
        return False
    
    if not create_audio_converter():
        print("Failed to create audio_converter.py. Exiting.")
        return False
    
    if not create_app_py():
        print("Failed to create app.py. Exiting.")
        return False
    
    print("\nSetup complete! You can now run the application with:")
    print("\ncd /home/alexander/git_repos/parts-of-music-transcriber")
    print("export FLASK_APP=app.py")
    print("export FLASK_ENV=development")
    print("flask run --host=0.0.0.0 --port=5000\n")
    
    return True

if __name__ == "__main__":
    main()
