# Project Name: MusicBrainz CLI

## Overview
A command-line tool for exploring music metadata using the MusicBrainz API. Users can search for artists, browse discographies, view album details, and explore tracklists—all from the terminal. Perfect for music enthusiasts who want quick access to comprehensive music data.

## API Integration
- **API:** MusicBrainz API v2
- **Base URL:** https://musicbrainz.org/ws/2/
- **Documentation:** https://musicbrainz.org/doc/MusicBrainz_API
- **Key endpoints:**
  - `/artist?query=<QUERY>` - Search for artists
  - `/artist/<MBID>?inc=<INCLUDES>` - Get artist details
  - `/release?artist=<MBID>` - Browse artist releases
  - `/release/<MBID>?inc=recordings+artist-credits` - Get album with tracks
- **Data format:** JSON (use `fmt=json` parameter)
- **Authentication:** None required for read operations
- **Rate limit:** 1 request per second (strictly enforced)
- **Required header:** User-Agent: `AppName/Version (contact-info)`

### Core Entities
- **MBID** - MusicBrainz Identifier (UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
- **Artist** - Musicians, bands, composers
- **Release** - Albums, singles, EPs (the actual product)
- **Recording** - Individual song recordings
- **Label** - Record labels

### Important Include Parameters
- `tags+genres` - User tags and official genres
- `recordings+artist-credits` - Track listings with artists
- `releases` - Shows releases an entity appears on
- `labels` - Label information for releases
- `aliases` - Alternative names for entities

## CLI Commands

### Core Commands (4 total)
1. `artist-info <name_or_mbid>` - Display detailed artist information
   - Shows: Name, MBID, Type, Country, Active period, Tags, Genres
   - Example: `python -m src.main artist-info "Radiohead"`

2. `artist-releases <name_or_mbid> [--limit N] [--type TYPE] [--status STATUS]` - List artist's releases
   - Shows: Release title, date, status, MBID
   - Filters: `--type` (album, single, ep), `--status` (official, bootleg)
   - Example: `python -m src.main artist-releases "Miles Davis" --limit 20 --type album`

3. `album-info <name_or_mbid> [--artist NAME]` - Display album details
   - Shows: Title, Artist, Date, Status, Country, Labels, Barcode, Tags
   - Example: `python -m src.main album-info "OK Computer" --artist "Radiohead"`

4. `album-tracks <name_or_mbid> [--artist NAME]` - Show album tracklist
   - Shows: Track number, title, duration for all tracks
   - Supports multi-disc releases
   - Example: `python -m src.main album-tracks "Abbey Road" --artist "The Beatles"`

## Technical Stack
- Python 3.8+
- argparse for CLI argument parsing (stdlib)
- urllib for HTTP requests (stdlib - no external HTTP library)
- json for response parsing (stdlib)
- pytest for testing with mocking
- unittest.mock for test mocking (stdlib)

## Code Organization

```
MusicBrainz-cli/
├── src/
│   ├── __init__.py
│   ├── main.py           # ALL CLI commands, argparse setup, helper functions
│   └── api.py            # ALL API functionality (client + endpoints combined)
├── tests/
│   ├── __init__.py
│   ├── test_main.py      # Tests for CLI commands and helpers
│   └── test_api.py       # Tests for API methods
├── .github/
│   └── workflows/
│       └── tests.yml     # CI/CD configuration
├── AGENTS.md             # This file
├── README.md             # Professional documentation
└── requirements.txt      # Python dependencies (just pytest)
```

### Architecture (Simplified - 2 Files)

#### `src/api.py` - Complete API Layer
Contains the `MusicBrainzAPI` class with:
- **Rate limiting** - Enforces 1 request/second
- **HTTP client** - Uses urllib for requests
- **Search methods** - `search_artist()`, `search_release()`
- **Lookup methods** - `lookup_artist()`, `lookup_release()`
- **Browse methods** - `browse_releases_by_artist()`
- **Error handling** - Custom `APIError` exception

#### `src/main.py` - Complete CLI Layer
Contains everything CLI-related:
- **Helper functions:**
  - `is_valid_mbid()` - Validates MBID format
  - `resolve_artist_mbid()` - Converts name to MBID
  - `resolve_release_mbid()` - Converts album name to MBID
  - `format_duration()` - Converts ms to MM:SS
  - `format_list()` - Formats tag lists
  
- **Command functions:**
  - `cmd_artist_info()` - Artist information command
  - `cmd_artist_releases()` - Artist releases command
  - `cmd_album_info()` - Album information command
  - `cmd_album_tracks()` - Album tracklist command
  
- **CLI setup:**
  - `create_parser()` - Builds argparse structure
  - `main()` - Entry point, routes to commands

### Key Design Patterns

**MBID Resolution:** Commands accept either names or MBIDs
```python
def resolve_artist_mbid(api, query):
    if is_valid_mbid(query):
        return query  # Already valid, use it
    # Otherwise search and return first result's MBID
    results = api.search_artist(query, limit=1)
    return results['artists'][0]['id']
```

**Rate Limiting:** Enforced at API client level
```python
def _rate_limit(self):
    elapsed = time.time() - self._last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    self._last_request_time = time.time()
```

**Error Handling:** Custom exceptions with user-friendly messages
```python
try:
    mbid = resolve_artist_mbid(api, args.query)
    data = api.lookup_artist(mbid, inc='tags+genres')
except ValueError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

## Standards
- Follow PEP 8 style guidelines
- Use docstrings (Google style) for all functions and classes
- Type hints for function signatures
- Handle missing API fields with `.get()` and defaults
- All API calls go through rate-limited client
- Mock all API calls in tests (no real requests during testing)
- Graceful error handling with try/except blocks
- User-friendly error messages (no stack traces shown to users)

## Critical Requirements

### 1. Rate Limiting (CRITICAL)
- **Must wait 1 second between API requests** - violation may cause IP ban
- Implemented in `MusicBrainzAPI._rate_limit()` method
- Tracks last request time and sleeps if needed
- Applied to every API call automatically

### 2. User-Agent Header (REQUIRED)
- Required on every HTTP request
- Format: `AppName/Version (contact-info)`
- Set in `src/api.py`: `USER_AGENT = "MusicBrainzCLI/1.0.0 (educational-project)"`

### 3. MBID Handling
- Lookups require MBID (UUID format)
- Implement name-to-MBID resolution in helper functions
- Validate MBID format using regex pattern
- Accept both names and MBIDs in all commands

### 4. Error Handling
- Handle 404 (not found), 503 (server busy), network errors
- Use try/except in all command functions
- Exit with code 1 for user errors, code 2 for API errors
- Display helpful error messages to users

### 5. Missing Data
- API responses may have missing fields
- Always use `.get()` with defaults: `artist.get('country', 'Unknown')`
- Never assume a field exists
- Handle empty lists and None values gracefully

## Testing Strategy

### Test Files
- **`tests/test_api.py`** - Tests all API methods with mocked HTTP responses
- **`tests/test_main.py`** - Tests CLI commands and helper functions

### Mocking Approach
All tests use mocking - NO real API calls are made during testing:

```python
@patch('src.api.urllib.request.urlopen')
def test_search_artist(mock_urlopen):
    # Create fake response
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"artists": [...]}'
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    # Test uses fake data
    api = MusicBrainzAPI()
    result = api.search_artist("Radiohead")
    assert result['artists'][0]['name'] == "Radiohead"
```

### Test Coverage
- Helper functions (MBID validation, formatting)
- API methods (search, lookup, browse)
- CLI commands (with various arguments)
- Error handling (not found, API errors)
- Rate limiting enforcement
- Integration tests (full command flow)

### Running Tests
```bash
pytest tests/ -v                    # Run all tests
pytest tests/test_api.py -v         # Run API tests only
pytest tests/test_main.py -v        # Run CLI tests only
pytest tests/ --cov=src             # Run with coverage
```

## Example MBIDs for Testing
- Radiohead (artist): `a74b1b7f-71a5-4011-9441-d0b5e4122711`
- OK Computer (release): `0b6b4ba0-d36f-47bd-b4ea-6a5b91842d29`
- The Beatles (artist): `b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d`
- Abbey Road (release): `aaa1d403-2c6b-4e90-bbbc-c4b0d58a6c43`

## CI/CD Pipeline

### GitHub Actions Workflow
- **File:** `.github/workflows/tests.yml`
- **Triggers:** Push to main/master, pull requests
- **Python versions:** 3.8, 3.9, 3.10, 3.11
- **Steps:**
  1. Checkout code
  2. Set up Python
  3. Install dependencies
  4. Run pytest tests
  5. Optional: Run coverage report

### Badge in README
```markdown
![Tests](https://github.com/username/repo-name/workflows/Tests/badge.svg)
```

## Development Workflow

### Adding a New Command
1. Add command function in `src/main.py` (e.g., `cmd_new_feature()`)
2. Add argparse subparser in `create_parser()`
3. Wire up function: `parser.set_defaults(func=cmd_new_feature)`
4. Add tests in `tests/test_main.py`
5. Update README with usage examples

### Adding a New API Method
1. Add method to `MusicBrainzAPI` class in `src/api.py`
2. Use `self._make_request()` for HTTP calls
3. Add docstring with args, returns, example
4. Add tests in `tests/test_api.py` with mocked responses
5. Update any commands that need the new method

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'src'"
**Solution:** Run from project root using `python -m src.main`, not `python src/main.py`

### Issue: Tests fail with "AttributeError" on mocks
**Solution:** Ensure mocking the correct import path: `@patch('src.api.urllib.request.urlopen')`

### Issue: "Artist not found" errors
**Solution:** Check spelling, some artists have disambiguation info

### Issue: Rate limit errors (503)
**Solution:** Rate limiting is automatic, but server may be busy - retry later

## Resources
- [MusicBrainz API Docs](https://musicbrainz.org/doc/MusicBrainz_API)
- [Python argparse tutorial](https://docs.python.org/3/howto/argparse.html)
- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock guide](https://docs.python.org/3/library/unittest.mock.html)

---

**Last Updated:** Project completion
**Version:** 1.0.0
**Test Status:** 41 tests passing