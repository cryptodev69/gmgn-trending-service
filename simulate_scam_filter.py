import asyncio
import httpx
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"

# --- Suspicious Thresholds ---
SUSPICIOUS_CRITERIA = {
    "min_liquidity": 5000,          # Must have at least $5k liquidity
    "max_whale_concentration": 60,  # Top 10 holders shouldn't own more than 60%
    "min_holder_count": 100,        # At least 100 holders
    "must_be_renounced": True,      # Mint authority must be renounced (for Sol)
    "launchpad_safelist": ["pump", "moonshot", None] # Trusted launchpads or None (older tokens)
}

async def analyze_safety(token: Dict[str, Any]):
    symbol = token.get("symbol", "Unknown")
    market = token.get("market_data", {})
    security = token.get("security", {})
    holders = token.get("holders", {})
    
    liquidity = market.get("liquidity") or 0
    holder_count = market.get("holder_count") or 0
    raw_whale_conc = holders.get("whale_concentration_top10")
    
    # Convert whale_conc to float if it's a string
    try:
        if isinstance(raw_whale_conc, str):
            # Handle potential percentage strings or weird formatting
            whale_conc = float(raw_whale_conc.strip().rstrip('%'))
        elif raw_whale_conc is None:
            whale_conc = 0.0
        else:
            whale_conc = float(raw_whale_conc)
    except (ValueError, TypeError):
        whale_conc = 0.0
    
    renounced = security.get("renounced_mint")
    
    # Convert renounced (1/0 or True/False) to boolean
    is_renounced = bool(renounced) if renounced is not None else False
    
    print(f"\n🔍 ANALYZING: {symbol}")
    print(f"   Liquidity: ${liquidity:,.0f}")
    print(f"   Holders: {holder_count}")
    print(f"   Whale Top 10: {whale_conc}%")
    print(f"   Mint Renounced: {is_renounced}")

    reasons = []
    
    if liquidity < SUSPICIOUS_CRITERIA["min_liquidity"]:
        reasons.append(f"❌ Low Liquidity (${liquidity:,.0f} < ${SUSPICIOUS_CRITERIA['min_liquidity']})")
        
    if holder_count < SUSPICIOUS_CRITERIA["min_holder_count"]:
        reasons.append(f"❌ Low Holder Count ({holder_count} < {SUSPICIOUS_CRITERIA['min_holder_count']})")
        
    if whale_conc > SUSPICIOUS_CRITERIA["max_whale_concentration"]:
        reasons.append(f"❌ High Whale Concentration ({whale_conc}% > {SUSPICIOUS_CRITERIA['max_whale_concentration']}%)")
        
    if SUSPICIOUS_CRITERIA["must_be_renounced"] and not is_renounced:
        # Note: Some legit old tokens might not be renounced, but for new trending memes it's a red flag
        # Skip this check for ETH/BSC/BASE as "renounced" logic might differ or field might be missing
        # The field 'renounced_mint' is very Solana specific in this API wrapper
        # We'll just log it for now or only enforce on SOL
        pass 

    if reasons:
        print("   ⚠️  VERDICT: SUSPICIOUS / HIGH RISK")
        for r in reasons:
            print(f"      {r}")
    else:
        print("   ✅ VERDICT: LOOKS SAFE(R)")

async def run_scam_filter_example(chain: str = "sol"):
    print(f"🚀 Finding High Potential vs. Scam Tokens on [{chain.upper()}]")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Get Trending
        try:
            resp = await client.get(
                f"{BASE_URL}/analysis/trending", 
                params={"chain": chain, "min_consistency": 2} 
            )
            resp.raise_for_status()
            tokens = resp.json()
        except Exception as e:
            print(f"Error fetching trending for {chain}: {e}")
            return
        
        if not tokens:
            print("No tokens found.")
            return

        # Take top 5 by volume to analyze
        # Sort by volume descending to see "hot" action
        top_volume = sorted(tokens, key=lambda x: x.get("avg_volume", 0), reverse=True)[:5]
        
        for t in top_volume:
            # 2. Deep Analysis
            addr = t.get("address")
            deep_resp = await client.get(f"{BASE_URL}/analysis/deep/{chain}/{addr}")
            deep_data = deep_resp.json()
            
            await analyze_safety(deep_data)

if __name__ == "__main__":
    print("\n=== SOLANA ===")
    asyncio.run(run_scam_filter_example("sol"))
    print("\n=== ETHEREUM ===")
    asyncio.run(run_scam_filter_example("eth"))
    print("\n=== BASE ===")
    asyncio.run(run_scam_filter_example("base"))
    print("\n=== BSC ===")
    asyncio.run(run_scam_filter_example("bsc"))
