import re
import urllib.request
import urllib.parse
import json
import base64
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request, status

from server.models import SpotifyTracksRequest
from server.security import verify_token

router = APIRouter(
    prefix="/spotify",
    tags=["spotify"],
    dependencies=[Depends(verify_token)]
)

def fetch_spotify_tracks(playlist_id: str, client_id: str, client_secret: str) -> list:
    # 1. Fetch access token
    auth_str = f"{client_id}:{client_secret}"
    auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    
    token_url = "https://accounts.spotify.com/api/token"
    payload = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode('utf-8')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    token_req = urllib.request.Request(token_url, data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(token_req, timeout=10) as res:
            token_data = json.loads(res.read().decode('utf-8'))
            access_token = token_data["access_token"]
    except Exception as e:
        raise Exception(f"Spotify Authentication failed. Please check your Spotify Client ID and Client Secret. Details: {str(e)}")

    # 2. Fetch tracks
    tracks = []
    next_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=100"
    tracks_headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    while next_url and len(tracks) < 300:
        req = urllib.request.Request(next_url, headers=tracks_headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                res_data = json.loads(res.read().decode('utf-8'))
                for item in res_data.get("items", []):
                    track_info = item.get("track")
                    if not track_info:
                        continue
                    
                    name = track_info.get("name")
                    artists = [a.get("name") for a in track_info.get("artists", [])]
                    duration_ms = track_info.get("duration_ms", 0)
                    duration_sec = int(duration_ms / 1000)
                    
                    thumb_url = ""
                    album = track_info.get("album")
                    if album and album.get("images"):
                        thumb_url = album.get("images")[0].get("url")
                        
                    tracks.append({
                        "name": name,
                        "artists": ", ".join(artists) if artists else "Unknown Artist",
                        "duration": duration_sec,
                        "thumbnail": thumb_url
                    })
                next_url = res_data.get("next")
        except Exception as e:
            raise Exception(f"Failed to fetch tracks from Spotify API. Details: {str(e)}")
            
    return tracks

@router.post("/playlist-tracks")
async def get_playlist_tracks(req_body: SpotifyTracksRequest, request: Request):
    # Parse playlist ID
    match = re.search(r'playlist/([a-zA-Z0-9]+)', req_body.url)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz Spotify playlist URL'si. / Invalid Spotify playlist URL."
        )
    playlist_id = match.group(1)
    
    # Get credentials from global preferences
    controller = request.app.state.server.controller
    prefs = controller.state.preferences
    client_id = prefs.spotify_client_id
    client_secret = prefs.spotify_client_secret
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lütfen Ayarlar panelinden Spotify Client ID ve Client Secret değerlerini girin. / Please configure Spotify Client ID and Client Secret in Settings."
        )
        
    try:
        # Run blocking network requests in a separate thread
        tracks = await asyncio.to_thread(fetch_spotify_tracks, playlist_id, client_id, client_secret)
        return {"tracks": tracks}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
