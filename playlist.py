from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables from .env file
load_dotenv()

# Retrieve Spotify API credentials from environment variables
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
refresh_token = os.getenv('SPOTIPY_REFRESH_TOKEN')

# Set up authentication
auth_manager = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="user-top-read playlist-modify-private playlist-modify-public playlist-read-private"
)

# Set the refresh token
auth_manager.refresh_token = refresh_token

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=auth_manager)

def get_top_tracks(limit, time_range):
    """
    Fetch top tracks from Spotify for a user.

    Args:
        limit (int): The number of tracks to fetch.
        time_range (str): The time frame to consider. Options are:
                          'short_term' (last 4 weeks),
                          'medium_term' (last 6 months),
                          'long_term' (all time)

    Returns:
        list: A list of top tracks.
    """
    tracks = []
    offset = 0
    while len(tracks) < limit:
        results = sp.current_user_top_tracks(limit=50, offset=offset, time_range=time_range)
        tracks.extend(results['items'])
        if len(results['items']) < 50:
            break
        offset += 50
    return tracks[:limit]

def get_or_create_playlist(name, is_private, description):
    """
    Retrieve an existing playlist or create a new one if it doesn't exist.

    Args:
        name (str): The name of the playlist to find or create.
        is_private (bool): Whether the playlist should be private.
        description (str): The description for the playlist.

    Returns:
        dict: The playlist object.
    """
    user_id = sp.me()['id']
    playlists = sp.user_playlists(user_id)
    for playlist in playlists['items']:
        if playlist['name'] == name:
            # Update playlist privacy and description if they don't match the desired settings
            sp.user_playlist_change_details(
                user_id, 
                playlist['id'], 
                public=not is_private,
                description=description
            )
            return playlist
    return sp.user_playlist_create(user_id, name, public=not is_private, description=description)


def update_playlist(time_range, track_limit, is_private):
    """
    Update a playlist with top tracks for a given time range.

    Args:
        time_range (str): The time frame for the top tracks.
        track_limit (int): The number of tracks to include in the playlist.
        is_private (bool): Whether the playlist should be private.
    """
    # Define playlist name and description based on time range
    time_range_names = {
        'short_term': 'Last 4 Weeks',
        'medium_term': 'Last 6 Months',
        'long_term': 'All Time'
    }
    playlist_name = f"Top {track_limit} Songs - {time_range_names[time_range]}"
    playlist_description = f"This playlist contains my top {track_limit} tracks from {time_range_names[time_range].lower()}. It uses the Spotify API and Github Actions to update daily to reflect my listening trends."

    # Retrieve top tracks
    top_tracks = get_top_tracks(limit=track_limit, time_range=time_range)

    # Get or create playlist
    playlist = get_or_create_playlist(playlist_name, is_private, playlist_description)

    # Clear existing tracks from the playlist
    sp.playlist_replace_items(playlist['id'], [])

    # Add new tracks to the playlist
    track_uris = [track['uri'] for track in top_tracks]
    sp.playlist_add_items(playlist['id'], track_uris)

    print('-'*30)
    print(f"Playlist '{playlist_name}' updated successfully!")
    print(f"Total tracks added: {len(track_uris)}")
    print(f"Playlist privacy: {'Private' if is_private else 'Public'}")
    print('-'*30)
    print("\n")

def main():
    """
    Main function to update playlists for different time ranges.
    """
    # Set track limit and playlist privacy
    track_limit = 100
    is_playlist_private = False

    # Update playlists for all time ranges
    time_ranges = ['short_term', 'medium_term', 'long_term']
    for time_range in time_ranges:
        update_playlist(time_range, track_limit, is_playlist_private)

if __name__ == "__main__":
    main()