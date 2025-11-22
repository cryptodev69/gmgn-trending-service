import asyncio
from typing import Dict, Any, Optional
from app.services.gmgn import gmgn_client
from app.services.analysis_service import get_trending_data_with_cache

import time

def calculate_safety_score(market: Dict[str, Any], security: Dict[str, Any], holders: Dict[str, Any], socials: Dict[str, str]) -> Dict[str, Any]:
    """
    Calculate a normalized safety score (0-100) based on available data.
    Adapts weights if specific data points (like whale concentration) are missing.
    """
    score = 0
    max_score = 0
    breakdown = []

    # 1. Liquidity (Max 30 pts)
    # > $100k = 30pts, > $50k = 20pts, > $10k = 10pts
    liquidity = market.get("liquidity") or 0
    liq_score = 0
    if liquidity > 100000:
        liq_score = 30
    elif liquidity > 50000:
        liq_score = 20
    elif liquidity > 10000:
        liq_score = 10
    
    score += liq_score
    max_score += 30
    breakdown.append(f"Liquidity (${liquidity:,.0f}): {liq_score}/30")

    # 2. Holder Count (Max 20 pts)
    # > 1000 = 20pts, > 500 = 15pts, > 100 = 5pts
    holder_count = market.get("holder_count") or 0
    holder_score = 0
    if holder_count > 1000:
        holder_score = 20
    elif holder_count > 500:
        holder_score = 15
    elif holder_count > 100:
        holder_score = 5
        
    score += holder_score
    max_score += 20
    breakdown.append(f"Holders ({holder_count}): {holder_score}/20")

    # 3. Token Age (Max 10 pts)
    # > 7 days = 10pts, > 24h = 5pts
    created_ts = market.get("created_timestamp")
    age_score = 0
    if created_ts:
        age_hours = (time.time() - created_ts) / 3600
        if age_hours > 168: # 7 days
            age_score = 10
        elif age_hours > 24:
            age_score = 5
    
    score += age_score
    max_score += 10
    breakdown.append(f"Age: {age_score}/10")

    # 4. Security Flags (Max 20 pts)
    # Not Honeypot: 10pts
    # Renounced/No Mint: 10pts
    sec_score = 0
    if security.get("is_honeypot") is False: # Explicitly False, not None
        sec_score += 10
    elif security.get("is_honeypot") is None:
        # If null, we can't verify, so we neutral it or give partial trust?
        # Let's be conservative: 0 points if unknown
        pass
        
    # Mintable check (False is good) or Renounced (True is good)
    if security.get("is_mintable") is False:
        sec_score += 10
    elif security.get("renounced_mint") == 1 or security.get("renounced_mint") is True:
        sec_score += 10
        
    score += sec_score
    max_score += 20
    breakdown.append(f"Security: {sec_score}/20")

    # 5. Whale Concentration (Max 20 pts) - ADAPTIVE
    # Only count this if we actually have data > 0 (since 0.0 usually means missing data for ETH/BSC)
    whale_conc = holders.get("whale_concentration_top10")
    
    # If whale_conc is effectively present (and not the suspicious exactly 0.0 on ETH/BSC which implies missing data)
    # However, 0.0 could effectively mean perfectly distributed, but highly unlikely.
    # We will treat 0.0 as "missing" for safety unless we are sure.
    # Let's check if top_holders list exists to confirm data validity.
    has_holder_data = (whale_conc is not None and whale_conc > 0) or (holders.get("top_holders") and len(holders["top_holders"]) > 0)
    
    if has_holder_data:
        whale_score = 0
        if whale_conc is None: whale_conc = 100 # Assume worst if missing but list exists
        
        if whale_conc < 30:
            whale_score = 20
        elif whale_conc < 50:
            whale_score = 10
        elif whale_conc < 70:
            whale_score = 5
            
        score += whale_score
        max_score += 20
        breakdown.append(f"Whale Conc ({whale_conc}%): {whale_score}/20")
    else:
        # Data missing, do not include in max_score so we don't penalize
        breakdown.append("Whale Conc: N/A (Excluded)")

    # 6. Social Presence (Max 15 pts)
    # Website: 5pts, Twitter: 5pts, Telegram/Discord: 5pts
    social_score = 0
    if socials.get("website"):
        social_score += 5
    if socials.get("twitter_username") or socials.get("twitter"):
        social_score += 5
    if socials.get("telegram") or socials.get("discord"):
        social_score += 5
    
    score += social_score
    max_score += 15
    breakdown.append(f"Socials: {social_score}/15")

    # Normalize to 100
    if max_score > 0:
        final_score = (score / max_score) * 100
    else:
        final_score = 0

    return {
        "score": round(final_score, 2),
        "breakdown": breakdown
    }

async def deep_analyze_token(address: str, chain: str = "sol") -> Dict[str, Any]:
    """
    Perform deep analysis on a token.
    Priority:
    1. Check if token is in cached trending data (fastest & most reliable for trending tokens).
    2. Fallback to direct API calls (for non-trending tokens).
    """
    # 1. Try to find in trending cache (check 1h timeframe as it's most comprehensive)
    trending_data = await get_trending_data_with_cache("1h", chain)
    found_token = None
    
    if isinstance(trending_data, dict):
        tokens = trending_data.get("tokens") or trending_data.get("rank") or []
        for t in tokens:
            if t.get("address") == address:
                found_token = t
                break
    
    if found_token:
        return _format_trending_token_as_deep_analysis(found_token, chain)

    # 2. Fallback: Fetch data concurrently
    results = await asyncio.gather(
        gmgn_client.get_token_info(contract_address=address, chain=chain),
        gmgn_client.get_security_info(contract_address=address, chain=chain),
        gmgn_client.get_top_buyers(contract_address=address, chain=chain),
        return_exceptions=True
    )
    
    token_info, security_info, top_buyers = results
    
    # Build response with partial data even if some calls failed
    response = {
        "address": address,
        "chain": chain,
        "market_data": {},
        "security": {},
        "holders": {},
        "socials": {},
        "errors": []
    }
    
    # Process token info
    if isinstance(token_info, Exception):
        response["errors"].append(f"Token info error: {str(token_info)}")
    elif isinstance(token_info, dict):
        if "error" in token_info:
             response["errors"].append(f"Token info error: {token_info['error']}")
        else:
            # Handle potential different structure
            token_data = token_info.get("token") if "token" in token_info else token_info
            
            response["market_data"] = {
                "symbol": token_data.get("symbol"),
                "name": token_data.get("name"),
                "price": token_data.get("price"),
                "market_cap": token_data.get("market_cap"),
                "liquidity": token_data.get("liquidity"),
                "volume_24h": token_data.get("volume"),
                "price_change_24h": token_data.get("price_change_24h"),
                "holder_count": token_data.get("holder_count"),
                "created_timestamp": token_data.get("created_timestamp")
            }
            
            # Extract socials from token info (usually in 'social_links' or top level)
            raw_socials = token_data.get("social_links") or token_data
            response["socials"] = {
                "twitter_username": raw_socials.get("twitter_username"),
                "website": raw_socials.get("website"),
                "telegram": raw_socials.get("telegram"),
                "discord": raw_socials.get("discord")
            }
    
    # Process security info
    if isinstance(security_info, Exception):
        response["errors"].append(f"Security info error: {str(security_info)}")
    elif isinstance(security_info, dict):
        if "error" in security_info:
             response["errors"].append(f"Security info error: {security_info['error']}")
        else:
            # Wrapper structure: {"security_info": {...}} or direct?
            sec_data = security_info.get("security_info") or security_info
            
            response["security"] = {
                "is_honeypot": sec_data.get("is_honeypot"),
                "is_open_source": sec_data.get("is_open_source"),
                "is_proxy": sec_data.get("is_proxy"),
                "is_mintable": sec_data.get("is_mintable"),
                "owner_address": sec_data.get("owner_address"),
                "creator_address": sec_data.get("creator_address"),
                "can_take_back_ownership": sec_data.get("can_take_back_ownership"),
                "owner_change_balance": sec_data.get("owner_change_balance"),
                "hidden_owner": sec_data.get("hidden_owner"),
                "selfdestruct": sec_data.get("selfdestruct"),
                "external_call": sec_data.get("external_call"),
                # Add flags from wrapper if present
                "renounced_mint": sec_data.get("renounced_mint"), 
                "renounced_freeze_account": sec_data.get("renounced_freeze_account")
            }
    
    # Process top buyers
    if isinstance(top_buyers, Exception):
        response["errors"].append(f"Top buyers error: {str(top_buyers)}")
    elif isinstance(top_buyers, dict):
        if "error" in top_buyers:
             response["errors"].append(f"Top buyers error: {top_buyers['error']}")
        else:
            buyers_list = top_buyers if isinstance(top_buyers, list) else top_buyers.get("top_buyers", [])
            
            # Calculate whale concentration
            total_holdings = 0
            top_10_holdings = 0
            
            for i, buyer in enumerate(buyers_list[:10] if isinstance(buyers_list, list) else []):
                holding = float(buyer.get("amount", 0) or 0)
                top_10_holdings += holding
                total_holdings += holding
                
            whale_concentration = (top_10_holdings / total_holdings * 100) if total_holdings > 0 else 0
            
            response["holders"] = {
                "top_buyers_count": len(buyers_list) if isinstance(buyers_list, list) else 0,
                "whale_concentration_top10": round(whale_concentration, 2),
                "top_holders": buyers_list[:10] if isinstance(buyers_list, list) else []
            }
    
    # Calculate Safety Score
    safety = calculate_safety_score(response["market_data"], response["security"], response["holders"], response["socials"])
    response["safety"] = safety
    
    return response

def _format_trending_token_as_deep_analysis(token: Dict[str, Any], chain: str) -> Dict[str, Any]:
    """Convert flat trending token data into deep analysis structure."""
    resp = {
        "address": token.get("address"),
        "chain": chain,
        "market_data": {
            "symbol": token.get("symbol"),
            "name": token.get("name"),
            "price": token.get("price"),
            "market_cap": token.get("market_cap"),
            "liquidity": token.get("liquidity"),
            "volume_24h": token.get("volume"),
            "price_change_24h": token.get("price_change_percent"),
            "holder_count": token.get("holder_count"),
            "created_timestamp": token.get("open_timestamp")
        },
        "security": {
            "is_honeypot": None, # Not usually in trending list explicitly unless "not_honeypot" filter
            "is_mintable": None, 
            "renounced_mint": token.get("renounced_mint"),
            "renounced_freeze_account": token.get("renounced_freeze_account"),
            "burn_ratio": token.get("burn_ratio"),
            "burn_status": token.get("burn_status"),
            "launchpad": token.get("launchpad")
        },
        "holders": {
            "whale_concentration_top10": token.get("top_10_holder_rate") * 100 if token.get("top_10_holder_rate") else 0,
            "top_buyers_count": None, # Not available in trending list
            "bluechip_owner_percentage": token.get("bluechip_owner_percentage"),
            "smart_degen_count": token.get("smart_degen_count")
        },
        "socials": {
            "twitter_username": token.get("twitter_username"),
            "website": token.get("website"),
            "telegram": token.get("telegram"),
            "discord": None # Trending list usually doesn't have discord
        },
        "source": "trending_cache",
        "errors": []
    }
    
    # Calculate Safety Score for cached data too
    safety = calculate_safety_score(resp["market_data"], resp["security"], resp["holders"], resp["socials"])
    resp["safety"] = safety
    
    return resp
