import requests
import base64
import os

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

def get_access_token(client_id, client_secret):
    url = 'https://accounts.spotify.com/api/token'
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials'
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print("Failed to get token:", response.status_code, response.text)
        return None

    token_info = response.json()
    return token_info['access_token']

# Example usage
access_token = get_access_token(client_id, client_secret)


