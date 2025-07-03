import os
import librosa
import numpy as np
import soundfile as sf
from music21 import stream, note, instrument, scale

"""
SATB Generator
==============

Turn your MP3 audio into SATB (Soprano, Alto, Tenor, Bass) sheet music with solfège syllables!

Usage:
  python3 SATB_generator.py song1.mp3 song2.mp3 --format musicxml --output-dir results --solfege movable
  python3 SATB_generator.py song1.mp3 --format pdf --output-dir results

Features:
- Converts audio to SATB scores (MusicXML, MIDI, PDF)
- Adds solfège syllables (fixed or movable do)
- Detects key for movable do
- Tries to guess note durations
- Batch processing (multiple files)
- Plays MIDI if you want (needs pygame)
"""

# Fixed do solfège (C major)
NOTE_TO_SOLFEGE_FIXED = {
    'C': 'Do', 'C#': 'Di', 'D': 'Re', 'D#': 'Ri', 'E': 'Mi', 'F': 'Fa',
    'F#': 'Fi', 'G': 'Sol', 'G#': 'Si', 'A': 'La', 'A#': 'Li', 'B': 'Ti'
}

# Movable do (major scale degrees)
DEGREE_TO_SOLFEGE = ['Do', 'Re', 'Mi', 'Fa', 'Sol', 'La', 'Ti']

def get_solfege_movable(note_obj, tonic):
    """Return movable do solfège for a note, given the tonic."""
    s = scale.MajorScale(tonic)
    try:
        deg = s.getScaleDegreeFromPitch(note_obj)
        if deg is not None and 1 <= deg <= 7:
            return DEGREE_TO_SOLFEGE[deg-1]
    except Exception:
        pass
    return ''

def play_midi_file(midi_path):
    """Play a MIDI file if pygame is installed."""
    try:
        import pygame
        import time
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load(midi_path)
        pygame.mixer.music.play()
        print(f"Playing {midi_path}...")
        while pygame.mixer.music.get_busy():
            time.sleep(0.5)
        pygame.mixer.music.stop()
        pygame.quit()
    except ImportError:
        print("Install pygame to play MIDI: pip install pygame")
    except Exception as e:
        print(f"Couldn't play MIDI: {e}")

def generate_satb_parts(mp3_file_paths, output_dir=None, output_format="musicxml", export_audio=True, solfege_system='fixed', play_midi=False):
    if isinstance(mp3_file_paths, str):
        mp3_file_paths = [mp3_file_paths]
    # Remove non-existent files from the list
    mp3_file_paths = [f for f in mp3_file_paths if os.path.exists(f)]
    if not mp3_file_paths:
        print("No valid input files found. Exiting.")
        return {}
    all_outputs = {}
    for mp3_file_path in mp3_file_paths:
        out_dir = output_dir or os.path.dirname(mp3_file_path)
        os.makedirs(out_dir, exist_ok=True)
        print(f"Working on {mp3_file_path}...")
        y, sr = librosa.load(mp3_file_path, sr=None)
        print("Analyzing audio...")
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        y_harmonic = librosa.effects.harmonic(y)
        pitches, mags = librosa.piptrack(y=y_harmonic, sr=sr)
        vocal_ranges = {
            "soprano": (60, 83),
            "alto": (53, 76),
            "tenor": (48, 69),
            "bass": (36, 60)
        }
        parts = {v: stream.Part(id=v) for v in vocal_ranges}
        parts["soprano"].append(instrument.Soprano())
        parts["alto"].append(instrument.Alto())
        parts["tenor"].append(instrument.Tenor())
        parts["bass"].append(instrument.Bass())
        # Key for movable do
        detected_key = 'C'
        if solfege_system == 'movable':
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            key_index = chroma.sum(axis=1).argmax()
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            detected_key = key_names[key_index]
        # Guess durations
        if len(onset_times) > 1:
            durations = np.diff(onset_times)
            durations = np.append(durations, durations[-1])
        else:
            durations = [1.0] * len(onset_times)
        for i, onset in enumerate(onset_times):
            if i < len(onset_frames):
                frame = onset_frames[i]
                if frame < pitches.shape[1]:
                    pitch_candidates = []
                    for freq_bin in range(pitches.shape[0]):
                        if mags[freq_bin, frame] > 0.1:
                            midi_pitch = int(round(librosa.hz_to_midi(pitches[freq_bin, frame])))
                            if 36 <= midi_pitch <= 83:
                                pitch_candidates.append((midi_pitch, mags[freq_bin, frame]))
                    pitch_candidates.sort(key=lambda x: x[1], reverse=True)
                    top_pitches = [p[0] for p in pitch_candidates[:4]]
                    assigned = {v: None for v in vocal_ranges}
                    for midi_pitch in sorted(top_pitches, reverse=True):
                        for v in ["soprano", "alto", "tenor", "bass"]:
                            if assigned[v] is None and vocal_ranges[v][0] <= midi_pitch <= vocal_ranges[v][1]:
                                assigned[v] = midi_pitch
                                break
                    for v, midi_pitch in assigned.items():
                        if midi_pitch is not None:
                            n = note.Note(midi_pitch)
                            n.quarterLength = float(durations[i])
                            if solfege_system == 'fixed':
                                n.lyric = NOTE_TO_SOLFEGE_FIXED.get(n.name, '')
                            else:
                                n.lyric = get_solfege_movable(n, detected_key)
                            parts[v].append(n)
                        else:
                            parts[v].append(note.Rest(quarterLength=float(durations[i])))
        score = stream.Score()
        for v in ["soprano", "alto", "tenor", "bass"]:
            score.append(parts[v])
        base = os.path.splitext(os.path.basename(mp3_file_path))[0]
        output_files = {}
        midi_path = os.path.join(out_dir, f"{base}_satb.mid")
        score.write('midi', fp=midi_path)
        output_files['score_midi'] = midi_path
        for v in ["soprano", "alto", "tenor", "bass"]:
            part_midi = os.path.join(out_dir, f"{base}_{v}.mid")
            parts[v].write('midi', fp=part_midi)
            output_files[f"{v}_midi"] = part_midi
        if output_format == "musicxml":
            xml_path = os.path.join(out_dir, f"{base}_satb.musicxml")
            score.write('musicxml', fp=xml_path)
            output_files['score'] = xml_path
            for v in ["soprano", "alto", "tenor", "bass"]:
                part_xml = os.path.join(out_dir, f"{base}_{v}.musicxml")
                parts[v].write('musicxml', fp=part_xml)
                output_files[v] = part_xml
        elif output_format == "midi":
            output_files['score'] = midi_path
        elif output_format == "pdf":
            pdf_path = os.path.join(out_dir, f"{base}_satb.pdf")
            try:
                musescore_paths = [
                    '/Applications/MuseScore 4.app/Contents/MacOS/mscore',
                    '/Applications/MuseScore 3.app/Contents/MacOS/mscore',
                    '/usr/bin/mscore', '/usr/local/bin/mscore',
                    '/usr/bin/musescore', '/usr/local/bin/musescore'
                ]
                musescore_exec = next((p for p in musescore_paths if os.path.exists(p)), None)
                if musescore_exec:
                    xml_path = os.path.join(out_dir, f"{base}_satb.musicxml")
                    score.write('musicxml', fp=xml_path)
                    os.system(f'"{musescore_exec}" "{xml_path}" -o "{pdf_path}"')
                    output_files['score'] = pdf_path
                    print(f"PDF exported: {pdf_path}")
                else:
                    print("MuseScore not found. Please install MuseScore and add it to your PATH for PDF export.")
                    print("Or open the MusicXML in MuseScore or LilyPond to make a PDF.")
            except Exception as e:
                print(f"PDF export failed: {e}")
        if export_audio:
            print("To turn MIDI into audio, try:")
            print("  fluidsynth -F output.wav soundfont.sf2 input.mid")
            print("  Or use GarageBand, Logic, Ableton, etc.")
            print(f"MIDI files are in: {out_dir}")
        if play_midi:
            play_midi_file(midi_path)
        print(f"Done! Results in {out_dir}\n")
        all_outputs[mp3_file_path] = output_files
    return all_outputs

def convert_mp3_to_wav(mp3_path, wav_path=None):
    if not os.path.exists(mp3_path):
        print(f"File not found: {mp3_path}")
        return None
    wav_path = wav_path or f"{os.path.splitext(mp3_path)[0]}.wav"
    y, sr = librosa.load(mp3_path, sr=None)
    sf.write(wav_path, y, sr)
    return wav_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate SATB parts from audio file(s)')
    parser.add_argument('input_files', nargs='+', help='Path(s) to the audio file(s)')
    parser.add_argument('--format', choices=['musicxml', 'midi', 'pdf'], default='musicxml', help='Output format')
    parser.add_argument('--output-dir', help='Where to put results')
    parser.add_argument('--no-audio', action='store_true', help='Skip audio export')
    parser.add_argument('--solfege', choices=['fixed', 'movable'], default='fixed', help='Solfege system')
    parser.add_argument('--play-midi', action='store_true', help='Play the MIDI file (needs pygame)')
    args = parser.parse_args()
    output_files = generate_satb_parts(
        args.input_files, 
        output_dir=args.output_dir, 
        output_format=args.format,
        export_audio=not args.no_audio,
        solfege_system=args.solfege,
        play_midi=args.play_midi
    )
    print("All done!")
    for file, outputs in output_files.items():
        print(f"{file}:")
        for part, path in outputs.items():
            print(f"  - {part}: {path}")