# n8n Integration Guide

This guide describes how to integrate the GMGN Trending Service with n8n to build an automated multi-chain crypto intelligence bot.

## Architecture Overview

The recommended workflow consists of 3 main stages:
1.  **Trigger & Aggregation**: Timed execution (e.g., every 5 minutes) fetching data from multiple sources (Trending, Signals).
2.  **Deep Analysis Loop**: Iterating through unique tokens to fetch detailed metrics and safety scores.
3.  **Filtering & Action**: Applying logic based on the `safety.score` and `trigger_source` to send alerts or execute trades.

---

## Step 1: Aggregation (Parallel Execution)

Use an **HTTP Request** node to fetch data from multiple endpoints in parallel or sequence.

### 1.1 Trending Tokens (Consistency Check)
Fetches tokens that are consistently trending across timeframes.
- **Method**: `GET`
- **URL**: `http://SERVICE_URL/api/v1/analysis/trending`
- **Query Parameters**:
    - `chain`: `sol`, `eth`, `base`, or `bsc`
    - `min_consistency`: `3` (Recommended)

### 1.2 Early Gems (New Pairs)
Fetches newly listed pairs with high liquidity.
- **Method**: `GET`
- **URL**: `http://SERVICE_URL/api/v1/signals/early-gems`
- **Query Parameters**:
    - `chain`: `sol`, `eth`, `base`, or `bsc`
    - `min_liquidity`: `10000`
    - `max_age_minutes`: `60`

### 1.3 Graduation Radar (Solana Only)
Fetches Pump.fun tokens about to hit Raydium.
- **Method**: `GET`
- **URL**: `http://SERVICE_URL/api/v1/signals/pump-graduation`
- **Query Parameters**:
    - `chain`: `sol`
    - `min_progress`: `95`

---

## Step 2: Deduplication & Loop

Use a **Code Node** or **Merge Node** in n8n to:
1.  Combine arrays from all sources.
2.  Deduplicate by `address`.
3.  Pass the unique list to a **Split In Batches** loop.

---

## Step 3: Deep Analysis (The Brain)

Inside the loop, call the deep analysis endpoint for each token.

- **Method**: `GET`
- **URL**: `http://SERVICE_URL/api/v1/analysis/deep/{{chain}}/{{address}}`
- **Note**: This endpoint uses an internal cache (60s), so if the token was just fetched in Step 1 (Trending), this call will be instant (0ms latency).

**Response Structure**:
```json
{
  "address": "...",
  "market_data": { "liquidity": 50000, "holder_count": 500 },
  "security": { "is_honeypot": false },
  "safety": {
    "score": 85.5,
    "breakdown": ["Liquidity: 30/30", "Socials: 10/15"]
  },
  "socials": { "twitter_username": "...", "website": "..." }
}
```

---

## Step 4: Filtering Logic (The Filter)

Use an **If** node to filter candidates based on your risk profile.

**Conservative Strategy:**
- `safety.score` > **80**
- `market_data.liquidity` > **50000**

**Degen Strategy:**
- `safety.score` > **60**
- `market_data.liquidity` > **10000**

---

## JSON Example for n8n HTTP Request

```json
{
  "method": "GET",
  "url": "http://gmgn-service:8000/api/v1/analysis/deep/sol/{{$json.address}}",
  "options": {}
}
```
