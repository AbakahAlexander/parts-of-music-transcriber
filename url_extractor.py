import requests
import os

def url_extractor(audio_path):
    # Upload audio
    upload_url = "https://api.assemblyai.com/v2/upload"
    headers = {"authorization": os.getenv('API_KEY')}

    with open(audio_path, 'rb') as f:
        response = requests.post(upload_url, headers=headers, data=f)

    print(response.status_code, response.text)

    # Extract URL
    if response.status_code == 200:
        audio_url = response.json()['upload_url']
    else:
        raise Exception("Upload failed")

    return audio_url
