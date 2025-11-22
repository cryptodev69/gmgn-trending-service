import asyncio
from typing import Dict, Any, Optional
from app.services.gmgn import gmgn_client
from app.services.analysis_service import get_trending_data_with_cache

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
    
    return response

def _format_trending_token_as_deep_analysis(token: Dict[str, Any], chain: str) -> Dict[str, Any]:
    """Convert flat trending token data into deep analysis structure."""
    return {
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
        "source": "trending_cache",
        "errors": []
    }
