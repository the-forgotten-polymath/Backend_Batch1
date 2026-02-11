# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser          │  cURL/CLI         │  Python Script       │
│  (Upload Interface)   │  (Command Line)   │  (API Client)        │
└──────────────┬────────┴──────────┬────────┴──────────┬───────────┘
               │                   │                   │
               └───────────────────┼───────────────────┘
                                   │
                         HTTP POST /enrich
                         (multipart/form-data)
                                   │
┌──────────────────────────────────▼───────────────────────────────┐
│                         FLASK API LAYER                          │
├──────────────────────────────────────────────────────────────────┤
│  app.py                                                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1. Validate file (type, size, columns)                    │ │
│  │  2. Save to temporary directory                            │ │
│  │  3. Initialize ProfileEnricher                             │ │
│  │  4. Process file                                            │ │
│  │  5. Generate summary.json                                   │ │
│  │  6. Create ZIP (enriched.xlsx + summary.json)              │ │
│  │  7. Stream ZIP to client                                    │ │
│  │  8. Cleanup temporary files                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────┬───────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────┐
│                    PROCESSING LAYER                              │
├──────────────────────────────────────────────────────────────────┤
│  processor.py (ProfileEnricher)                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Excel Processing:                                          │ │
│  │  • Read Excel with Pandas                                   │ │
│  │  • Validate columns                                         │ │
│  │  • Create column mapping                                    │ │
│  │  • Add new columns                                          │ │
│  │  • Process each row                                         │ │
│  │  • Write enriched Excel + logs sheet                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Rate Limiting:                                             │ │
│  │  • Initialize RateLimiterManager                            │ │
│  │  • Token bucket per platform                                │ │
│  │  • Wait for token before each request                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Statistics Tracking:                                       │ │
│  │  • Success/error counts per platform                        │ │
│  │  • Sample errors collection                                 │ │
│  │  • Processing duration                                      │ │
│  │  • Success rate calculation                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────┬───────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
┌───────────────────▼───┐  ┌───────▼──────┐  ┌───▼──────────────┐
│   SCRAPING LAYER      │  │ RATE LIMITER │  │  VALIDATION      │
├───────────────────────┤  ├──────────────┤  ├──────────────────┤
│ scrapers/             │  │ utils/       │  │ utils/           │
│                       │  │              │  │                  │
│ ┌─────────────────┐   │  │ TokenBucket  │  │ • URL sanitize   │
│ │ LeetCodeScraper │   │  │ • rate       │  │ • URL validate   │
│ │ • Contest rank  │   │  │ • capacity   │  │ • Platform check │
│ └─────────────────┘   │  │ • tokens     │  │ • File validate  │
│                       │  │ • consume()  │  │ • Column map     │
│ ┌─────────────────┐   │  │ • wait()     │  └──────────────────┘
│ │CodeforceScraper │   │  │              │
│ │ • Rating        │   │  │ Manager:     │
│ └─────────────────┘   │  │ • Per-       │
│                       │  │   platform   │
│ ┌─────────────────┐   │  │   limiters   │
│ │ GitHubScraper   │   │  │ • wait_for_  │
│ │ • Commits 12mo  │   │  │   platform() │
│ │ • Public repos  │   │  └──────────────┘
│ └─────────────────┘   │
│                       │
│ ┌─────────────────┐   │
│ │ LinkedInScraper │   │
│ │ • Profile photo │   │
│ │ • Save to disk  │   │
│ └─────────────────┘   │
│                       │
│ All extend:           │
│ ┌─────────────────┐   │
│ │  BaseScraper    │   │
│ │  • fetch_page() │   │
│ │  • parse_html() │   │
│ │  • retry logic  │   │
│ │  • backoff      │   │
│ └─────────────────┘   │
└───────────┬───────────┘
            │
┌───────────▼───────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                           │
├────────────────────────────────────────────────────────────────┤
│  LeetCode.com  │  Codeforces.com  │  LinkedIn.com  │  GitHub  │
│  (HTML)        │  (HTML)          │  (HTML/Image)  │  (HTML)  │
└────────────────────────────────────────────────────────────────┘

## Data Flow

1. **Upload Phase**
   Excel File → Flask → Validation → Temp Storage

2. **Processing Phase**
   For each row:
   ┌─────────────────────────────────────────────────┐
   │ 1. Extract URLs from row                        │
   │ 2. Sanitize and validate URLs                   │
   │ 3. For each platform:                           │
   │    a. Wait for rate limit token                 │
   │    b. Scrape platform (with retries)            │
   │    c. Update row with result                    │
   │    d. Log attempt (success/error)               │
   │    e. Update statistics                         │
   │ 4. Move to next row                             │
   └─────────────────────────────────────────────────┘

3. **Output Phase**
   Enriched Data → Excel Writer → Logs Sheet → Summary JSON → ZIP → Client

## Component Responsibilities

### app.py (Flask API)
- HTTP request handling
- File upload validation
- Response generation
- Temporary file management
- Error handling

### processor.py (ProfileEnricher)
- Excel reading/writing
- Row-by-row processing
- Scraper coordination
- Statistics collection
- Log generation

### scrapers/*.py
- Platform-specific scraping
- HTML parsing
- Data extraction
- Error handling
- Retry logic

### utils/rate_limiter.py
- Token bucket implementation
- Rate limit enforcement
- Thread-safe operations
- Per-platform limits

### utils/validators.py
- URL sanitization
- Platform validation
- File validation
- Column normalization

## Processing Flow Example

```
Input Excel:
┌─────────┬──────────────────────────┬─────────────────────────┐
│ RollNo  │ LeetCodeURL              │ GitHubURL               │
├─────────┼──────────────────────────┼─────────────────────────┤
│ 2021001 │ leetcode.com/user1       │ github.com/user1        │
└─────────┴──────────────────────────┴─────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Validate & Normalize  │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Rate Limit: LeetCode  │
              │ Wait 1.25s            │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Scrape LeetCode       │
              │ Result: Rank 12345    │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Rate Limit: GitHub    │
              │ Wait 1.25s            │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Scrape GitHub         │
              │ Result: 245 commits   │
              └───────────────────────┘
                          │
                          ▼
Output Excel:
┌─────────┬──────────────┬──────────────┬──────────────────┐
│ RollNo  │ LeetCodeURL  │ LC_Rank      │ GH_Commits_12mo  │
├─────────┼──────────────┼──────────────┼──────────────────┤
│ 2021001 │ leetcode...  │ 12345        │ 245              │
└─────────┴──────────────┴──────────────┴──────────────────┘
```

## Error Handling Strategy

```
Request → Scraper
    │
    ├─ Success → Return data
    │
    ├─ HTTP 404 → Return "Profile not found"
    │
    ├─ HTTP 429 → Retry with backoff (max 2 times)
    │
    ├─ Timeout → Retry with backoff (max 2 times)
    │
    └─ Other Error → Log and return "N/A"

All errors are:
• Logged to Enrich_Logs sheet
• Counted in statistics
• Included in summary.json (sample)
• Isolated (don't abort entire job)
```

## Rate Limiting Strategy

```
Token Bucket Algorithm:

┌─────────────────────────────────────┐
│ Bucket (capacity = rate × 2)        │
│ ┌─────┬─────┬─────┬─────┬─────┐    │
│ │  T  │  T  │  T  │  T  │     │    │
│ └─────┴─────┴─────┴─────┴─────┘    │
│                                     │
│ Refill rate: 0.8 tokens/second     │
│ (LeetCode example)                  │
└─────────────────────────────────────┘

Request arrives:
1. Check if token available
2. If yes: consume token, proceed
3. If no: wait 100ms, retry
4. Tokens refill continuously

Result: Smooth, distributed requests
```

## Security Layers

```
1. File Upload
   ├─ MIME type check (.xlsx only)
   ├─ File size limit (10MB)
   └─ Extension validation

2. URL Processing
   ├─ Sanitization (remove malicious chars)
   ├─ Platform validation (correct domain)
   └─ Scheme enforcement (https://)

3. Processing
   ├─ Temporary file isolation
   ├─ No credential storage
   └─ Automatic cleanup

4. Response
   ├─ ZIP packaging
   └─ Secure file streaming
```
