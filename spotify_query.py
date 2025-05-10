import requests

# Replace with your valid token


def search_track(query,access_token, limit=3):
    url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": query,
        "type": "track",
        "limit": limit
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return

    data = response.json()
    tracks = data.get("tracks", {}).get("items", [])
    
    for i, track in enumerate(tracks, 1):
        name = track["name"]
        artists = ", ".join([a["name"] for a in track["artists"]])
        url = track["external_urls"]["spotify"]
        print(f"{i}. {name} by {artists} - {url}")

