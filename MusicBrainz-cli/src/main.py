"""
src/main.py

MusicBrainz CLI - Command-line interface for exploring music metadata.
Provides 4 core commands for artist and album information.
"""

import argparse
import sys
import re
from typing import Dict, Any, Optional
from src.api import MusicBrainzAPI, APIError


# ==================== HELPER FUNCTIONS ====================

MBID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


def is_valid_mbid(string: str) -> bool:
    """
    Check if string is a valid MusicBrainz Identifier (MBID).
    
    Args:
        string: String to validate
    
    Returns:
        True if valid MBID format, False otherwise
    """
    if not string or not isinstance(string, str):
        return False
    return MBID_PATTERN.match(string) is not None


def resolve_artist_mbid(api: MusicBrainzAPI, query: str) -> str:
    """
    Convert artist name or MBID to MBID.
    
    If query is already a valid MBID, return it.
    Otherwise, search for the artist and return the first result's MBID.
    
    Args:
        api: MusicBrainz API instance
        query: Artist name or MBID
    
    Returns:
        Artist MBID
    
    Raises:
        ValueError: If artist not found
    """
    if is_valid_mbid(query):
        return query
    
    results = api.search_artist(query, limit=1)
    artists = results.get('artists', [])
    
    if not artists:
        raise ValueError(f"Artist '{query}' not found")
    
    return artists[0]['id']


def resolve_release_mbid(api: MusicBrainzAPI, query: str, artist: Optional[str] = None) -> str:
    """
    Convert release name or MBID to MBID.
    
    If query is already a valid MBID, return it.
    Otherwise, search for the release and return the first result's MBID.
    
    Args:
        api: MusicBrainz API instance
        query: Release name or MBID
        artist: Optional artist name to narrow search
    
    Returns:
        Release MBID
    
    Raises:
        ValueError: If release not found
    """
    if is_valid_mbid(query):
        return query
    
    search_query = query
    if artist:
        search_query = f'release:"{query}" AND artist:"{artist}"'
    
    results = api.search_release(search_query, limit=1)
    releases = results.get('releases', [])
    
    if not releases:
        if artist:
            raise ValueError(f"Release '{query}' by '{artist}' not found")
        else:
            raise ValueError(f"Release '{query}' not found")
    
    return releases[0]['id']


def format_duration(milliseconds: int) -> str:
    """
    Convert milliseconds to MM:SS format.
    
    Args:
        milliseconds: Duration in milliseconds
    
    Returns:
        Formatted string in MM:SS format
    """
    if not milliseconds or milliseconds < 0:
        return "0:00"
    
    seconds = milliseconds // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    
    return f"{minutes}:{seconds:02d}"


def format_list(items: list, max_items: int = 5) -> str:
    """
    Format a list of items as a string with truncation.
    
    Args:
        items: List of items to format
        max_items: Maximum items to show before truncating
    
    Returns:
        Formatted string
    """
    if not items:
        return "None"
    
    if len(items) <= max_items:
        return ", ".join(str(item) for item in items)
    
    truncated = ", ".join(str(item) for item in items[:max_items])
    return f"{truncated}, ..."


# ==================== COMMAND FUNCTIONS ====================

def cmd_artist_info(api: MusicBrainzAPI, args: argparse.Namespace) -> None:
    """
    Display detailed information about an artist.
    
    Shows artist name, MBID, type, country, active period, and tags/genres.
    
    Args:
        api: MusicBrainz API instance
        args: Parsed command-line arguments
    """
    try:
        print(f"Searching for '{args.query}'...")
        mbid = resolve_artist_mbid(api, args.query)
        
        artist = api.lookup_artist(mbid, inc='tags+genres+aliases')
        
        # Display artist information
        name = artist.get('name', 'Unknown')
        print(f"\n{'=' * 60}")
        print(f"{name}")
        print(f"{'=' * 60}\n")
        
        print(f"MBID:    {artist.get('id', 'N/A')}")
        print(f"Type:    {artist.get('type', 'Unknown')}")
        print(f"Country: {artist.get('country', 'Unknown')}")
        
        # Life span
        life_span = artist.get('life-span', {})
        if life_span:
            begin = life_span.get('begin', '?')
            if life_span.get('ended'):
                end = life_span.get('end', '?')
                print(f"Active:  {begin} - {end}")
            else:
                print(f"Active:  {begin} - present")
        
        # Disambiguation
        disambiguation = artist.get('disambiguation', '')
        if disambiguation:
            print(f"Note:    {disambiguation}")
        
        # Tags
        tags = artist.get('tags', [])
        if tags:
            tag_names = [tag['name'] for tag in tags[:10]]
            print(f"\nTags:    {format_list(tag_names, max_items=10)}")
        
        # Genres
        genres = artist.get('genres', [])
        if genres:
            genre_names = [genre['name'] for genre in genres[:10]]
            print(f"Genres:  {format_list(genre_names, max_items=10)}")
        
        print()
        
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except APIError as e:
        print(f"\nAPI Error: {e}", file=sys.stderr)
        sys.exit(2)


def cmd_artist_releases(api: MusicBrainzAPI, args: argparse.Namespace) -> None:
    """
    List all releases by an artist.
    
    Shows release title, date, status, and MBID with optional filtering
    by type (album, single, etc.) and status (official, bootleg, etc.).
    
    Args:
        api: MusicBrainz API instance
        args: Parsed command-line arguments
    """
    try:
        print(f"Searching for '{args.query}'...")
        mbid = resolve_artist_mbid(api, args.query)
        
        artist = api.lookup_artist(mbid)
        artist_name = artist.get('name', 'Unknown')
        print(f"Found: {artist_name}\n")
        
        print("Fetching releases...")
        releases_data = api.browse_releases_by_artist(
            mbid,
            limit=args.limit,
            release_type=args.type if hasattr(args, 'type') and args.type else None,
            status=args.status if hasattr(args, 'status') and args.status else None
        )
        
        releases = releases_data.get('releases', [])
        
        if not releases:
            print(f"\nNo releases found for {artist_name}.")
            return
        
        release_count = releases_data.get('release-count', len(releases))
        
        print(f"\n{'=' * 60}")
        print(f"Releases by {artist_name}")
        print(f"{'=' * 60}")
        print(f"Showing {len(releases)} of {release_count} total releases\n")
        
        for i, release in enumerate(releases, 1):
            title = release.get('title', 'Unknown')
            date = release.get('date', 'Unknown date')
            status = release.get('status', 'Unknown')
            
            print(f"{i:3d}. {title}")
            print(f"      {date} | {status}")
            print(f"      MBID: {release.get('id', 'N/A')}")
            print()
        
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except APIError as e:
        print(f"\nAPI Error: {e}", file=sys.stderr)
        sys.exit(2)


def cmd_album_info(api: MusicBrainzAPI, args: argparse.Namespace) -> None:
    """
    Display detailed information about an album/release.
    
    Shows album title, artist, release date, status, country, labels,
    barcode, and tags.
    
    Args:
        api: MusicBrainz API instance
        args: Parsed command-line arguments
    """
    try:
        print(f"Searching for '{args.query}'...")
        artist_arg = args.artist if hasattr(args, 'artist') and args.artist else None
        mbid = resolve_release_mbid(api, args.query, artist=artist_arg)
        
        release = api.lookup_release(mbid, inc='artist-credits+labels+tags+genres')
        
        # Display release information
        title = release.get('title', 'Unknown')
        print(f"\n{'=' * 60}")
        print(f"{title}")
        print(f"{'=' * 60}\n")
        
        print(f"MBID:   {release.get('id', 'N/A')}")
        
        # Artist credits
        artist_credit = release.get('artist-credit', [])
        if artist_credit:
            artists = ', '.join([ac.get('name', 'Unknown') for ac in artist_credit])
            print(f"Artist: {artists}")
        
        print(f"Date:   {release.get('date', 'Unknown')}")
        print(f"Status: {release.get('status', 'Unknown')}")
        print(f"Country: {release.get('country', 'Unknown')}")
        
        # Label information
        label_info = release.get('label-info', [])
        if label_info:
            labels = [li.get('label', {}).get('name', 'Unknown') for li in label_info]
            print(f"Labels: {format_list(labels, max_items=3)}")
        
        # Barcode
        barcode = release.get('barcode', '')
        if barcode:
            print(f"Barcode: {barcode}")
        
        # Tags
        tags = release.get('tags', [])
        if tags:
            tag_names = [tag['name'] for tag in tags[:10]]
            print(f"\nTags: {format_list(tag_names, max_items=10)}")
        
        print()
        
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except APIError as e:
        print(f"\nAPI Error: {e}", file=sys.stderr)
        sys.exit(2)


def cmd_album_tracks(api: MusicBrainzAPI, args: argparse.Namespace) -> None:
    """
    Show tracklist for an album/release.
    
    Displays all tracks with track number, title, and duration.
    Supports multi-disc releases.
    
    Args:
        api: MusicBrainz API instance
        args: Parsed command-line arguments
    """
    try:
        print(f"Searching for '{args.query}'...")
        artist_arg = args.artist if hasattr(args, 'artist') and args.artist else None
        mbid = resolve_release_mbid(api, args.query, artist=artist_arg)
        
        release = api.lookup_release(mbid, inc='recordings+artist-credits')
        
        title = release.get('title', 'Unknown')
        artist_credit = release.get('artist-credit', [])
        artists = ', '.join([ac.get('name', 'Unknown') for ac in artist_credit])
        
        print(f"\n{'=' * 60}")
        print(f"{title}")
        print(f"by {artists}")
        print(f"{'=' * 60}\n")
        
        media = release.get('media', [])
        
        if not media:
            print("No track information available.")
            return
        
        for medium in media:
            medium_position = medium.get('position', 1)
            format_name = medium.get('format', 'Medium')
            track_count = medium.get('track-count', 0)
            
            print(f"{format_name} {medium_position} ({track_count} tracks):")
            print()
            
            tracks = medium.get('tracks', [])
            for track in tracks:
                position = track.get('position', '?')
                track_title = track.get('title', 'Unknown')
                length = track.get('length', 0)
                duration = format_duration(length) if length else "?"
                
                print(f"  {position:>2}. {track_title} ({duration})")
            
            print()
        
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except APIError as e:
        print(f"\nAPI Error: {e}", file=sys.stderr)
        sys.exit(2)


# ==================== CLI SETUP ====================

def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser with all commands.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='musicbrainz-cli',
        description='MusicBrainz CLI - Explore music metadata from the terminal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s artist-info "Radiohead"
  %(prog)s artist-releases "Miles Davis" --limit 20 --type album
  %(prog)s album-info "OK Computer" --artist "Radiohead"
  %(prog)s album-tracks "Abbey Road" --artist "The Beatles"

For more information, visit: https://musicbrainz.org
        """
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        required=True
    )
    
    # artist-info command
    parser_artist_info = subparsers.add_parser(
        'artist-info',
        help='Display detailed information about an artist'
    )
    parser_artist_info.add_argument('query', help='Artist name or MBID')
    parser_artist_info.set_defaults(func=cmd_artist_info)
    
    # artist-releases command
    parser_artist_releases = subparsers.add_parser(
        'artist-releases',
        help='List all releases by an artist'
    )
    parser_artist_releases.add_argument('query', help='Artist name or MBID')
    parser_artist_releases.add_argument(
        '--limit',
        type=int,
        default=25,
        help='Maximum results (default: 25)'
    )
    parser_artist_releases.add_argument(
        '--type',
        choices=['album', 'single', 'ep', 'broadcast', 'other'],
        help='Filter by release type'
    )
    parser_artist_releases.add_argument(
        '--status',
        choices=['official', 'promotion', 'bootleg', 'pseudo-release'],
        help='Filter by release status'
    )
    parser_artist_releases.set_defaults(func=cmd_artist_releases)
    
    # album-info command
    parser_album_info = subparsers.add_parser(
        'album-info',
        help='Display detailed information about an album'
    )
    parser_album_info.add_argument('query', help='Album name or MBID')
    parser_album_info.add_argument('--artist', help='Artist name to narrow search')
    parser_album_info.set_defaults(func=cmd_album_info)
    
    # album-tracks command
    parser_album_tracks = subparsers.add_parser(
        'album-tracks',
        help='Show tracklist for an album'
    )
    parser_album_tracks.add_argument('query', help='Album name or MBID')
    parser_album_tracks.add_argument('--artist', help='Artist name to narrow search')
    parser_album_tracks.set_defaults(func=cmd_album_tracks)
    
    return parser


def main():
    """
    Main entry point for the CLI application.
    
    Parses arguments, initializes API client, and routes to appropriate command.
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Initialize API client
    api = MusicBrainzAPI()
    
    # Route to the appropriate command function
    try:
        args.func(api, args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()