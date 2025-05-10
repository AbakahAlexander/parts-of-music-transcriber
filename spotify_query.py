import requests

def search_track(query, access_token, limit=5, return_results=False):
    """
    Search for tracks on Spotify
    
    Args:
        query (str): Search query
        access_token (str): Spotify API access token
        limit (int): Maximum number of results to return
        return_results (bool): Whether to return results as a list
        
    Returns:
        list: List of track objects if return_results is True, otherwise None
    """
    endpoint = "https://api.spotify.com/v1/search"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "q": query,
        "type": "track",
        "limit": limit
    }
    
    response = requests.get(endpoint, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.json())
        if return_results:
            return []
        return None
    
    data = response.json()
    tracks = data.get("tracks", {}).get("items", [])
    
    if not return_results:
        # Print track information
        for i, track in enumerate(tracks):
            artists = ", ".join([artist["name"] for artist in track["artists"]])
            print(f"{i+1}. {track['name']} by {artists}")
            print(f"   Link: {track['external_urls']['spotify']}")
            print()
        return None
    else:
        # Return track information as a list
        return tracks

