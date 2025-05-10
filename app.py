from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from werkzeug.utils import secure_filename
from SATB_generator import generate_satb_parts
from audio_converter import convert_musicxml_to_audio

# Import functions used in main.py
from get_acces_token import get_access_token
from audio_recorder import record_audio
from url_extractor import url_extractor
from transciber import transcriber
from spotify_query import search_track

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
AUDIO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')
RECORDINGS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recordings')

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER
app.config['RECORDINGS_FOLDER'] = RECORDINGS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB max upload

# Get Spotify API credentials from environment variables
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

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
                'basename': os.path.splitext(filename)[0],
                'type': 'satb_parts'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File processing failed'}), 500

@app.route('/record', methods=['POST'])
def record():
    try:
        data = request.get_json()
        duration = data.get('duration', 5)
        
        # Generate a unique filename
        import time
        timestamp = int(time.time())
        filename = os.path.join(app.config['RECORDINGS_FOLDER'], f"recording_{timestamp}.wav")
        
        # Record audio
        audio_path = record_audio(filename, int(duration))
        
        # Process recorded audio - this follows the flow in main.py
        audio_url = url_extractor(audio_path)
        music_text = transcriber(audio_url)
        
        # Get Spotify access token
        access_token = get_access_token(client_id, client_secret)
        
        # Search for tracks
        tracks = search_track(music_text, access_token, limit=3, return_results=True)
        
        # Return results
        return jsonify({
            'message': 'Audio recorded and processed successfully',
            'music_text': music_text,
            'tracks': tracks,
            'type': 'spotify_results'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<filename>')
def serve_results(filename):
    return send_file(os.path.join(app.config['RESULTS_FOLDER'], filename))

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(os.path.join(app.config['AUDIO_FOLDER'], filename))

@app.route('/recordings/<filename>')
def serve_recordings(filename):
    return send_file(os.path.join(app.config['RECORDINGS_FOLDER'], filename))

if __name__ == '__main__':
    app.run(debug=True)
