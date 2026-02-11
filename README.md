# Placement Profile Enricher API

A Flask-based API that automatically enriches Excel spreadsheets with candidate profile data from LeetCode, Codeforces, LinkedIn, and GitHub.

## Features

- 🚀 **Automated Profile Scraping**: Extract contest ranks, ratings, commits, and profile photos
- ⚡ **Rate-Limited Processing**: Token bucket algorithm prevents API blocking
- 📊 **Excel Integration**: Preserves original data and adds enriched columns
- 📸 **Photo Management**: Downloads and saves LinkedIn profile photos
- 📝 **Detailed Logging**: Per-row, per-platform logs with success/error tracking
- 📦 **ZIP Response**: Returns enriched Excel + JSON summary in one download

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your preferred settings (optional)
```

### 3. Run the API

```bash
python app.py
```

The API will start on `http://localhost:5000`

## API Usage

### POST /enrich

Upload an Excel file for enrichment.

**Request:**
```bash
curl -X POST http://localhost:5000/enrich \
  -F "excel=@candidates.xlsx" \
  -o enriched_profiles.zip
```

**Expected Excel Columns** (case-insensitive):
- `RollNo` - Student roll number (optional, can be derived from URLs)
- `LeetCodeURL` - LeetCode profile URL
- `CodeforcesURL` - Codeforces profile URL
- `LinkedInURL` - LinkedIn profile URL
- `GitHubURL` - GitHub profile URL

**Response:**
- ZIP file containing:
  - `enriched.xlsx` - Original data + new columns + logs sheet
  - `summary.json` - Processing statistics and errors

**New Columns Added:**
- `LC_Global_Contest_Rank` - LeetCode global contest ranking
- `CF_Rating` - Codeforces current rating
- `Photos_Path` - Relative path to saved LinkedIn photo
- `GH_Commits_12mo` - GitHub commits in last 12 months
- `GH_Public_Repos` - GitHub public repository count

### GET /health

Health check endpoint.

```bash
curl http://localhost:5000/health
```

## Configuration

Edit `.env` file to customize:

### Rate Limits (requests per second)
```env
LEETCODE_RATE_LIMIT=0.8
CODEFORCES_RATE_LIMIT=1.0
LINKEDIN_RATE_LIMIT=0.5
GITHUB_RATE_LIMIT=0.8
```

### Request Settings
```env
REQUEST_TIMEOUT=15
MAX_RETRIES=2
RETRY_BACKOFF_FACTOR=2
```

### File Upload
```env
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=xlsx
```

### Selenium (for LinkedIn photos)
```env
SELENIUM_ENABLED=false
SELENIUM_HEADLESS=true
```

## Example Excel Format

| RollNo | LeetCodeURL | CodeforcesURL | LinkedInURL | GitHubURL |
|--------|-------------|---------------|-------------|-----------|
| 2021001 | https://leetcode.com/user1 | https://codeforces.com/profile/user1 | https://linkedin.com/in/user1 | https://github.com/user1 |
| 2021002 | https://leetcode.com/user2 | https://codeforces.com/profile/user2 | https://linkedin.com/in/user2 | https://github.com/user2 |

## Output Structure

```
enriched_profiles.zip
├── enriched.xlsx
│   ├── Enriched_Data (sheet)
│   │   └── Original columns + new enriched columns
│   └── Enrich_Logs (sheet)
│       └── timestamp, row_id, platform, url, status, message
└── summary.json
    └── Platform-wise success rates and sample errors
```

## Summary JSON Format

```json
{
  "total_rows": 150,
  "total_duration_ms": 185000,
  "platforms": {
    "leetcode": {
      "success_count": 142,
      "error_count": 8,
      "success_rate": 94.67,
      "sample_errors": [
        {"row": 5, "url": "...", "error": "Profile not found"}
      ]
    },
    "codeforces": { ... },
    "github": { ... },
    "linkedin": { ... }
  }
}
```

## Project Structure

```
placement-profile-enricher/
├── app.py                 # Flask API
├── config.py              # Configuration
├── processor.py           # Excel processing logic
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py   # Base scraper with retry logic
│   ├── leetcode_scraper.py
│   ├── codeforces_scraper.py
│   ├── github_scraper.py
│   └── linkedin_scraper.py
├── utils/
│   ├── __init__.py
│   ├── rate_limiter.py   # Token bucket rate limiter
│   └── validators.py     # URL and file validation
├── photos/               # Saved LinkedIn photos
├── uploads/              # Temporary uploads
└── output/               # Temporary outputs
```

## Performance

- **Processing Speed**: ~1 second per platform per row (configurable)
- **Memory Usage**: <300MB for files up to 10MB
- **Capacity**: Handles up to 150 rows efficiently
- **Retry Logic**: 2 retries with exponential backoff per request

## Error Handling

- **Isolated Failures**: One row/platform failure doesn't abort the job
- **Detailed Logging**: Every attempt logged with timestamp and error message
- **Graceful Degradation**: Missing data marked as "N/A"
- **Rate Limit Protection**: Token bucket prevents bursts

## Testing

Create a sample Excel file and test:

```bash
# Test with sample file
curl -X POST http://localhost:5000/enrich \
  -F "excel=@test_candidates.xlsx" \
  -o result.zip

# Extract and review
unzip result.zip
```

## Troubleshooting

### LinkedIn Photos Not Working
- LinkedIn requires authentication for most profiles
- Enable Selenium: Set `SELENIUM_ENABLED=true` in `.env`
- Note: Selenium is slower and may still fail for private profiles

### Rate Limiting Issues
- Reduce rate limits in `.env`
- Increase `DEFAULT_DELAY_MS`
- Process smaller batches

### Memory Issues
- Reduce `MAX_FILE_SIZE_MB`
- Process files in smaller chunks
- Increase system memory

## Security Notes

- File size limits enforced (default 10MB)
- URL validation and sanitization
- No credentials required or stored
- Temporary files cleaned up after processing
- Respects website terms of service

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please open an issue on GitHub.
