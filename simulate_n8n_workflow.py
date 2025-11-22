import asyncio
import httpx
import json
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"

async def fetch_trending(chain: str, min_consistency: int = 3) -> List[Dict[str, Any]]:
    """Step 1: Fetch trending tokens (Simulates n8n HTTP Request node)"""
    url = f"{BASE_URL}/analysis/trending"
    params = {
        "chain": chain,
        "min_consistency": min_consistency,
        "volume_threshold": 1000,
        "market_cap_threshold": 10000
    }
    
    logger.info(f"Fetching trending tokens for chain: {chain}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=60.0)
        response.raise_for_status()
        return response.json()

async def fetch_deep_analysis(chain: str, address: str) -> Dict[str, Any]:
    """Step 2: Deep analysis on specific token (Simulates n8n HTTP Request inside Loop)"""
    url = f"{BASE_URL}/analysis/deep/{chain}/{address}"
    
    logger.info(f"Performing deep analysis for token: {address}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=60.0)
        response.raise_for_status()
        return response.json()

async def simulate_workflow(chain: str = "sol"):
    print(f"\n{'='*50}")
    print(f"🚀 STARTING N8N SIMULATION WORKFLOW FOR [{chain.upper()}]")
    print(f"{'='*50}\n")

    # --- Step 1: Get Trending Tokens ---
    try:
        trending_tokens = await fetch_trending(chain)
        print(f"✅ Found {len(trending_tokens)} trending tokens matching criteria.")
    except Exception as e:
        logger.error(f"Failed to fetch trending tokens: {e}")
        return

    if not trending_tokens:
        logger.warning("No tokens found. Workflow ends.")
        return

    # --- Step 2: Filter/Select (n8n Logic) ---
    # Let's say n8n takes the top 3 tokens sorted by consistency and volume
    top_tokens = trending_tokens[:3]
    print(f"🔍 Selecting top {len(top_tokens)} for deep dive analysis:\n")

    for i, t in enumerate(top_tokens, 1):
        print(f"   {i}. {t.get('symbol')} ({t.get('address')}) - Consistency: {t.get('consistency_count')}/5")

    print("\n" + "-"*30 + "\n")

    # --- Step 3: Deep Analysis Loop ---
    results = []
    for token in top_tokens:
        address = token.get("address")
        symbol = token.get("symbol")
        
        try:
            analysis = await fetch_deep_analysis(chain, address)
            results.append(analysis)
            
            # Print a summary of the deep analysis
            market = analysis.get("market_data", {})
            security = analysis.get("security", {})
            holders = analysis.get("holders", {})
            socials = analysis.get("socials", {})
            safety = analysis.get("safety", {})
            
            print(f"📊 ANALYSIS REPORT: {symbol}")
            print(f"   Price: ${market.get('price')}")
            print(f"   Liquidity: ${market.get('liquidity'):,.0f}")
            print(f"   Holder Count: {market.get('holder_count')}")
            print(f"   Security Flags:")
            print(f"     - Honeypot: {security.get('is_honeypot')}")
            print(f"     - Mintable: {security.get('is_mintable')}")
            print(f"     - Renounced: {security.get('renounced_mint')}")
            print(f"   Whale Concentration (Top 10): {holders.get('whale_concentration_top10')}%")
            
            print(f"   Socials:")
            print(f"     - Twitter: {socials.get('twitter_username') or 'N/A'}")
            print(f"     - Website: {socials.get('website') or 'N/A'}")
            print(f"     - Telegram: {socials.get('telegram') or 'N/A'}")
            
            print(f"   🛡️  SAFETY SCORE: {safety.get('score')}/100")
            if safety.get('breakdown'):
                print("      Breakdown:")
                for item in safety['breakdown']:
                    print(f"      - {item}")
            
            print(f"   Source: {analysis.get('source', 'live_fetch')}")
            print("\n")
            
        except Exception as e:
            logger.error(f"Failed analysis for {symbol}: {e}")

    print(f"{'='*50}")
    print("✅ WORKFLOW COMPLETE")
    print(f"{'='*50}")

if __name__ == "__main__":
    # You can change the chain here to 'eth', 'base', 'bsc' to test others
    asyncio.run(simulate_workflow(chain="sol"))
