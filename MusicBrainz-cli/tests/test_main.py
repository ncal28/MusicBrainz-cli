"""
tests/test_main.py

Tests for CLI commands with mocked API responses.
Tests the command-line interface without making real API calls.
"""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
from src.main import (
    is_valid_mbid,
    resolve_artist_mbid,
    resolve_release_mbid,
    format_duration,
    format_list,
    cmd_artist_info,
    cmd_artist_releases,
    cmd_album_info,
    cmd_album_tracks,
    main
)


# ==================== MOCK DATA (same as test_api.py) ====================

MOCK_ARTIST_SEARCH = {
    "artists": [
        {
            "id": "a74b1b7f-71a5-4011-9441-d0b5e4122711",
            "name": "Radiohead",
            "type": "Group",
            "country": "GB"
        }
    ]
}

MOCK_ARTIST_LOOKUP = {
    "id": "a74b1b7f-71a5-4011-9441-d0b5e4122711",
    "name": "Radiohead",
    "type": "Group",
    "country": "GB",
    "life-span": {
        "begin": "1985",
        "ended": False
    },
    "tags": [
        {"name": "rock", "count": 10},
        {"name": "alternative rock", "count": 8}
    ],
    "genres": [
        {"name": "alternative rock", "count": 5}
    ]
}

MOCK_RELEASE_SEARCH = {
    "releases": [
        {
            "id": "0b6b4ba0-d36f-47bd-b4ea-6a5b91842d29",
            "title": "OK Computer",
            "date": "1997-05-21",
            "status": "Official"
        }
    ]
}

MOCK_RELEASE_LOOKUP = {
    "id": "0b6b4ba0-d36f-47bd-b4ea-6a5b91842d29",
    "title": "OK Computer",
    "date": "1997-05-21",
    "status": "Official",
    "country": "GB",
    "barcode": "724385248023",
    "artist-credit": [
        {"name": "Radiohead"}
    ],
    "label-info": [
        {"label": {"name": "Parlophone"}}
    ],
    "tags": [
        {"name": "alternative rock", "count": 5}
    ]
}

MOCK_RELEASE_WITH_TRACKS = {
    "id": "0b6b4ba0-d36f-47bd-b4ea-6a5b91842d29",
    "title": "OK Computer",
    "artist-credit": [
        {"name": "Radiohead"}
    ],
    "media": [
        {
            "position": 1,
            "format": "CD",
            "track-count": 3,
            "tracks": [
                {"position": "1", "title": "Airbag", "length": 285000},
                {"position": "2", "title": "Paranoid Android", "length": 383000},
                {"position": "3", "title": "Subterranean Homesick Alien", "length": 270000}
            ]
        }
    ]
}

MOCK_BROWSE_RELEASES = {
    "releases": [
        {"id": "r1", "title": "Pablo Honey", "date": "1993", "status": "Official"},
        {"id": "r2", "title": "The Bends", "date": "1995", "status": "Official"}
    ],
    "release-count": 2
}


# ==================== HELPER FUNCTION TESTS ====================

def test_is_valid_mbid():
    """Test MBID validation."""
    # Valid MBIDs
    assert is_valid_mbid("a74b1b7f-71a5-4011-9441-d0b5e4122711") == True
    assert is_valid_mbid("A74B1B7F-71A5-4011-9441-D0B5E4122711") == True  # Case insensitive
    
    # Invalid MBIDs
    assert is_valid_mbid("not-a-valid-mbid") == False
    assert is_valid_mbid("Radiohead") == False
    assert is_valid_mbid("") == False
    assert is_valid_mbid(None) == False


def test_format_duration():
    """Test duration formatting."""
    assert format_duration(285000) == "4:45"
    assert format_duration(383000) == "6:23"
    assert format_duration(61000) == "1:01"
    assert format_duration(5000) == "0:05"
    assert format_duration(0) == "0:00"
    assert format_duration(None) == "0:00"
    assert format_duration(-1000) == "0:00"


def test_format_list():
    """Test list formatting with truncation."""
    # Short list
    items = ["rock", "pop", "jazz"]
    assert format_list(items) == "rock, pop, jazz"
    
    # Long list (should truncate)
    items = ["a", "b", "c", "d", "e", "f", "g"]
    result = format_list(items, max_items=5)
    assert result == "a, b, c, d, e, ..."
    
    # Empty list
    assert format_list([]) == "None"


def test_resolve_artist_mbid_with_valid_mbid():
    """Test that valid MBIDs are returned as-is."""
    api = MagicMock()
    mbid = "a74b1b7f-71a5-4011-9441-d0b5e4122711"
    
    result = resolve_artist_mbid(api, mbid)
    
    assert result == mbid
    # API should NOT be called if MBID is valid
    assert not api.search_artist.called


def test_resolve_artist_mbid_with_name():
    """Test resolving artist name to MBID."""
    api = MagicMock()
    api.search_artist.return_value = MOCK_ARTIST_SEARCH
    
    result = resolve_artist_mbid(api, "Radiohead")
    
    assert result == "a74b1b7f-71a5-4011-9441-d0b5e4122711"
    assert api.search_artist.called


def test_resolve_artist_mbid_not_found():
    """Test error when artist not found."""
    api = MagicMock()
    api.search_artist.return_value = {"artists": []}  # No results
    
    with pytest.raises(ValueError) as exc_info:
        resolve_artist_mbid(api, "NonexistentArtist")
    
    assert "not found" in str(exc_info.value)


def test_resolve_release_mbid_with_artist():
    """Test resolving release with artist name."""
    api = MagicMock()
    api.search_release.return_value = MOCK_RELEASE_SEARCH
    
    result = resolve_release_mbid(api, "OK Computer", artist="Radiohead")
    
    assert result == "0b6b4ba0-d36f-47bd-b4ea-6a5b91842d29"
    # Verify search was called with artist filter
    call_args = api.search_release.call_args[0][0]
    assert "OK Computer" in call_args
    assert "Radiohead" in call_args


# ==================== COMMAND TESTS ====================
# These test the actual CLI command functions

def test_cmd_artist_info(capsys):
    """
    Test artist-info command.
    
    capsys is a pytest fixture that captures stdout/stderr
    so we can verify what the command prints.
    """
    # Create mock API
    api = MagicMock()
    api.search_artist.return_value = MOCK_ARTIST_SEARCH
    api.lookup_artist.return_value = MOCK_ARTIST_LOOKUP
    
    # Create mock arguments (simulates argparse output)
    args = MagicMock()
    args.query = "Radiohead"
    
    # Run the command
    cmd_artist_info(api, args)
    
    # Capture the output
    captured = capsys.readouterr()
    
    # Verify output contains expected information
    assert "Radiohead" in captured.out
    assert "Group" in captured.out
    assert "GB" in captured.out
    assert "rock" in captured.out
    
    # Verify API was called correctly
    assert api.search_artist.called
    assert api.lookup_artist.called


def test_cmd_artist_info_with_mbid(capsys):
    """Test artist-info command when given an MBID directly."""
    api = MagicMock()
    api.lookup_artist.return_value = MOCK_ARTIST_LOOKUP
    
    args = MagicMock()
    args.query = "a74b1b7f-71a5-4011-9441-d0b5e4122711"
    
    cmd_artist_info(api, args)
    
    captured = capsys.readouterr()
    
    assert "Radiohead" in captured.out
    # Should NOT call search (MBID was provided)
    assert not api.search_artist.called
    assert api.lookup_artist.called


def test_cmd_artist_info_not_found(capsys):
    """Test artist-info command when artist not found."""
    api = MagicMock()
    api.search_artist.return_value = {"artists": []}  # No results
    
    args = MagicMock()
    args.query = "NonexistentArtist"
    
    # Command should exit with error
    with pytest.raises(SystemExit) as exc_info:
        cmd_artist_info(api, args)
    
    assert exc_info.value.code == 1  # Error exit code


def test_cmd_artist_releases(capsys):
    """Test artist-releases command."""
    api = MagicMock()
    api.search_artist.return_value = MOCK_ARTIST_SEARCH
    api.lookup_artist.return_value = MOCK_ARTIST_LOOKUP
    api.browse_releases_by_artist.return_value = MOCK_BROWSE_RELEASES
    
    args = MagicMock()
    args.query = "Radiohead"
    args.limit = 25
    args.type = None
    args.status = None
    
    cmd_artist_releases(api, args)
    
    captured = capsys.readouterr()
    
    # Verify output
    assert "Radiohead" in captured.out
    assert "Pablo Honey" in captured.out
    assert "The Bends" in captured.out
    assert "1993" in captured.out
    
    # Verify API calls
    assert api.browse_releases_by_artist.called


def test_cmd_artist_releases_with_filters(capsys):
    """Test artist-releases with type and status filters."""
    api = MagicMock()
    api.search_artist.return_value = MOCK_ARTIST_SEARCH
    api.lookup_artist.return_value = MOCK_ARTIST_LOOKUP
    api.browse_releases_by_artist.return_value = MOCK_BROWSE_RELEASES
    
    args = MagicMock()
    args.query = "Radiohead"
    args.limit = 10
    args.type = "album"
    args.status = "official"
    
    cmd_artist_releases(api, args)
    
    # Verify filters were passed to API
    call_kwargs = api.browse_releases_by_artist.call_args[1]
    assert call_kwargs['release_type'] == "album"
    assert call_kwargs['status'] == "official"


def test_cmd_album_info(capsys):
    """Test album-info command."""
    api = MagicMock()
    api.search_release.return_value = MOCK_RELEASE_SEARCH
    api.lookup_release.return_value = MOCK_RELEASE_LOOKUP
    
    args = MagicMock()
    args.query = "OK Computer"
    args.artist = "Radiohead"
    
    cmd_album_info(api, args)
    
    captured = capsys.readouterr()
    
    # Verify output
    assert "OK Computer" in captured.out
    assert "Radiohead" in captured.out
    assert "1997-05-21" in captured.out
    assert "Official" in captured.out
    assert "Parlophone" in captured.out
    
    # Verify API calls
    assert api.search_release.called
    assert api.lookup_release.called


def test_cmd_album_info_without_artist(capsys):
    """Test album-info command without artist filter."""
    api = MagicMock()
    api.search_release.return_value = MOCK_RELEASE_SEARCH
    api.lookup_release.return_value = MOCK_RELEASE_LOOKUP
    
    args = MagicMock()
    args.query = "OK Computer"
    args.artist = None  # No artist specified
    
    cmd_album_info(api, args)
    
    captured = capsys.readouterr()
    assert "OK Computer" in captured.out


def test_cmd_album_tracks(capsys):
    """Test album-tracks command."""
    api = MagicMock()
    api.search_release.return_value = MOCK_RELEASE_SEARCH
    api.lookup_release.return_value = MOCK_RELEASE_WITH_TRACKS
    
    args = MagicMock()
    args.query = "OK Computer"
    args.artist = "Radiohead"
    
    cmd_album_tracks(api, args)
    
    captured = capsys.readouterr()
    
    # Verify output
    assert "OK Computer" in captured.out
    assert "Radiohead" in captured.out
    assert "Airbag" in captured.out
    assert "Paranoid Android" in captured.out
    assert "4:45" in captured.out  # Duration of Airbag (285000ms)
    assert "6:23" in captured.out  # Duration of Paranoid Android (383000ms)
    assert "CD 1" in captured.out  # Format and disc number
    
    # Verify API calls
    assert api.search_release.called
    assert api.lookup_release.called


def test_cmd_album_tracks_no_tracks(capsys):
    """Test album-tracks when no track info available."""
    api = MagicMock()
    api.search_release.return_value = MOCK_RELEASE_SEARCH
    
    # Return release with no media/tracks
    release_no_tracks = {
        "id": "test-id",
        "title": "Test Album",
        "artist-credit": [{"name": "Test Artist"}],
        "media": []  # No tracks
    }
    api.lookup_release.return_value = release_no_tracks
    
    args = MagicMock()
    args.query = "Test Album"
    args.artist = None
    
    cmd_album_tracks(api, args)
    
    captured = capsys.readouterr()
    assert "No track information available" in captured.out


# ==================== CLI INTEGRATION TESTS ====================

@patch('sys.argv', ['main.py', 'artist-info', 'Radiohead'])
@patch('src.main.MusicBrainzAPI')
def test_main_artist_info_command(mock_api_class, capsys):
    """
    Test the main() function with artist-info command.
    
    This tests the full CLI flow from command-line args to output.
    """
    # Setup mock API
    mock_api = MagicMock()
    mock_api.search_artist.return_value = MOCK_ARTIST_SEARCH
    mock_api.lookup_artist.return_value = MOCK_ARTIST_LOOKUP
    mock_api_class.return_value = mock_api
    
    # Run main
    main()
    
    captured = capsys.readouterr()
    assert "Radiohead" in captured.out


@patch('sys.argv', ['main.py', 'artist-releases', 'Radiohead', '--limit', '10'])
@patch('src.main.MusicBrainzAPI')
def test_main_artist_releases_with_limit(mock_api_class, capsys):
    """Test main() with artist-releases command and limit argument."""
    mock_api = MagicMock()
    mock_api.search_artist.return_value = MOCK_ARTIST_SEARCH
    mock_api.lookup_artist.return_value = MOCK_ARTIST_LOOKUP
    mock_api.browse_releases_by_artist.return_value = MOCK_BROWSE_RELEASES
    mock_api_class.return_value = mock_api
    
    main()
    
    captured = capsys.readouterr()
    assert "Pablo Honey" in captured.out


@patch('sys.argv', ['main.py', 'album-info', 'OK Computer', '--artist', 'Radiohead'])
@patch('src.main.MusicBrainzAPI')
def test_main_album_info_with_artist(mock_api_class, capsys):
    """Test main() with album-info command and artist argument."""
    mock_api = MagicMock()
    mock_api.search_release.return_value = MOCK_RELEASE_SEARCH
    mock_api.lookup_release.return_value = MOCK_RELEASE_LOOKUP
    mock_api_class.return_value = mock_api
    
    main()
    
    captured = capsys.readouterr()
    assert "OK Computer" in captured.out


@patch('sys.argv', ['main.py', 'album-tracks', 'OK Computer'])
@patch('src.main.MusicBrainzAPI')
def test_main_album_tracks(mock_api_class, capsys):
    """Test main() with album-tracks command."""
    mock_api = MagicMock()
    mock_api.search_release.return_value = MOCK_RELEASE_SEARCH
    mock_api.lookup_release.return_value = MOCK_RELEASE_WITH_TRACKS
    mock_api_class.return_value = mock_api
    
    main()
    
    captured = capsys.readouterr()
    assert "Airbag" in captured.out


@patch('sys.argv', ['main.py', '--help'])
def test_main_help(capsys):
    """Test that --help works and shows all commands."""
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    # Help should exit with code 0
    assert exc_info.value.code == 0
    
    captured = capsys.readouterr()
    assert "artist-info" in captured.out
    assert "artist-releases" in captured.out
    assert "album-info" in captured.out
    assert "album-tracks" in captured.out


@patch('sys.argv', ['main.py'])
def test_main_no_command(capsys):
    """Test that running with no command shows error."""
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    # Should exit with error code
    assert exc_info.value.code != 0


@patch('sys.argv', ['main.py', 'artist-info'])
def test_main_missing_required_arg(capsys):
    """Test that missing required argument shows error."""
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    # Should exit with error code
    assert exc_info.value.code != 0


# ==================== ERROR HANDLING TESTS ====================

def test_cmd_artist_info_api_error(capsys):
    """Test artist-info command when API raises error."""
    from src.api import APIError
    
    api = MagicMock()
    api.search_artist.side_effect = APIError("Service unavailable")
    
    args = MagicMock()
    args.query = "Radiohead"
    
    with pytest.raises(SystemExit) as exc_info:
        cmd_artist_info(api, args)
    
    # Should exit with error code 2 (API error)
    assert exc_info.value.code == 2
    
    captured = capsys.readouterr()
    assert "API Error" in captured.err


def test_cmd_artist_releases_not_found(capsys):
    """Test artist-releases when artist not found."""
    api = MagicMock()
    api.search_artist.return_value = {"artists": []}
    
    args = MagicMock()
    args.query = "NonexistentArtist"
    args.limit = 25
    args.type = None
    args.status = None
    
    with pytest.raises(SystemExit) as exc_info:
        cmd_artist_releases(api, args)
    
    assert exc_info.value.code == 1


def test_cmd_album_tracks_not_found(capsys):
    """Test album-tracks when release not found."""
    api = MagicMock()
    api.search_release.return_value = {"releases": []}
    
    args = MagicMock()
    args.query = "NonexistentAlbum"
    args.artist = None
    
    with pytest.raises(SystemExit) as exc_info:
        cmd_album_tracks(api, args)
    
    assert exc_info.value.code == 1


# ==================== EDGE CASE TESTS ====================

def test_resolve_artist_mbid_empty_query():
    """Test resolving with empty query."""
    api = MagicMock()
    api.search_artist.return_value = {"artists": []}  # Empty query returns no results
    
    with pytest.raises(ValueError) as exc_info:
        resolve_artist_mbid(api, "")
    
    assert "not found" in str(exc_info.value)


def test_format_duration_large_value():
    """Test formatting very long durations."""
    # 1 hour = 3,600,000 ms
    assert format_duration(3600000) == "60:00"
    
    # 90 minutes
    assert format_duration(5400000) == "90:00"


def test_format_list_single_item():
    """Test formatting list with single item."""
    assert format_list(["rock"]) == "rock"


def test_cmd_artist_releases_no_releases(capsys):
    """Test artist-releases when artist has no releases."""
    api = MagicMock()
    api.search_artist.return_value = MOCK_ARTIST_SEARCH
    api.lookup_artist.return_value = MOCK_ARTIST_LOOKUP
    api.browse_releases_by_artist.return_value = {"releases": [], "release-count": 0}
    
    args = MagicMock()
    args.query = "Radiohead"
    args.limit = 25
    args.type = None
    args.status = None
    
    cmd_artist_releases(api, args)
    
    captured = capsys.readouterr()
    assert "No releases found" in captured.out


# ==================== SUMMARY ====================

"""
These tests cover:

1. Helper Functions:
   - MBID validation
   - Duration formatting
   - List formatting
   - MBID resolution

2. Command Functions:
   - artist-info (with name and MBID)
   - artist-releases (with and without filters)
   - album-info (with and without artist)
   - album-tracks (with tracks and without)

3. CLI Integration:
   - Full command-line argument parsing
   - Help text
   - Error handling

4. Error Cases:
   - Not found errors
   - API errors
   - Missing arguments
   - Empty results

All tests use mocking - NO real API calls are made!

Run with: pytest tests/test_main.py -v
"""


if __name__ == "__main__":
    # Run tests with: pytest tests/test_main.py -v
    pytest.main([__file__, "-v"])