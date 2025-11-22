import asyncio
import httpx
import json
from app.core.config import settings

BASE_URL = settings.GMGN_WRAPPER_URL
API_KEY = settings.GMGN_API_KEY

HEADERS = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

async def probe_endpoint(endpoint: str, desc: str):
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔎 PROBING: {desc}")
    print(f"   URL: {url}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url, headers=HEADERS)
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                # Try to extract the list of items
                items = []
                if isinstance(data, dict):
                    # Look for common keys list
                    for key in ["tokens", "pairs", "data", "rank"]:
                        if key in data and isinstance(data[key], list):
                            items = data[key]
                            print(f"   Found key '{key}' with {len(items)} items.")
                            break
                    if not items and "code" in data: # Direct list sometimes?
                         # Maybe deep nested
                         pass
                
                if items:
                    first = items[0]
                    print("   SAMPLE ITEM KEYS:", list(first.keys()))
                    print(f"   Sample Symbol: {first.get('symbol', 'N/A')}")
                    # Check specific interesting fields
                    interesting = ["liquidity", "sniper_count", "progress", "open_timestamp", "holder_count"]
                    found_interesting = {k: first.get(k) for k in interesting if k in first}
                    print(f"   Interesting Metrics: {found_interesting}")
                else:
                    print("   ⚠️  No items found or unknown structure.")
                    print(f"   Raw keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
            else:
                print(f"   ❌ Error: {resp.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

async def run_exploration():
    print("🚀 EXPLORING GMGN WRAPPER CAPABILITIES")
    
    # 1. New Pairs (Early Gems)
    await probe_endpoint("/api/solana/new-pairs?limit=10", "Solana New Pairs")
    await probe_endpoint("/api/ethereum/new-pairs?limit=10", "Ethereum New Pairs")
    
    # 2. Sniped Tokens (Sniper Watch)
    # Note: Wrapper endpoint might be /sniped-tokens or similar
    await probe_endpoint("/api/solana/sniped-tokens?size=10", "Solana Sniped Tokens")
    await probe_endpoint("/api/ethereum/sniped-tokens?size=10", "Ethereum Sniped Tokens")
    
    # 3. Bonding Curve Completion (Pump Graduation)
    await probe_endpoint("/api/solana/tokens-by-completion?limit=10", "Solana Bonding Curve (Pump.fun)")
    # ETH probably doesn't have this specific endpoint returning data, but worth checking
    await probe_endpoint("/api/base/tokens-by-completion?limit=10", "Base Bonding Curve (Virtuals?)")

if __name__ == "__main__":
    asyncio.run(run_exploration())
