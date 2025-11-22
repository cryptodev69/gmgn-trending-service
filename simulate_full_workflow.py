import asyncio
import httpx
import logging
from typing import List, Dict, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"

# Configuration
CONFIG = {
    "min_consistency": 3,
    "min_liquidity_gem": 10000,
    "min_progress_grad": 98.0,
    "min_safety_score": 70.0,
    "timeout": 60.0
}

async def fetch_trending(client: httpx.AsyncClient, chain: str) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/analysis/trending"
    params = {
        "chain": chain,
        "min_consistency": CONFIG["min_consistency"]
    }
    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"[{chain}] Trending: Found {len(data)} tokens")
        return data
    except Exception as e:
        logger.error(f"[{chain}] Trending Error: {e}")
        return []

async def fetch_graduation_signals(client: httpx.AsyncClient, chain: str) -> List[Dict[str, Any]]:
    # Only for Solana usually, but flexible
    url = f"{BASE_URL}/signals/pump-graduation"
    params = {
        "chain": chain,
        "min_progress": CONFIG["min_progress_grad"]
    }
    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"[{chain}] Graduation Signals: Found {len(data)} tokens")
        return data
    except Exception as e:
        # Expected for non-pump chains
        logger.warning(f"[{chain}] Graduation Signal Skipped/Error: {e}")
        return []

async def fetch_gem_signals(client: httpx.AsyncClient, chain: str) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/signals/early-gems"
    params = {
        "chain": chain,
        "min_liquidity": CONFIG["min_liquidity_gem"]
    }
    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"[{chain}] Early Gem Signals: Found {len(data)} tokens")
        return data
    except Exception as e:
        logger.error(f"[{chain}] Early Gem Error: {e}")
        return []

async def deep_analyze(client: httpx.AsyncClient, chain: str, address: str, source: str) -> Dict[str, Any]:
    url = f"{BASE_URL}/analysis/deep/{chain}/{address}"
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        data["trigger_source"] = source
        return data
    except Exception as e:
        logger.error(f"[{chain}] Deep Analysis Error for {address}: {e}")
        return None

async def simulate_chain_workflow(chain: str):
    print(f"\n{'='*60}")
    print(f"🛠️  EXECUTING WORKFLOW FOR CHAIN: [{chain.upper()}]")
    print(f"{'='*60}")
    
    async with httpx.AsyncClient(timeout=CONFIG["timeout"]) as client:
        # 1. Aggregation Phase (Parallel Fetch)
        # -------------------------------------
        tasks = [
            fetch_trending(client, chain),
            fetch_gem_signals(client, chain)
        ]
        # Only add graduation radar for Solana
        if chain == "sol":
            tasks.append(fetch_graduation_signals(client, chain))
            
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        trending_list = results[0]
        gem_list = results[1]
        grad_list = results[2] if len(results) > 2 else []
        
        # Deduplicate by Address
        unique_tokens = {}
        
        for t in trending_list:
            unique_tokens[t['address']] = {"symbol": t.get("symbol"), "source": "Trending"}
            
        for t in gem_list:
            if t['address'] not in unique_tokens:
                unique_tokens[t['address']] = {"symbol": t.get("symbol"), "source": "Early Gem"}
            else:
                unique_tokens[t['address']]["source"] += " + Early Gem"
                
        for t in grad_list:
            if t['address'] not in unique_tokens:
                unique_tokens[t['address']] = {"symbol": t.get("symbol"), "source": "Graduation Radar"}
            else:
                unique_tokens[t['address']]["source"] += " + Graduation Radar"
        
        print(f"\n🔹 AGGREGATION COMPLETE: {len(unique_tokens)} unique tokens identified.")
        
        # Limit for simulation to avoid rate limits/time
        tokens_to_analyze = list(unique_tokens.items())[:5] # Analyze top 5
        print(f"🔹 ANALYZING TOP {len(tokens_to_analyze)} CANDIDATES...\n")
        
        # 2. Deep Analysis Phase
        # ----------------------
        candidates = []
        for address, info in tokens_to_analyze:
            analysis = await deep_analyze(client, chain, address, info["source"])
            if analysis:
                candidates.append(analysis)
        
        # 3. Filter & Decision Phase
        # --------------------------
        valid_buys = []
        for c in candidates:
            safety = c.get("safety", {})
            score = safety.get("score", 0)
            symbol = c.get("market_data", {}).get("symbol", "Unknown")
            
            print(f"   📝 {symbol} ({c['trigger_source']}) -> Score: {score}/100")
            
            if score >= CONFIG["min_safety_score"]:
                valid_buys.append(c)
            else:
                print(f"      ❌ Rejected: Score too low (< {CONFIG['min_safety_score']})")
                
        # 4. Final Output
        # ---------------
        print(f"\n✅ FINAL BUY CANDIDATES [{len(valid_buys)}]:")
        for b in valid_buys:
            market = b.get("market_data", {})
            print(f"   🚀 {market.get('symbol')} | Score: {b['safety']['score']} | Liq: ${market.get('liquidity',0):,.0f}")
            print(f"      Source: {b['trigger_source']}")
            print(f"      Reason: {b['safety']['breakdown']}")
            print("")

if __name__ == "__main__":
    print("Running Multi-Chain Workflow Simulation...")
    # Run for all major chains
    chains = ["sol", "eth", "base", "bsc"]
    
    for chain in chains:
        asyncio.run(simulate_chain_workflow(chain))
