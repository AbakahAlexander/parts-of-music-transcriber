import os
import subprocess
import tempfile
from music21 import converter

def convert_musicxml_to_midi(musicxml_file, midi_file=None):
    """
    Convert MusicXML file to MIDI format
    
    Args:
        musicxml_file (str): Path to MusicXML file
        midi_file (str): Path to output MIDI file (optional)
        
    Returns:
        str: Path to the MIDI file
    """
    if midi_file is None:
        midi_file = os.path.splitext(musicxml_file)[0] + '.mid'
    
    # Load the MusicXML file with music21
    score = converter.parse(musicxml_file)
    
    # Write to MIDI
    score.write('midi', fp=midi_file)
    
    return midi_file

def convert_midi_to_audio(midi_file, audio_file=None, format='wav', soundfont=None):
    """
    Convert MIDI file to audio using FluidSynth
    
    Args:
        midi_file (str): Path to MIDI file
        audio_file (str): Path to output audio file (optional)
        format (str): Output format (wav or mp3)
        soundfont (str): Path to soundfont file
        
    Returns:
        str: Path to the audio file
    """
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
    """
    Download a free soundfont file for MIDI rendering
    
    Returns:
        str: Path to the downloaded soundfont
    """
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
    """
    Convert MusicXML file directly to audio
    
    Args:
        musicxml_file (str): Path to MusicXML file
        audio_file (str): Path to output audio file (optional)
        format (str): Output format (wav or mp3)
        
    Returns:
        str: Path to the audio file
    """
    if audio_file is None:
        audio_file = os.path.splitext(musicxml_file)[0] + f'.{format}'
    
    # First convert to MIDI
    midi_file = convert_musicxml_to_midi(musicxml_file)
    
    # Then convert MIDI to audio
    audio_file = convert_midi_to_audio(midi_file, audio_file, format)
    
    return audio_file
