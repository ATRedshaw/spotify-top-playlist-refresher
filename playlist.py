from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables from .env file
print("Loading environment variables...")
load_dotenv()

# Retrieve Spotify API credentials from environment variables
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
refresh_token = os.getenv('SPOTIPY_REFRESH_TOKEN')

# Check if environment variables are loaded
print(f"Client ID: {'Loaded' if client_id else 'Missing'}")
print(f"Client Secret: {'Loaded' if client_secret else 'Missing'}")
print(f"Redirect URI: {'Loaded' if redirect_uri else 'Missing'}")
print(f"Refresh Token: {'Loaded' if refresh_token else 'Missing'}")

# Set up authentication
print("Setting up Spotify OAuth...")
try:
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-top-read playlist-modify-private playlist-modify-public playlist-read-private"
    )
    auth_manager.refresh_token = refresh_token
    print("Authentication manager initialized successfully.")
except Exception as e:
    print(f"Error setting up Spotify OAuth: {e}")
    exit(1)

# Initialize Spotify client
print("Initializing Spotify client...")
try:
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("Spotify client initialized.")
except Exception as e:
    print(f"Error initializing Spotify client: {e}")
    exit(1)

def get_top_tracks(limit, time_range):
    """
    Fetch top tracks from Spotify for a user.
    """
    print(f"Fetching top {limit} tracks for time range: {time_range}")
    tracks = []
    offset = 0
    while len(tracks) < limit:
        try:
            results = sp.current_user_top_tracks(limit=50, offset=offset, time_range=time_range)
            tracks.extend(results['items'])
            print(f"Fetched {len(results['items'])} tracks (offset: {offset})")
            if len(results['items']) < 50:
                break
            offset += 50
        except Exception as e:
            print(f"Error fetching top tracks: {e}")
            break
    print(f"Total tracks fetched: {len(tracks)}")
    return tracks[:limit]

def get_or_create_playlist(name, is_private, description):
    """
    Retrieve an existing playlist or create a new one if it doesn't exist.
    """
    print(f"Looking for playlist '{name}'...")
    try:
        user_id = sp.me()['id']
        playlists = sp.user_playlists(user_id)
        for playlist in playlists['items']:
            if playlist['name'] == name:
                # Update playlist privacy and description if needed
                print(f"Found playlist '{name}'. Updating if necessary...")
                sp.user_playlist_change_details(
                    user_id, 
                    playlist['id'], 
                    public=not is_private,
                    description=description
                )
                return playlist
        print(f"Playlist '{name}' not found. Creating new playlist...")
        return sp.user_playlist_create(user_id, name, public=not is_private, description=description)
    except Exception as e:
        print(f"Error getting or creating playlist: {e}")
        exit(1)

def update_playlist(time_range, track_limit, is_private):
    """
    Update a playlist with top tracks for a given time range.
    """
    print(f"Updating playlist for time range: {time_range}")
    
    time_range_names = {
        'short_term': 'Last 4 Weeks',
        'medium_term': 'Last 6 Months',
        'long_term': 'All Time'
    }
    playlist_name = f"Top {track_limit} Songs - {time_range_names[time_range]}"
    playlist_description = f"This playlist contains my top {track_limit} tracks from {time_range_names[time_range].lower()}."

    # Retrieve top tracks
    top_tracks = get_top_tracks(limit=track_limit, time_range=time_range)
    if not top_tracks:
        print("No top tracks found, skipping playlist update.")
        return

    # Get or create playlist
    playlist = get_or_create_playlist(playlist_name, is_private, playlist_description)

    # Clear existing tracks from the playlist
    print(f"Clearing existing tracks from playlist '{playlist_name}'...")
    try:
        sp.playlist_replace_items(playlist['id'], [])
    except Exception as e:
        print(f"Error clearing playlist: {e}")
        exit(1)

    # Add new tracks to the playlist
    track_uris = [track['uri'] for track in top_tracks]
    print(f"Adding {len(track_uris)} tracks to playlist '{playlist_name}'...")
    try:
        sp.playlist_add_items(playlist['id'], track_uris)
    except Exception as e:
        print(f"Error adding tracks to playlist: {e}")
        exit(1)

    print('-' * 30)
    print(f"Playlist '{playlist_name}' updated successfully!")
    print(f"Total tracks added: {len(track_uris)}")
    print(f"Playlist privacy: {'Private' if is_private else 'Public'}")
    print('-' * 30)

def main():
    """
    Main function to update playlists for different time ranges.
    """
    print("Starting playlist update process...")

    # Set track limit and playlist privacy
    track_limit = 100
    is_playlist_private = False

    # Update playlists for all time ranges
    time_ranges = ['short_term', 'medium_term', 'long_term']
    for time_range in time_ranges:
        update_playlist(time_range, track_limit, is_playlist_private)

    print("Playlist update process completed.")

if __name__ == "__main__":
    main()
