from get_acces_token import get_access_token
from audio_recorder import record_audio
from url_extractor import url_extractor
from transciber import transcriber
from spotify_query import search_track
import os

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

# Example usage
access_token = get_access_token(client_id, client_secret)

if __name__ == "__main__":
    print("Audio Recorder")
    print("--------------")

            
    filename = "recording.wav"
    
    duration = input("Enter recording duration in seconds (default: 5): ").strip()
    duration = int(duration) if duration else 5
    
    print("Press Enter to start recording (Ctrl+C to exit)")
    input()
    
    audio_path = record_audio(filename, duration)

    audio_url = url_extractor(audio_path)

    music_text = transcriber(audio_url)

    search_track(music_text,access_token, limit=3)