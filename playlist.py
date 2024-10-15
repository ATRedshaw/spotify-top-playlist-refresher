import sys
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def print_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

# Load environment variables from .env file
print_flush("Loading environment variables...")
load_dotenv()

# Retrieve Spotify API credentials from environment variables
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
refresh_token = os.getenv('SPOTIPY_REFRESH_TOKEN')

# Check if environment variables are loaded
print_flush(f"Client ID: {'Loaded' if client_id else 'Missing'}")
print_flush(f"Client Secret: {'Loaded' if client_secret else 'Missing'}")
print_flush(f"Redirect URI: {'Loaded' if redirect_uri else 'Missing'}")
print_flush(f"Refresh Token: {'Loaded' if refresh_token else 'Missing'}")

# Set up authentication
print_flush("Setting up Spotify OAuth...")
try:
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-top-read playlist-modify-private playlist-modify-public playlist-read-private"
    )
    auth_manager.refresh_token = refresh_token
    print_flush("Authentication manager initialized successfully.")
except Exception as e:
    print_flush(f"Error setting up Spotify OAuth: {e}")
    sys.exit(1)

# Initialize Spotify client
print_flush("Initializing Spotify client...")
try:
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print_flush("Spotify client initialized.")
except Exception as e:
    print_flush(f"Error initializing Spotify client: {e}")
    sys.exit(1)

def get_top_tracks(limit, time_range):
    """
    Fetch top tracks from Spotify for a user.
    """
    print_flush(f"Fetching top {limit} tracks for time range: {time_range}")
    tracks = []
    offset = 0
    while len(tracks) < limit:
        try:
            results = sp.current_user_top_tracks(limit=50, offset=offset, time_range=time_range)
            tracks.extend(results['items'])
            print_flush(f"Fetched {len(results['items'])} tracks (offset: {offset})")
            if len(results['items']) < 50:
                break
            offset += 50
        except Exception as e:
            print_flush(f"Error fetching top tracks: {e}")
            break
    print_flush(f"Total tracks fetched: {len(tracks)}")
    return tracks[:limit]

def get_or_create_playlist(name, is_private, description):
    """
    Retrieve an existing playlist or create a new one if it doesn't exist.
    """
    print_flush(f"Looking for playlist '{name}'...")
    try:
        user_id = sp.me()['id']
        playlists = sp.user_playlists(user_id)
        for playlist in playlists['items']:
            if playlist['name'] == name:
                print_flush(f"Found playlist '{name}'. Updating if necessary...")
                sp.user_playlist_change_details(
                    user_id, 
                    playlist['id'], 
                    public=not is_private,
                    description=description
                )
                return playlist
        print_flush(f"Playlist '{name}' not found. Creating new playlist...")
        return sp.user_playlist_create(user_id, name, public=not is_private, description=description)
    except Exception as e:
        print_flush(f"Error getting or creating playlist: {e}")
        sys.exit(1)

def update_playlist(time_range, track_limit, is_private):
    """
    Update a playlist with top tracks for a given time range, preserving existing tracks.
    """
    print_flush(f"Updating playlist for time range: {time_range}")
    
    time_range_names = {
        'short_term': 'Last 4 Weeks',
        'medium_term': 'Last 6 Months',
        'long_term': 'All Time'
    }
    playlist_name = f"Top {track_limit} Songs - {time_range_names[time_range]}"
    playlist_description = f"This playlist contains my top {track_limit} tracks from {time_range_names[time_range].lower()}."

    top_tracks = get_top_tracks(limit=track_limit, time_range=time_range)
    if not top_tracks:
        print_flush("No top tracks found, skipping playlist update.")
        return

    playlist = get_or_create_playlist(playlist_name, is_private, playlist_description)

    # Get current tracks in the playlist
    current_tracks = []
    results = sp.playlist_items(playlist['id'], fields="items(track(uri))")
    current_tracks = [item['track']['uri'] for item in results['items']]

    # Create a set of current track URIs for faster lookup
    current_track_set = set(current_tracks)

    # Prepare the new track list
    new_track_list = []
    tracks_to_add = []

    for track in top_tracks:
        if track['uri'] in current_track_set:
            new_track_list.append(track['uri'])
        else:
            tracks_to_add.append(track['uri'])

    # Add any remaining current tracks that are not in the top tracks
    new_track_list.extend([uri for uri in current_tracks if uri not in new_track_list])

    # Trim the list to the desired limit
    new_track_list = new_track_list[:track_limit]

    print_flush(f"Reordering tracks in playlist '{playlist_name}'...")
    try:
        sp.playlist_replace_items(playlist['id'], new_track_list)
    except Exception as e:
        print_flush(f"Error reordering playlist: {e}")
        sys.exit(1)

    if tracks_to_add:
        print_flush(f"Adding {len(tracks_to_add)} new tracks to playlist '{playlist_name}'...")
        try:
            sp.playlist_add_items(playlist['id'], tracks_to_add)
        except Exception as e:
            print_flush(f"Error adding new tracks to playlist: {e}")
            sys.exit(1)

    print_flush('-' * 30)
    print_flush(f"Playlist '{playlist_name}' updated successfully!")
    print_flush(f"Total tracks: {len(new_track_list)}")
    print_flush(f"New tracks added: {len(tracks_to_add)}")
    print_flush(f"Playlist privacy: {'Private' if is_private else 'Public'}")
    print_flush('-' * 30)

def main():
    """
    Main function to update playlists for different time ranges.
    """
    print_flush("Starting playlist update process...")

    track_limit = 100
    is_playlist_private = False

    time_ranges = ['short_term', 'medium_term', 'long_term']
    for time_range in time_ranges:
        update_playlist(time_range, track_limit, is_playlist_private)

    print_flush("Playlist update process completed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_flush(f"An unexpected error occurred: {e}")
        sys.exit(1)