import requests
import time
import os



def transcriber(audio_url):

    # 1. Submit transcription request
    headers = {"authorization": os.getenv('API_KEY')}
    transcript_request = {"audio_url": audio_url}

    response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        json=transcript_request,
        headers=headers
    )

    if response.status_code != 200:
        raise Exception("Transcription request failed:", response.text)

    transcript_id = response.json()['id']
    print("Transcript ID:", transcript_id)

    # 2. Poll for completion
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    while True:
        polling_response = requests.get(polling_endpoint, headers=headers)
        status = polling_response.json()['status']

        if status == 'completed':
            print("\n🎧 Transcription Result:\n")
            print(polling_response.json()['text'])
            break
        elif status == 'error':
            print("❌ Error:", polling_response.json()['error'])
            break
        else:
            print("⏳ Status:", status)
            time.sleep(3)

    music_text = polling_response.json()['text']
    return music_text
