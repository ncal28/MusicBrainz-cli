# MusicBrainz CLI

![Tests](https://github.com/ncal28/MusicBrainz-cli/workflows/Tests/badge.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A command-line interface for exploring music metadata using the MusicBrainz API. Search for artists, browse discographies, view album details, and explore tracklists—all from your terminal.

## Features

- 🎵 **Artist Information** - Get detailed artist data including country, active period, genres, and tags
- 💿 **Artist Discography** - Browse all releases by an artist with optional filtering by type and status
- 📀 **Album Details** - View comprehensive album information including labels, release date, and tags
- 🎼 **Track Listings** - Display complete tracklists with track numbers, titles, and durations
- 🔍 **Smart Search** - Search by artist/album name or use MusicBrainz IDs (MBIDs) directly
- ⚡ **Rate Limited** - Respects MusicBrainz API rate limits (1 request/second)
- ✅ **Well Tested** - Comprehensive test suite with 41 passing tests

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ncal28/MusicBrainz-cli.git
   cd MusicBrainz-cli
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python -m src.main --help
   ```

## Usage

### Basic Commands

#### Artist Information
Get detailed information about an artist:
```bash
python -m src.main artist-info "Radiohead"
```

**Output:**
```
============================================================
Radiohead
============================================================

MBID:    a74b1b7f-71a5-4011-9441-d0b5e4122711
Type:    Group
Country: GB
Active:  1985 - present

Tags:    rock, alternative rock, electronic, experimental, art rock
Genres:  alternative rock, art rock, electronic
```

#### Artist Releases
List all releases by an artist:
```bash
python -m src.main artist-releases "Miles Davis" --limit 20 --type album --status official
```

**Options:**
- `--limit N` - Maximum number of results (default: 25, max: 100)
- `--type` - Filter by type: `album`, `single`, `ep`, `broadcast`, `other`
- `--status` - Filter by status: `official`, `promotion`, `bootleg`, `pseudo-release`

**Output:**
```
============================================================
Releases by Miles Davis
============================================================
Showing 20 of 150 total releases

  1. Kind of Blue
      1959-08-17 | Official
      MBID: abc123...

  2. Bitches Brew
      1970-03-30 | Official
      MBID: def456...
```

#### Album Information
Get detailed information about an album:
```bash
python -m src.main album-info "OK Computer" --artist "Radiohead"
```

**Output:**
```
============================================================
OK Computer
============================================================

MBID:   0b6b4ba0-d36f-47bd-b4ea-6a5b91842d29
Artist: Radiohead
Date:   1997-05-21
Status: Official
Country: GB
Labels: Parlophone, Capitol Records

Tags: alternative rock, electronic, art rock
```

#### Album Tracklist
Display the tracklist for an album:
```bash
python -m src.main album-tracks "Abbey Road" --artist "The Beatles"
```

**Output:**
```
============================================================
Abbey Road
by The Beatles
============================================================

CD 1 (17 tracks):

   1. Come Together (4:20)
   2. Something (3:03)
   3. Maxwell's Silver Hammer (3:27)
   ...
```

### Advanced Usage

#### Using MBIDs Directly
If you know the MusicBrainz ID (MBID), you can use it directly:
```bash
python -m src.main artist-info "a74b1b7f-71a5-4011-9441-d0b5e4122711"
```

#### Filtering Releases
Get only official studio albums:
```bash
python -m src.main artist-releases "Radiohead" --type album --status official --limit 50
```

#### Narrow Album Search
When searching for albums with common names, specify the artist:
```bash
python -m src.main album-info "Rubber Soul" --artist "The Beatles"
```

## Command Reference

| Command | Description | Required Args | Optional Args |
|---------|-------------|---------------|---------------|
| `artist-info` | Display artist details | `<query>` | None |
| `artist-releases` | List artist's releases | `<query>` | `--limit`, `--type`, `--status` |
| `album-info` | Display album details | `<query>` | `--artist` |
| `album-tracks` | Show album tracklist | `<query>` | `--artist` |

**Note:** `<query>` can be either a name (e.g., "Radiohead") or an MBID (e.g., "a74b1b7f-71a5-4011-9441-d0b5e4122711")

## API Information

This project uses the [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API), a comprehensive open-source music encyclopedia.

**API Features:**
- No authentication required
- Rate limit: 1 request per second (automatically enforced by this CLI)
- Data format: JSON
- License: Public Domain (CC0) for data

**MusicBrainz Resources:**
- [API Documentation](https://musicbrainz.org/doc/MusicBrainz_API)
- [MusicBrainz Database](https://musicbrainz.org/)
- [Entity Types](https://musicbrainz.org/doc/MusicBrainz_Entity)

## Development

### Project Structure
```
MusicBrainz-cli/
├── src/
│   ├── __init__.py
│   ├── main.py           # CLI commands and argparse setup
│   └── api.py            # MusicBrainz API client
├── tests/
│   ├── __init__.py
│   ├── test_main.py      # CLI command tests
│   └── test_api.py       # API client tests
├── .github/
│   └── workflows/
│       └── tests.yml     # CI/CD configuration
├── AGENTS.md             # AI assistant context
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

### Running Tests

**Run all tests:**
```bash
pytest tests/ -v
```

**Run specific test file:**
```bash
pytest tests/test_api.py -v
pytest tests/test_main.py -v
```

**Run with coverage:**
```bash
pytest tests/ --cov=src --cov-report=html
```

**Test output:**
```
tests/test_api.py::test_search_artist PASSED
tests/test_api.py::test_lookup_artist PASSED
tests/test_main.py::test_cmd_artist_info PASSED
...
==================== 41 passed in 2.5s ====================
```

### Technologies Used

- **Python 3.8+** - Core language
- **argparse** - Command-line argument parsing (stdlib)
- **urllib** - HTTP requests (stdlib, no external dependencies)
- **json** - JSON parsing (stdlib)
- **pytest** - Testing framework
- **unittest.mock** - Mocking for tests (stdlib)

### Code Quality

- **PEP 8** compliant code style
- **Docstrings** on all functions and classes
- **Type hints** for function signatures
- **Comprehensive tests** with 41 test cases
- **100% mocked tests** - No real API calls during testing

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** and add tests
4. **Run tests** to ensure everything passes (`pytest tests/`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to your branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'src'"**
- Make sure you're running from the project root directory
- Use `python -m src.main` not `python src/main.py`
- Ensure `src/__init__.py` exists

**"Artist not found" errors**
- Check spelling of artist/album names
- Try using the MBID directly if you have it
- Some artists have disambiguation (e.g., "Mercury Rev" vs "Mercury")

**Rate limiting issues**
- The CLI automatically enforces the 1 request/second limit
- If you see 503 errors, the MusicBrainz API may be temporarily unavailable

**Tests failing**
- Ensure pytest is installed: `pip install pytest`
- Make sure you're using Python 3.8+
- Check that all dependencies are installed: `pip install -r requirements.txt`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **MusicBrainz** - For providing the comprehensive music metadata API
- **MusicBrainz Contributors** - For maintaining the world's largest open music encyclopedia
- **pytest** - For the excellent testing framework

## Related Projects

- [MusicBrainz Picard](https://picard.musicbrainz.org/) - Official music tagger
- [python-musicbrainzngs](https://python-musicbrainzngs.readthedocs.io/) - Python library for MusicBrainz
- [ListenBrainz](https://listenbrainz.org/) - Open music listening data platform

## Author

**Nolan Callahan**
- GitHub: [@ncal28](https://github.com/ncal28)
- Project: [MusicBrainz CLI](https://github.com/ncal28/MusicBrainz-cli)

---

**Note:** This project was developed as part of an AI-assisted development course, demonstrating modern software development practices including API integration, testing, CI/CD, and professional documentation.