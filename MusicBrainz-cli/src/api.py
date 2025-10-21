"""
src/api.py

MusicBrainz API integration - handles all API communication.
Combines rate-limited HTTP client with high-level endpoint methods.
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional

# API Configuration
API_BASE = "https://musicbrainz.org/ws/2"
USER_AGENT = "MusicBrainzCLI/1.0.0 (educational-project)"
RATE_LIMIT = 1.0  # Must wait 1 second between requests
REQUEST_TIMEOUT = 30


class MusicBrainzAPI:
    """
    MusicBrainz API client with rate limiting and high-level methods.
    
    Provides methods for searching, looking up, and browsing MusicBrainz entities.
    Enforces 1 request per second rate limit to comply with API requirements.
    """
    
    def __init__(self):
        """Initialize API client with rate limiting."""
        self._last_request_time = 0
    
    # ==================== LOW-LEVEL HTTP METHODS ====================
    
    def _rate_limit(self) -> None:
        """
        Enforce 1 second minimum between API requests.
        
        This is critical - MusicBrainz will ban IPs that exceed rate limits.
        """
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT:
            time.sleep(RATE_LIMIT - elapsed)
        self._last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an HTTP request to the MusicBrainz API.
        
        Args:
            endpoint: API endpoint (e.g., 'artist', 'release', 'artist/MBID')
            params: Query parameters as dictionary
        
        Returns:
            Parsed JSON response as dictionary
        
        Raises:
            APIError: For HTTP errors or network issues
        """
        # Enforce rate limiting
        self._rate_limit()
        
        # Always request JSON format
        params['fmt'] = 'json'
        
        # Build URL
        query_string = urllib.parse.urlencode(params)
        url = f"{API_BASE}/{endpoint}?{query_string}"
        
        # Create request with required headers
        req = urllib.request.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Accept', 'application/json')
        
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {'error': 'not_found', 'message': 'Entity not found'}
            elif e.code == 503:
                raise APIError("MusicBrainz service unavailable (503). Try again later.")
            elif e.code == 400:
                raise APIError("Bad request (400). Check your query parameters.")
            else:
                raise APIError(f"HTTP {e.code}: {e.reason}")
        
        except urllib.error.URLError as e:
            raise APIError(f"Network error: {e.reason}")
        
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response: {e}")
        
        except Exception as e:
            raise APIError(f"Unexpected error: {str(e)}")
    
    # ==================== SEARCH METHODS ====================
    
    def search_artist(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for artists by name or query.
        
        Args:
            query: Artist name or search query
            limit: Maximum results (default: 10, max: 100)
        
        Returns:
            Dictionary with 'artists' key containing results
        
        Example:
            >>> api.search_artist("Radiohead")
            {'artists': [{'id': '...', 'name': 'Radiohead', ...}]}
        """
        return self._make_request('artist', {
            'query': query,
            'limit': min(limit, 100)
        })
    
    def search_release(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for releases (albums) by name or query.
        
        Args:
            query: Release name or search query
            limit: Maximum results (default: 10, max: 100)
        
        Returns:
            Dictionary with 'releases' key containing results
        """
        return self._make_request('release', {
            'query': query,
            'limit': min(limit, 100)
        })
    
    def search_recording(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for recordings (songs) by name or query.
        
        Args:
            query: Recording name or search query
            limit: Maximum results (default: 10, max: 100)
        
        Returns:
            Dictionary with 'recordings' key containing results
        """
        return self._make_request('recording', {
            'query': query,
            'limit': min(limit, 100)
        })
    
    def search_label(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for record labels by name or query.
        
        Args:
            query: Label name or search query
            limit: Maximum results (default: 10, max: 100)
        
        Returns:
            Dictionary with 'labels' key containing results
        """
        return self._make_request('label', {
            'query': query,
            'limit': min(limit, 100)
        })
    
    def search_by_tag(self, entity_type: str, tag: str, limit: int = 25) -> Dict[str, Any]:
        """
        Search for entities by tag/genre.
        
        Args:
            entity_type: 'artist' or 'release'
            tag: Tag name (e.g., 'jazz', 'electronic')
            limit: Maximum results (default: 25)
        
        Returns:
            Dictionary with entity results
        """
        return self._make_request(entity_type, {
            'query': f'tag:{tag}',
            'limit': min(limit, 100)
        })
    
    # ==================== LOOKUP METHODS ====================
    
    def lookup_artist(self, mbid: str, inc: Optional[str] = None) -> Dict[str, Any]:
        """
        Look up artist by MBID.
        
        Args:
            mbid: MusicBrainz Identifier (UUID)
            inc: Optional includes (e.g., 'tags+genres+aliases')
        
        Returns:
            Dictionary with artist details
        """
        params = {}
        if inc:
            params['inc'] = inc
        return self._make_request(f'artist/{mbid}', params)
    
    def lookup_release(self, mbid: str, inc: Optional[str] = None) -> Dict[str, Any]:
        """
        Look up release by MBID.
        
        Args:
            mbid: MusicBrainz Identifier (UUID)
            inc: Optional includes (e.g., 'recordings+artist-credits+labels')
        
        Returns:
            Dictionary with release details
        """
        params = {}
        if inc:
            params['inc'] = inc
        return self._make_request(f'release/{mbid}', params)
    
    def lookup_recording(self, mbid: str, inc: Optional[str] = None) -> Dict[str, Any]:
        """
        Look up recording by MBID.
        
        Args:
            mbid: MusicBrainz Identifier (UUID)
            inc: Optional includes (e.g., 'artists+releases+isrcs')
        
        Returns:
            Dictionary with recording details
        """
        params = {}
        if inc:
            params['inc'] = inc
        return self._make_request(f'recording/{mbid}', params)
    
    def lookup_label(self, mbid: str, inc: Optional[str] = None) -> Dict[str, Any]:
        """
        Look up label by MBID.
        
        Args:
            mbid: MusicBrainz Identifier (UUID)
            inc: Optional includes
        
        Returns:
            Dictionary with label details
        """
        params = {}
        if inc:
            params['inc'] = inc
        return self._make_request(f'label/{mbid}', params)
    
    # ==================== BROWSE METHODS ====================
    
    def browse_releases_by_artist(
        self, 
        artist_mbid: str, 
        limit: int = 25,
        release_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Browse all releases by a specific artist.
        
        Args:
            artist_mbid: Artist's MBID
            limit: Maximum results (default: 25, max: 100)
            release_type: Filter by type ('album', 'single', 'ep', etc.)
            status: Filter by status ('official', 'bootleg', etc.)
        
        Returns:
            Dictionary with 'releases' key containing release list
        """
        params = {
            'artist': artist_mbid,
            'limit': min(limit, 100)
        }
        
        if release_type:
            params['type'] = release_type
        if status:
            params['status'] = status
        
        return self._make_request('release', params)
    
    def browse_releases_by_label(
        self,
        label_mbid: str,
        limit: int = 25,
        release_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Browse all releases by a specific label.
        
        Args:
            label_mbid: Label's MBID
            limit: Maximum results (default: 25, max: 100)
            release_type: Filter by type ('album', 'single', 'ep', etc.)
        
        Returns:
            Dictionary with 'releases' key containing release list
        """
        params = {
            'label': label_mbid,
            'limit': min(limit, 100)
        }
        
        if release_type:
            params['type'] = release_type
        
        return self._make_request('release', params)


class APIError(Exception):
    """Exception raised for API communication errors."""
    pass


# Example usage and testing
if __name__ == "__main__":
    """Test the API with real requests."""
    print("Testing MusicBrainz API...\n")
    
    api = MusicBrainzAPI()
    
    # Test 1: Search for artist
    print("Test 1: Searching for 'Radiohead'...")
    result = api.search_artist('Radiohead', limit=1)
    if result.get('artists'):
        artist = result['artists'][0]
        print(f"✓ Found: {artist['name']} (MBID: {artist['id']})\n")
    
    # Test 2: Lookup artist with details
    print("Test 2: Looking up Radiohead details...")
    artist_mbid = 'a74b1b7f-71a5-4011-9441-d0b5e4122711'
    result = api.lookup_artist(artist_mbid, inc='tags+genres')
    print(f"✓ Artist: {result['name']}")
    print(f"  Country: {result.get('country', 'Unknown')}")
    tags = result.get('tags', [])[:3]
    if tags:
        print(f"  Tags: {', '.join([t['name'] for t in tags])}\n")
    
    # Test 3: Browse releases
    print("Test 3: Browsing Radiohead releases...")
    result = api.browse_releases_by_artist(artist_mbid, limit=5, release_type='album')
    if result.get('releases'):
        print(f"✓ Found {len(result['releases'])} albums:")
        for release in result['releases'][:3]:
            print(f"  - {release['title']} ({release.get('date', 'Unknown')})")
    
    print("\nAPI tests complete!")