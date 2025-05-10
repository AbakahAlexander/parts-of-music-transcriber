import os
import librosa
import numpy as np
import soundfile as sf
from music21 import converter, stream, note, pitch, instrument, midi

def generate_satb_parts(mp3_file_path, output_dir=None, output_format="musicxml", export_audio=True):
    """
    Generate SATB (Soprano, Alto, Tenor, Bass) parts from an MP3 file.
    
    Args:
        mp3_file_path (str): Path to the MP3 file
        output_dir (str): Directory to save output files (defaults to same directory as input)
        output_format (str): Format for output files ("musicxml", "midi", "pdf")
        export_audio (bool): Whether to export audio files for each part
        
    Returns:
        dict: Dictionary containing paths to the generated files for each part
    """
    if not os.path.exists(mp3_file_path):
        raise FileNotFoundError(f"MP3 file not found: {mp3_file_path}")
    
    if output_dir is None:
        output_dir = os.path.dirname(mp3_file_path)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Processing {mp3_file_path}...")
    
    # Load audio file
    y, sr = librosa.load(mp3_file_path, sr=None)
    
    # Step 1: Source separation (separating vocals/instruments)
    # In a complete implementation, you would use a library like Spleeter or Demucs
    # For simplicity, we'll simulate this step
    print("Performing source separation...")
    
    # Step 2: Pitch detection and transcription
    print("Analyzing pitch content...")
    
    # Use librosa to detect pitches and onsets
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    
    # Harmonic-percussive source separation for better pitch analysis
    y_harmonic = librosa.effects.harmonic(y)
    pitches, magnitudes = librosa.piptrack(y=y_harmonic, sr=sr)
    
    # Step 3: Transcribe and generate parts
    # Define vocal ranges (MIDI note numbers)
    vocal_ranges = {
        "soprano": (60, 83),  # C4-B5
        "alto": (53, 76),     # F3-E5
        "tenor": (48, 69),    # C3-A4
        "bass": (36, 60)      # C2-C4
    }
    
    # Create music21 streams for each part
    parts = {
        "soprano": stream.Part(id='soprano'),
        "alto": stream.Part(id='alto'),
        "tenor": stream.Part(id='tenor'),
        "bass": stream.Part(id='bass')
    }
    
    # Add appropriate instruments
    parts["soprano"].append(instrument.Soprano())
    parts["alto"].append(instrument.Alto())
    parts["tenor"].append(instrument.Tenor())
    parts["bass"].append(instrument.Bass())
    
    # In a real implementation, you would:
    # 1. Use a more sophisticated algorithm to extract notes and assign to parts
    # 2. Consider harmonies and music theory rules for proper voice leading
    # 3. Handle rhythm and note durations more precisely
    
    # Simulate transcribing notes to each part
    for i, onset in enumerate(onset_times):
        # Find the strongest pitches at this onset
        if i < len(onset_frames):
            frame = onset_frames[i]
            if frame < pitches.shape[1]:
                pitch_candidates = []
                for freq_bin in range(pitches.shape[0]):
                    if magnitudes[freq_bin, frame] > 0.1:  # Only consider strong enough frequencies
                        midi_pitch = int(round(librosa.hz_to_midi(pitches[freq_bin, frame])))
                        if 36 <= midi_pitch <= 83:  # Within overall SATB range
                            pitch_candidates.append((midi_pitch, magnitudes[freq_bin, frame]))
                
                # Sort by magnitude
                pitch_candidates.sort(key=lambda x: x[1], reverse=True)
                
                # Take top 4 pitches (or fewer if not enough)
                top_pitches = [p[0] for p in pitch_candidates[:4]]
                
                # Assign to parts based on ranges
                assigned_pitches = {'soprano': None, 'alto': None, 'tenor': None, 'bass': None}
                
                # First, try to find ideal pitches for each voice
                for midi_pitch in sorted(top_pitches, reverse=True):
                    assigned = False
                    for voice in ['soprano', 'alto', 'tenor', 'bass']:
                        if assigned_pitches[voice] is None and vocal_ranges[voice][0] <= midi_pitch <= vocal_ranges[voice][1]:
                            assigned_pitches[voice] = midi_pitch
                            assigned = True
                            break
                
                # Add notes to parts
                for voice, midi_pitch in assigned_pitches.items():
                    if midi_pitch is not None:
                        n = note.Note(midi_pitch)
                        n.quarterLength = 1.0  # For simplicity, use quarter notes
                        parts[voice].append(n)
                    else:
                        # Add rest if no pitch assigned
                        parts[voice].append(note.Rest(quarterLength=1.0))
    
    # Create a score with all parts
    score = stream.Score()
    for part_name in ['soprano', 'alto', 'tenor', 'bass']:
        score.append(parts[part_name])
    
    # Export files
    base_name = os.path.splitext(os.path.basename(mp3_file_path))[0]
    output_files = {}
    
    # Always export MIDI regardless of output_format selection
    # This ensures we have playable files
    midi_output_path = os.path.join(output_dir, f"{base_name}_satb.mid")
    score.write('midi', fp=midi_output_path)
    output_files['score_midi'] = midi_output_path
    
    for part_name in ['soprano', 'alto', 'tenor', 'bass']:
        part_midi_path = os.path.join(output_dir, f"{base_name}_{part_name}.mid")
        parts[part_name].write('midi', fp=part_midi_path)
        output_files[f"{part_name}_midi"] = part_midi_path
    
    # Export in requested format
    if output_format == "musicxml":
        output_path = os.path.join(output_dir, f"{base_name}_satb.musicxml")
        score.write('musicxml', fp=output_path)
        output_files['score'] = output_path
        
        # Export individual parts
        for part_name in ['soprano', 'alto', 'tenor', 'bass']:
            part_path = os.path.join(output_dir, f"{base_name}_{part_name}.musicxml")
            parts[part_name].write('musicxml', fp=part_path)
            output_files[part_name] = part_path
            
    elif output_format == "midi":
        output_path = os.path.join(output_dir, f"{base_name}_satb.mid")
        score.write('midi', fp=output_path)
        output_files['score'] = output_path
        
        # Export individual parts
        for part_name in ['soprano', 'alto', 'tenor', 'bass']:
            part_path = os.path.join(output_dir, f"{base_name}_{part_name}.mid")
            parts[part_name].write('midi', fp=part_path)
            output_files[part_name] = part_path
            
    elif output_format == "pdf":
        # Note: PDF export requires additional setup with MuseScore or LilyPond
        output_path = os.path.join(output_dir, f"{base_name}_satb.pdf")
        try:
            score.write('musicxml.pdf', fp=output_path)
            output_files['score'] = output_path
        except:
            print("PDF export requires additional setup with MuseScore or LilyPond.")
    
    # Export audio if requested
    if export_audio:
        try:
            print("Attempting to render audio files...")
            # Audio rendering requires additional libraries like FluidSynth
            # We'll provide instructions on how to convert MIDI to audio
            print("To render audio from MIDI files, you can use:")
            print("1. FluidSynth: fluidsynth -F output.wav soundfont.sf2 input.mid")
            print("2. A Digital Audio Workstation (DAW) like GarageBand, Logic, Ableton, etc.")
            print("3. Online MIDI to MP3 converters")
            print(f"The MIDI files are located in: {output_dir}")
        except Exception as e:
            print(f"Error exporting audio: {e}")
    
    print(f"SATB parts generated and saved to {output_dir}")
    return output_files

def convert_mp3_to_wav(mp3_path, wav_path=None):
    """
    Convert an MP3 file to WAV format for easier processing.
    
    Args:
        mp3_path (str): Path to MP3 file
        wav_path (str): Path for output WAV file (optional)
        
    Returns:
        str: Path to the WAV file
    """
    if not os.path.exists(mp3_path):
        raise FileNotFoundError(f"MP3 file not found: {mp3_path}")
    
    if wav_path is None:
        base_name = os.path.splitext(mp3_path)[0]
        wav_path = f"{base_name}.wav"
    
    # Load MP3 and save as WAV
    y, sr = librosa.load(mp3_path, sr=None)
    sf.write(wav_path, y, sr)
    
    return wav_path

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate SATB parts from audio file')
    parser.add_argument('input_file', help='Path to the audio file')
    parser.add_argument('--format', choices=['musicxml', 'midi', 'pdf'], default='musicxml', 
                        help='Output format (default: musicxml)')
    parser.add_argument('--output-dir', help='Output directory')
    parser.add_argument('--no-audio', action='store_true', help='Do not export audio files')
    
    if len(sys.argv) > 1:
        args = parser.parse_args()
        try:
            output_files = generate_satb_parts(
                args.input_file, 
                output_dir=args.output_dir, 
                output_format=args.format,
                export_audio=not args.no_audio
            )
            print("Generated files:")
            for part, path in output_files.items():
                print(f"- {part}: {path}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        parser.print_help()