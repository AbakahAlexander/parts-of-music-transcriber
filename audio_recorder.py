try:
    import sounddevice as sd
    import numpy as np
    import wave
    import os
    import time
except OSError as e:
    if 'PortAudio library not found' in str(e):
        print("Error: PortAudio library not found.")
        print("Please install the PortAudio development libraries:")
        print("  For Ubuntu/Debian: sudo apt-get install portaudio19-dev")
        print("  For macOS: brew install portaudio")
        print("  For Windows: pip install pipwin && pipwin install pyaudio")
        print("\nAfter installing the library, reinstall sounddevice: pip install sounddevice")
        exit(1)
    else:
        raise

def record_audio(filename="recording.wav", duration=5, samplerate=44100):
    """
    Record audio from the microphone and save as a WAV file.
    
    Args:
        filename (str): Name of the output file
        duration (int): Recording duration in seconds
        samplerate (int): Sample rate in Hz
    """
    print(f"Recording {duration} seconds of audio...")
    
    # Record audio
    recording = sd.rec(int(duration * samplerate), 
                      samplerate=samplerate,
                      channels=2, 
                      dtype='int16')
    
    # Wait for the recording to finish
    sd.wait()
    
    print("Recording finished!")
    
    # Save recording to WAV file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)  # 2 bytes for 'int16'
        wf.setframerate(samplerate)
        wf.writeframes(recording.tobytes())
    
    print(f"Audio saved as {filename}")
    print(f"File saved at: {os.path.abspath(filename)}")

    return os.path.abspath(filename)

