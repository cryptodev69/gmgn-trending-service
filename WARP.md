# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

### Setup & Installation
- **Virtual Environment**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Install Dependencies**:
  ```bash
  pip install -r requirements.txt
  ```

### Development Server
Run the FastAPI server locally with hot reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Docker
- **Build & Run**:
  ```bash
  docker-compose up --build
  ```
  The service will be available at `http://localhost:8000`.
- **Database Note**: This project currently does not define a database service in `docker-compose.yml`. If a PostgreSQL database is added, ensure it uses version **14** per user preference (e.g., `image: postgres:14`).

### Testing
Run tests using `pytest`:
- **All Tests**:
  ```bash
  python -m pytest
  ```
- **Single File**:
  ```bash
  python -m pytest tests/test_main.py
  ```

### Linting & Formatting
(Standard Python tools assumed; configure if missing)
- **Lint**: `flake8 .` or `ruff check .`
- **Format**: `black .` or `ruff format .`

### Analysis Script
The repository contains a standalone analysis script `analyzer.py` that fetches trending token data, generates a CSV report, and a plot.
**Note**: This script imports `gmgn` directly. Ensure `app/services/gmgn_package` is in your `PYTHONPATH` or accessible.
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/app/services/gmgn_package
python analyzer.py
```
- **Outputs**: `trending_analysis.csv`, `trending_analysis_plot.png`

## Architecture

### Backend (FastAPI)
- **Entrypoint**: `app/main.py` initializes the `FastAPI` app and CORS settings.
- **Configuration**: `app/core/config.py` uses `pydantic-settings` to load environment variables (e.g., `.env`).
- **Routing**: `app/api/v1/api.py` aggregates routers for `market`, `tokens`, `wallets`, `chain`, and `analysis`.
- **Structure**:
  - `app/api/v1/endpoints/`: request handlers.
  - `app/models/`: Pydantic data models.
  - `app/services/`: external integrations.

### GMGN Integration
The core logic scrapes [gmgn.ai](https://gmgn.ai) using `tls_client` to mimic real browser TLS fingerprints (Chrome/Safari/Firefox) and evade bot detection.
- **Main Service**: `app/services/gmgn.py` defines `GMGNClient`. It wraps synchronous requests in a `ThreadPoolExecutor` to provide an `async` API for FastAPI.
- **Multi-Chain Support**: All client methods accept a `chain` parameter (defaults to `"sol"`) to support multiple blockchains:
  - `sol` - Solana
  - `eth` - Ethereum
  - `base` - Base
  - `bsc` - Binance Smart Chain
  - And potentially others supported by GMGN.ai
- **Package**: `app/services/gmgn_package/client.py` contains a synchronous `gmgn` class (legacy or lower-level) used by the analysis script.

### Analysis Service
- **Module**: `app/services/analysis_service.py`
- **Purpose**: Aggregates trending token data across multiple timeframes to identify consistent performers.
- **Flow**:
  1. Fetches trending tokens for 5 timeframes (1m, 5m, 1h, 6h, 24h) concurrently.
  2. Aggregates data using pandas to find tokens appearing in multiple timeframes.
  3. Filters by volume, market cap, and consistency thresholds.
  4. Returns JSON-serializable data for API consumption.
- **API Endpoint**: `GET /api/v1/analysis/trending?chain=sol&min_consistency=3&volume_threshold=1000&market_cap_threshold=10000`

### Standalone Analysis
- **Script**: `analyzer.py`
- **Flow**:
  1. Fetches trending tokens for multiple timeframes (1m, 5m, 1h, 6h, 24h).
  2. Aggregates data to find "consistent" tokens (appearing in multiple timeframes).
  3. Filters by volume and market cap.
  4. Generates `trending_analysis.csv` and a Matplotlib visualization `trending_analysis_plot.png`.

## Caching

The service implements a 60-second TTL cache for trending token data to:
- Reduce load on GMGN.ai API
- Prevent rate limiting
- Improve response times

Caching is automatically applied to the `/analysis/trending` endpoint. Repeated requests within 60 seconds will return cached data.

## Multi-Chain Usage Examples

All API endpoints now support a `chain` query parameter:

```bash
# Solana (default)
curl http://localhost:8000/api/v1/analysis/trending

# Ethereum
curl http://localhost:8000/api/v1/analysis/trending?chain=eth

# Base
curl http://localhost:8000/api/v1/analysis/trending?chain=base

# BSC
curl http://localhost:8000/api/v1/analysis/trending?chain=bsc
```

### Deep Analysis Endpoint

The `/analysis/deep/{chain}/{address}` endpoint performs comprehensive token analysis by aggregating:
- Market data (price, volume, liquidity, holder count)
- Security information (honeypot detection, contract risks)
- Holder analysis (whale concentration, top buyers)
- **Adaptive Safety Score** (0-100): Rates token safety based on liquidity, holders, age, security flags, and social presence.
- **Social Links**: Twitter, Website, Telegram.

**Note on BSC**: Due to upstream limitations, BSC deep analysis relies heavily on the **Trending Cache**. If a BSC token is not found in the trending cache, the fallback direct scrape may be limited or blocked, potentially resulting in a lower safety score due to missing data. The service handles this gracefully (no 500 errors).

**Usage:**
```bash
# Analyze a Solana token
curl http://localhost:8000/api/v1/analysis/deep/sol/{TOKEN_ADDRESS}
```
# Analyze an Ethereum token
curl http://localhost:8000/api/v1/analysis/deep/eth/{TOKEN_ADDRESS}
```

**Example Response:**
```json
{
  "address": "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN",
  "chain": "sol",
  "market_data": {
    "symbol": "TRUMP",
    "price": 6.33,
    "market_cap": 6340965000.0,
    "volume_24h": 42201770.0,
    "holder_count": 50000
  },
  "security": {
    "is_honeypot": false,
    "is_mintable": false,
    "is_open_source": true
  },
  "holders": {
    "whale_concentration_top10": 15.5,
    "top_buyers_count": 10
  },
  "errors": []
}
```

## Signals Endpoints

These endpoints provide real-time triggers for specific trading opportunities.

### Graduation Radar
Detects tokens on bonding curves (e.g., Pump.fun) nearing completion (95-100%).
**Use Case:** Catch tokens *before* they list on DEXs like Raydium.

```bash
# Scan for tokens >95% complete with at least 50 holders
curl "http://localhost:8000/api/v1/signals/pump-graduation?chain=sol&min_progress=95"
```

### Early Gem Detection
Finds newly listed pairs (last 1 hour) with high initial liquidity.
**Use Case:** Catch high-quality launches immediately.

```bash
# Scan for new pairs with >$10k liquidity
curl "http://localhost:8000/api/v1/signals/early-gems?chain=sol&min_liquidity=10000"
```

### Momentum Scanner
Detects tokens with high trading volume relative to market cap (Turnover) and positive price momentum.
**Use Case:** Catching breakouts and high-interest tokens in real-time.

```bash
# Scan for tokens with turnover >20% and price up >10%
curl "http://localhost:8000/api/v1/signals/momentum?chain=sol&min_vol_mcap_ratio=0.2&min_price_change=10"
```

## AI Assessment Endpoint

The service includes an AI-powered endpoint to generate "degen-style" assessments of tokens. This is designed to be the final step in an automated workflow.

- **Endpoint**: `POST /api/v1/ai/assess`
- **Supported Providers**: OpenAI (default), Anthropic.
- **Configuration**: Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env`.

**Example Request:**
```json
{
  "token": {
    "name": "Pepe",
    "symbol": "PEPE",
    "address": "0x...",
    "chain": "sol",
    "market_cap": 1000000,
    "liquidity": 50000,
    "holder_count": 1000
  },
  "security": {
    "is_honeypot": false,
    "is_mintable": false
  },
  "safety_score": 85
}
```

**Example Response:**
```json
{
  "verdict": "BULLISH",
  "summary": "This coin is sending signals...",
  "risk": {
    "risk_level": "LOW",
    "score": 85,
    "positive_signals": ["High liquidity", "Renounced contract"]
  },
  "meme_potential_score": 92
}
```

## N8N Integration Workflow

This service is designed to be orchestrated by **n8n**. A typical workflow for finding and analyzing 100x gems involves:

1.  **Trigger**: Run on a schedule (e.g., every 5-10 minutes).
2.  **Step 1: Fetch Trending Tokens**
    - **Node**: HTTP Request
    - **URL**: `GET http://host.docker.internal:8000/api/v1/analysis/trending?chain=sol&min_consistency=2`
    - **Purpose**: Get a list of potential candidates.
3.  **Step 2: Iterate & Filter**
    - **Node**: Loop over items.
    - **Logic**: Filter by `safety_score` or other basic metrics.
4.  **Step 3: Deep Analysis**
    - **Node**: HTTP Request
    - **URL**: `GET http://host.docker.internal:8000/api/v1/analysis/deep/sol/{{$json.address}}`
    - **Purpose**: Get detailed security, holder, and social data.
5.  **Step 4: AI Assessment (The "Degen Check")**
    - **Node**: HTTP Request
    - **Method**: POST
    - **URL**: `http://host.docker.internal:8000/api/v1/ai/assess`
    - **Body**: JSON
    - **Payload**: Construct the payload using data from Step 3.
      ```json
      {
        "token": {
          "name": "{{$json.market_data.name}}",
          "symbol": "{{$json.market_data.symbol}}",
          "address": "{{$json.address}}",
          "chain": "{{$json.chain}}",
          "market_cap": {{$json.market_data.market_cap}},
          "liquidity": {{$json.market_data.liquidity}},
          "holder_count": {{$json.market_data.holder_count}}
        },
        "security": {{$json.security}},
        "social": {{$json.socials}},
        "safety_score": {{$json.safety.score}}
      }
      ```
6.  **Step 5: Alert/Action**
    - **Node**: Telegram/Discord/Slack
    - **Logic**: If `verdict` is "BULLISH" and `meme_potential_score` > 80, send an alert with the summary and entry suggestion.
