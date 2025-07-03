from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
from SATB_generator import generate_satb_parts
import requests

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'mp3', 'webm', 'wav', 'ogg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.secret_key = 'supersecretkey'  # Change this in production

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Dummy database for matching (replace with real DB or fingerprinting)
SONG_DATABASE = {
    'Michael_W_Smith_-_Above_All-Powers-www.CeeNaija.com__satb.mp3': 'Michael W. Smith - Above All Powers',
    # Add more known tracks here
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def match_audio_to_database(filename):
    # Dummy: match by filename only (replace with real fingerprinting for production)
    base = os.path.basename(filename)
    return SONG_DATABASE.get(base, None)

def recognize_audio_with_spotify_or_general(filepath):
    # --- GENERAL CASE: Use a cloud audio recognition API (e.g., AudD, ACRCloud, etc.) ---
    # This is a placeholder. Replace with your API credentials and logic.
    # Example: AudD API (https://audd.io/)
    # You must sign up for an API key at https://audd.io/
    AUDD_API_TOKEN = os.environ.get('AUDD_API_TOKEN')  # Set this in your environment
    if AUDD_API_TOKEN:
        with open(filepath, 'rb') as f:
            files = {'file': f}
            data = {'api_token': AUDD_API_TOKEN, 'return': 'spotify'}
            response = requests.post('https://api.audd.io/', data=data, files=files)
            if response.ok:
                result = response.json().get('result')
                if result and 'title' in result and 'artist' in result:
                    # Optionally, get Spotify info
                    return {
                        'title': result['title'],
                        'artist': result['artist'],
                        'album': result.get('album'),
                        'spotify': result.get('spotify', {})
                    }
    # --- FALLBACK: Try filename match (demo) ---
    base = os.path.basename(filepath)
    if base in SONG_DATABASE:
        return {'title': SONG_DATABASE[base], 'artist': 'Demo Artist'}
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/match', methods=['POST'])
def api_match():
    # Accepts either 'audio' (from recorder) or 'file' (from upload)
    file = request.files.get('audio') or request.files.get('file')
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'No valid audio uploaded'}), 400
    # Save with a unique name to avoid collisions
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"recording_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(filepath)
    # --- Use general audio recognition (cloud API) ---
    match_info = recognize_audio_with_spotify_or_general(filepath)
    if not match_info:
        os.remove(filepath)
        return jsonify({'match': None})
    # Optionally, return Spotify info for frontend display
    return jsonify({'match': match_info['title'], 'artist': match_info.get('artist'), 'spotify': match_info.get('spotify'), 'filename': unique_name})

@app.route('/api/generate', methods=['POST'])
def api_generate():
    # Example: generate SATB/PDF for a matched song (for AJAX/JS use)
    filename = request.form.get('filename')
    output_format = request.form.get('format', 'musicxml')
    solfege = request.form.get('solfege', 'fixed')
    if not filename:
        return jsonify({'error': 'No file provided'}), 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    outputs = generate_satb_parts(
        [filepath],
        output_dir=app.config['RESULTS_FOLDER'],
        output_format=output_format,
        solfege_system=solfege,
        export_audio=True,
        play_midi=False
    )
    download_links = []
    pdf_link = None
    for file_outputs in outputs.values():
        for part, path in file_outputs.items():
            rel_path = os.path.relpath(path, app.config['RESULTS_FOLDER'])
            if part == 'score' and output_format == 'pdf':
                pdf_link = rel_path
            else:
                download_links.append({'part': part, 'url': url_for('download_file', filename=rel_path)})
    return jsonify({'download_links': download_links, 'pdf_link': pdf_link})

@app.route('/results/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['RESULTS_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
