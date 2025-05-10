import os
import sys
import pygame
import tkinter as tk
from tkinter import ttk, filedialog
from music21 import converter, midi
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.playback import play

class PartPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SATB Part Player")
        self.root.geometry("600x400")
        
        self.parts = {
            'soprano': {'path': None, 'audio': None},
            'alto': {'path': None, 'audio': None},
            'tenor': {'path': None, 'audio': None},
            'bass': {'path': None, 'audio': None},
            'score': {'path': None, 'audio': None}
        }
        
        self.current_dir = None
        self.song_name = tk.StringVar(value="No song loaded")

        self.create_widgets()
        
    def create_widgets(self):
        # Top frame for song info and load button
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Song:").pack(side=tk.LEFT)
        ttk.Label(top_frame, textvariable=self.song_name).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(top_frame, text="Load Song", command=self.load_song).pack(side=tk.RIGHT)
        
        # Middle frame for part selection and playback controls
        part_frame = ttk.LabelFrame(self.root, text="Parts", padding=10)
        part_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Part checkbuttons
        self.part_vars = {}
        for i, part in enumerate(['soprano', 'alto', 'tenor', 'bass']):
            self.part_vars[part] = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                part_frame, 
                text=part.capitalize(), 
                variable=self.part_vars[part]
            ).grid(row=i//2, column=i%2, sticky=tk.W, padx=20, pady=10)
            
            # Individual part play button
            ttk.Button(
                part_frame,
                text="▶",
                width=3,
                command=lambda p=part: self.play_part(p)
            ).grid(row=i//2, column=(i%2)+2, padx=5, pady=10)
        
        # Control frame
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Play Selected Parts", command=self.play_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Play All", command=self.play_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Stop", command=self.stop_playback).pack(side=tk.LEFT, padx=5)
        
        # Export frame
        export_frame = ttk.Frame(self.root, padding=10)
        export_frame.pack(fill=tk.X, padx=10)
        
        ttk.Button(export_frame, text="Export Selected Parts to MP3", command=self.export_mp3).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X, side=tk.BOTTOM)

    def load_song(self):
        """Load a song directory containing SATB parts"""
        directory = filedialog.askdirectory(title="Select song directory")
        if not directory:
            return
            
        self.current_dir = directory
        self.song_name.set(os.path.basename(directory))
        
        # Look for MusicXML or MIDI files for each part
        for part in self.parts.keys():
            musicxml_path = os.path.join(directory, f"*_{part}.musicxml")
            midi_path = os.path.join(directory, f"*_{part}.mid")
            mp3_path = os.path.join(directory, f"*_{part}.mp3")
            
            # Try to find files with wildcard matching
            import glob
            musicxml_matches = glob.glob(musicxml_path)
            midi_matches = glob.glob(midi_path)
            mp3_matches = glob.glob(mp3_path)
            
            # Prioritize MP3, then MIDI, then MusicXML
            if mp3_matches:
                self.parts[part]['path'] = mp3_matches[0]
            elif midi_matches:
                self.parts[part]['path'] = midi_matches[0]
            elif musicxml_matches:
                self.parts[part]['path'] = musicxml_matches[0]
            
        self.status_var.set(f"Loaded song from {directory}")

    def convert_to_audio(self, part):
        """Convert MusicXML or MIDI file to audio"""
        path = self.parts[part]['path']
        if not path:
            return None
            
        # If already MP3, just load it
        if path.endswith('.mp3'):
            return AudioSegment.from_mp3(path)
            
        # If MIDI, convert to audio
        if path.endswith('.mid'):
            # In a complete implementation, we'd use a MIDI synthesizer
            # For simplicity, we'll just mention the external tools needed
            self.status_var.set(f"Please convert {os.path.basename(path)} to MP3 using an external tool")
            return None
            
        # If MusicXML, first convert to MIDI then to audio
        if path.endswith('.musicxml'):
            try:
                # Load the score
                score = converter.parse(path)
                
                # Generate a MIDI file
                midi_path = path.replace('.musicxml', '.mid')
                score.write('midi', fp=midi_path)
                
                self.status_var.set(f"Created MIDI file. Please convert {os.path.basename(midi_path)} to MP3")
                return None
            except Exception as e:
                self.status_var.set(f"Error converting {os.path.basename(path)}: {str(e)}")
                return None

    def play_part(self, part):
        """Play a single part"""
        if not self.parts[part]['path']:
            self.status_var.set(f"No {part} part found")
            return
            
        self.status_var.set(f"Playing {part} part...")
        
        # Get audio data
        audio = self.parts[part].get('audio')
        if not audio:
            audio = self.convert_to_audio(part)
            if not audio:
                return
            self.parts[part]['audio'] = audio
        
        # Play the audio
        try:
            play(audio)
        except Exception as e:
            self.status_var.set(f"Error playing {part}: {str(e)}")

    def play_selected(self):
        """Play selected parts simultaneously"""
        selected_parts = [part for part, var in self.part_vars.items() if var.get()]
        if not selected_parts:
            self.status_var.set("No parts selected")
            return
            
        self.status_var.set(f"Playing selected parts: {', '.join(selected_parts)}")
        
        # In a complete implementation, we'd mix the audio for the selected parts
        # This requires more sophisticated audio processing
        self.status_var.set("Playing multiple parts simultaneously requires additional implementation")

    def play_all(self):
        """Play all parts"""
        if not self.parts['score']['path']:
            self.status_var.set("Full score not found")
            return
            
        self.status_var.set("Playing full score...")
        self.play_part('score')

    def stop_playback(self):
        """Stop current playback"""
        # This would require more sophisticated audio control
        self.status_var.set("Playback stopped")

    def export_mp3(self):
        """Export selected parts to MP3"""
        selected_parts = [part for part, var in self.part_vars.items() if var.get()]
        if not selected_parts:
            self.status_var.set("No parts selected for export")
            return
            
        output_dir = filedialog.askdirectory(title="Select export directory")
        if not output_dir:
            return
            
        self.status_var.set("Exporting selected parts to MP3...")
        
        # In a complete implementation, we'd convert and export each selected part
        self.status_var.set("MP3 export requires additional implementation")


def render_audio_from_musicxml(musicxml_file, output_file=None):
    """
    Render audio from a MusicXML file
    
    Args:
        musicxml_file (str): Path to MusicXML file
        output_file (str): Path to output audio file
        
    Returns:
        str: Path to the audio file
    """
    if not output_file:
        output_file = os.path.splitext(musicxml_file)[0] + ".mp3"
        
    try:
        # Parse the MusicXML file
        score = converter.parse(musicxml_file)
        
        # Generate a MIDI file
        midi_file = os.path.splitext(output_file)[0] + ".mid"
        score.write('midi', fp=midi_file)
        
        print(f"MIDI file generated: {midi_file}")
        print(f"To convert to audio, use a MIDI synthesizer like FluidSynth or a DAW.")
        print(f"Command example (with FluidSynth): fluidsynth -F {output_file} soundfont.sf2 {midi_file}")
        
        return midi_file
    except Exception as e:
        print(f"Error rendering audio: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--render":
        if len(sys.argv) > 2:
            render_audio_from_musicxml(sys.argv[2])
        else:
            print("Usage: python part_player.py --render <musicxml_file>")
    else:
        root = tk.Tk()
        app = PartPlayerApp(root)
        root.mainloop()
