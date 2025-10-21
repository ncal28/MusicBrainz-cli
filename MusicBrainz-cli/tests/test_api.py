"""
tests/test_api.py

Tests for MusicBrainz API client with mocked HTTP requests.
No real API calls are made during testing.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.api import MusicBrainzAPI, APIError


# ==================== MOCK DATA ====================
# These are fake API responses that look like real MusicBrainz data

MOCK_ARTIST_SEARCH = {
    "artists": [
        {
            "id": "a74b1b7f-71a5-4011-9441-d0b5e4122711",
            "name": "Radiohead",
            "type": "Group",
            "country": "GB",
            "score": 100
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
            "status": "Official",
            "artist-credit": [
                {"name": "Radiohead"}
            ]
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
        {
            "label": {
                "name": "Parlophone"
            }
        }
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
                {
                    "position": "1",
                    "title": "Airbag",
                    "length": 285000
                },
                {
                    "position": "2",
                    "title": "Paranoid Android",
                    "length": 383000
                },
                {
                    "position": "3",
                    "title": "Subterranean Homesick Alien",
                    "length": 270000
                }
            ]
        }
    ]
}

MOCK_BROWSE_RELEASES = {
    "releases": [
        {
            "id": "release-1",
            "title": "Pablo Honey",
            "date": "1993-02-22",
            "status": "Official"
        },
        {
            "id": "release-2",
            "title": "The Bends",
            "date": "1995-03-13",
            "status": "Official"
        }
    ],
    "release-count": 2
}


# ==================== HELPER FUNCTION ====================

def create_mock_response(data: dict):
    """
    Create a mock HTTP response that looks like urllib.request.urlopen() result.
    
    This is the key function that makes mocking work!
    
    Args:
        data: Dictionary to return as JSON
    
    Returns:
        Mock object that behaves like a real HTTP response
    """
    # Create a fake response object
    mock_response = MagicMock()
    
    # When someone calls .read(), return JSON data as bytes
    # The decode() is called on the bytes, so we return bytes directly
    mock_response.read.return_value = json.dumps(data).encode('utf-8')
    
    return mock_response


# ==================== SEARCH TESTS ====================

@patch('src.api.urllib.request.urlopen')  # Replace real urlopen with mock
def test_search_artist(mock_urlopen):
    """
    Test searching for an artist.
    
    This test:
    1. Creates fake API response data
    2. Tells the mock to return that data
    3. Calls the real API method
    4. Verifies it parsed the fake data correctly
    
    NO real API call is made!
    """
    # Setup: Tell the mock what to return
    mock_response = create_mock_response(MOCK_ARTIST_SEARCH)
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    # Execute: Call the API method
    api = MusicBrainzAPI()
    result = api.search_artist("Radiohead", limit=1)
    
    # Verify: Check the result
    assert 'artists' in result
    assert len(result['artists']) == 1
    assert result['artists'][0]['name'] == "Radiohead"
    assert result['artists'][0]['id'] == "a74b1b7f-71a5-4011-9441-d0b5e4122711"
    
    # Verify that urlopen was actually called (API method ran)
    assert mock_urlopen.called


@patch('src.api.urllib.request.urlopen')
def test_search_release(mock_urlopen):
    """Test searching for a release (album)."""
    mock_response = create_mock_response(MOCK_RELEASE_SEARCH)
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    api = MusicBrainzAPI()
    result = api.search_release("OK Computer", limit=1)
    
    assert 'releases' in result
    assert len(result['releases']) == 1
    assert result['releases'][0]['title'] == "OK Computer"
    assert mock_urlopen.called


# ==================== LOOKUP TESTS ====================

@patch('src.api.urllib.request.urlopen')
def test_lookup_artist(mock_urlopen):
    """
    Test looking up artist by MBID with tags and genres.
    
    This verifies that the 'inc' parameter works correctly.
    """
    mock_response = create_mock_response(MOCK_ARTIST_LOOKUP)
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    api = MusicBrainzAPI()
    result = api.lookup_artist(
        "a74b1b7f-71a5-4011-9441-d0b5e4122711",
        inc="tags+genres"
    )
    
    assert result['name'] == "Radiohead"
    assert result['country'] == "GB"
    assert 'tags' in result
    assert len(result['tags']) > 0
    assert result['tags'][0]['name'] == "rock"
    assert mock_urlopen.called


@patch('src.api.urllib.request.urlopen')
def test_lookup_release(mock_urlopen):
    """Test looking up release by MBID with labels and tags."""
    mock_response = create_mock_response(MOCK_RELEASE_LOOKUP)
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    api = MusicBrainzAPI()
    result = api.lookup_release(
        "0b6b4ba0-d36f-47bd-b4ea-6a5b91842d29",
        inc="artist-credits+labels+tags"
    )
    
    assert result['title'] == "OK Computer"
    assert result['date'] == "1997-05-21"
    assert result['status'] == "Official"
    assert 'label-info' in result
    assert result['barcode'] == "724385248023"
    assert mock_urlopen.called


@patch('src.api.urllib.request.urlopen')
def test_lookup_release_with_recordings(mock_urlopen):
    """Test looking up release with track information."""
    mock_response = create_mock_response(MOCK_RELEASE_WITH_TRACKS)
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    api = MusicBrainzAPI()
    result = api.lookup_release(
        "0b6b4ba0-d36f-47bd-b4ea-6a5b91842d29",
        inc="recordings+artist-credits"
    )
    
    assert result['title'] == "OK Computer"
    assert 'media' in result
    assert len(result['media']) == 1
    
    # Check tracks
    tracks = result['media'][0]['tracks']
    assert len(tracks) == 3
    assert tracks[0]['title'] == "Airbag"
    assert tracks[0]['length'] == 285000
    assert mock_urlopen.called


# ==================== BROWSE TESTS ====================

@patch('src.api.urllib.request.urlopen')
def test_browse_releases_by_artist(mock_urlopen):
    """Test browsing releases by artist MBID."""
    mock_response = create_mock_response(MOCK_BROWSE_RELEASES)
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    api = MusicBrainzAPI()
    result = api.browse_releases_by_artist(
        "a74b1b7f-71a5-4011-9441-d0b5e4122711",
        limit=25
    )
    
    assert 'releases' in result
    assert len(result['releases']) == 2
    assert result['releases'][0]['title'] == "Pablo Honey"
    assert result['releases'][1]['title'] == "The Bends"
    assert result['release-count'] == 2
    assert mock_urlopen.called


@patch('src.api.urllib.request.urlopen')
def test_browse_releases_with_filters(mock_urlopen):
    """Test browsing releases with type and status filters."""
    mock_response = create_mock_response(MOCK_BROWSE_RELEASES)
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    api = MusicBrainzAPI()
    result = api.browse_releases_by_artist(
        "a74b1b7f-71a5-4011-9441-d0b5e4122711",
        limit=10,
        release_type="album",
        status="official"
    )
    
    assert 'releases' in result
    assert mock_urlopen.called


# ==================== ERROR HANDLING TESTS ====================

@patch('src.api.urllib.request.urlopen')
def test_api_rate_limiting(mock_urlopen):
    """
    Test that rate limiting is enforced.
    
    This verifies that multiple requests are properly spaced out.
    """
    import time
    
    mock_response = create_mock_response(MOCK_ARTIST_SEARCH)
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    api = MusicBrainzAPI()
    
    # Make first request
    start_time = time.time()
    api.search_artist("Artist1")
    
    # Make second request - should be delayed by rate limiting
    api.search_artist("Artist2")
    elapsed = time.time() - start_time
    
    # Should take at least 1 second due to rate limiting
    assert elapsed >= 1.0


@patch('src.api.urllib.request.urlopen')
def test_api_error_handling(mock_urlopen):
    """
    Test that API errors are handled properly.
    
    This simulates a 503 Service Unavailable error.
    """
    from urllib.error import HTTPError
    
    # Make urlopen raise an HTTPError
    mock_urlopen.side_effect = HTTPError(
        url="https://test.com",
        code=503,
        msg="Service Unavailable",
        hdrs={},
        fp=None
    )
    
    api = MusicBrainzAPI()
    
    # Should raise APIError, not HTTPError
    with pytest.raises(APIError) as exc_info:
        api.search_artist("Test")
    
    assert "503" in str(exc_info.value)


@patch('src.api.urllib.request.urlopen')
def test_invalid_json_response(mock_urlopen):
    """Test handling of invalid JSON from API."""
    # Return invalid JSON
    mock_response = MagicMock()
    mock_response.read.return_value = b"NOT JSON DATA"
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    api = MusicBrainzAPI()
    
    # Should raise APIError for invalid JSON
    with pytest.raises(APIError) as exc_info:
        api.search_artist("Test")
    
    assert "JSON" in str(exc_info.value)


# ==================== INTEGRATION-STYLE TESTS ====================

@patch('src.api.urllib.request.urlopen')
def test_search_then_lookup_workflow(mock_urlopen):
    """
    Test a common workflow: search for artist, then lookup details.
    
    This simulates what a real user would do.
    """
    # First call returns search results
    # Second call returns lookup details
    search_response = create_mock_response(MOCK_ARTIST_SEARCH)
    lookup_response = create_mock_response(MOCK_ARTIST_LOOKUP)
    
    mock_urlopen.return_value.__enter__.return_value = search_response
    
    api = MusicBrainzAPI()
    
    # Step 1: Search for artist
    search_result = api.search_artist("Radiohead")
    artist_mbid = search_result['artists'][0]['id']
    
    # Step 2: Lookup artist details
    mock_urlopen.return_value.__enter__.return_value = lookup_response
    artist_details = api.lookup_artist(artist_mbid, inc="tags+genres")
    
    assert artist_details['name'] == "Radiohead"
    assert 'tags' in artist_details
    assert mock_urlopen.call_count >= 2  # Called twice


if __name__ == "__main__":
    # Run tests with: pytest tests/test_api.py -v
    pytest.main([__file__, "-v"])