import asyncio
import httpx
from typing import Optional, Dict, Any, Union
from app.core.config import settings
from concurrent.futures import ThreadPoolExecutor

class GMGNClient:
    def __init__(self):
        self.base_url = settings.GMGN_WRAPPER_URL
        self.api_key = settings.GMGN_API_KEY
        self.headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        self.executor = ThreadPoolExecutor(max_workers=5) # For fallback ops

    def _get_chain_path(self, chain: str) -> str:
        """Map internal chain codes to wrapper paths."""
        chain_map = {
            "sol": "solana",
            "eth": "ethereum",
            "base": "base",
            "bsc": "binance"
        }
        return chain_map.get(chain, chain)

    async def _get_fallback_bsc(self, timeframe: str) -> Dict[str, Any]:
        """
        Fallback method to directly scrape GMGN for BSC tokens.
        Returns data in the structure expected by AnalysisService: {"rank": [...]} 
        or compatible with wrapper response {"tokens": [...]}.
        """
        # We need tls_client here locally since we are bypassing wrapper
        import tls_client
        from fake_useragent import UserAgent
        import random
        
        identifier = random.choice(
            [browser for browser in tls_client.settings.ClientIdentifiers.__args__ 
             if browser.startswith(('chrome', 'safari', 'firefox', 'opera'))]
        )
        session = tls_client.Session(
            random_tls_extension_order=True, 
            client_identifier=identifier
        )
        
        # Basic user agent generation
        parts = identifier.split('_')
        browser_name = parts[0]
        if browser_name == 'opera': browser_name = 'chrome'
        os_name = 'windows'
        
        user_agent = UserAgent(browsers=[browser_name], os=[os_name]).random
        
        headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json',
            'user-agent': user_agent,
            'referer': 'https://gmgn.ai/?chain=bsc'
        }
        
        # Construct URL manually
        limit_param = "&limit=20" if timeframe == "1m" else ""
        url = f"https://gmgn.ai/defi/quotation/v1/rank/bsc/swaps/{timeframe}?orderby=swaps&direction=desc{limit_param}"
        
        loop = asyncio.get_event_loop()
        
        def _sync_req():
            resp = session.get(url, headers=headers)
            if resp.status_code >= 400:
                raise Exception(f"BSC Direct Error: {resp.status_code}")
            data = resp.json()
            if data.get("code") == 0 and "data" in data:
                # The direct API returns {"data": {"rank": [...]}}
                # We return {"rank": [...]} to match legacy format which AnalysisService handles
                return data["data"] 
            return {}

        return await loop.run_in_executor(self.executor, _sync_req)

    async def _get(self, endpoint: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/api{endpoint}"
            response = await self.client.get(url, headers=self.headers)
            
            if response.status_code >= 400:
                # Log error but try to continue or return error dict
                print(f"Wrapper Error {response.status_code}: {response.text}")
                return {"error": f"Upstream error: {response.status_code}"}
            
            return response.json()
        except Exception as e:
            print(f"Request failed: {e}")
            return {"error": str(e)}

    async def get_token_info(self, contract_address: str, chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        
        # Wrapper returns 404/500 for BSC sometimes?
        # If chain is BSC, we might need a fallback if wrapper fails
        try:
            data = await self._get(f"/{chain_path}/token-info/{contract_address}")
            if "error" in data and chain == "bsc":
                raise Exception("Wrapper failed for BSC")
            return data
        except Exception:
            if chain == "bsc":
                return await self._get_fallback_bsc_token_info(contract_address)
            raise

    async def _get_fallback_bsc_token_info(self, address: str) -> Dict[str, Any]:
        """
        Direct scrape fallback for BSC token info.
        Using new v1 endpoints often fails with 40000300 invalid argument for some tokens.
        Trying v2 or just rank endpoint if possible, or accepting that some tokens fail.
        """
        import tls_client
        from fake_useragent import UserAgent
        import random
        
        identifier = random.choice(
            [browser for browser in tls_client.settings.ClientIdentifiers.__args__ 
             if browser.startswith(('chrome', 'safari', 'firefox'))]
        )
        session = tls_client.Session(
            random_tls_extension_order=True, 
            client_identifier=identifier
        )
        
        headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json',
            'user-agent': UserAgent().random,
            'referer': 'https://gmgn.ai/?chain=bsc'
        }
        
        # Try different endpoint structure if v1 fails
        url = f"https://gmgn.ai/defi/quotation/v1/tokens/bsc/{address}"
        
        loop = asyncio.get_event_loop()
        def _sync_req():
            try:
                # Add retries with delay
                import time
                for _ in range(2):
                    resp = session.get(url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("code") == 0 and "data" in data and data["data"].get("token"):
                            return data["data"]["token"]
                        elif data.get("code") == 0 and "data" in data:
                             return data["data"]
                    time.sleep(1)
                    
                return {"error": f"Direct scrape failed: {resp.status_code} - {resp.text[:100]}"}
            except Exception as e:
                return {"error": f"Direct scrape exception: {str(e)}"}

        return await loop.run_in_executor(self.executor, _sync_req)

    async def get_new_pairs(self, limit: int = 50, chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        # Wrapper might not support limit param directly in URL path if not query
        return await self._get(f"/{chain_path}/new-pairs?limit={limit}")

    async def get_trending_wallets(self, timeframe: str = "7d", wallet_tag: str = "smart_degen", chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        return await self._get(f"/{chain_path}/trending-wallets?timeframe={timeframe}&tag={wallet_tag}")

    async def get_trending_tokens(self, timeframe: str = "1h", chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        # Wrapper endpoint is /api/{chain}/trending-tokens
        # It returns {"tokens": [...]} which matches what we want roughly, but we need to adapt
        # My analysis service expects a structure.
        # Original GMGN response: {"data": {"rank": [...]}}
        # Wrapper response: {"tokens": [...]}
        # I need to normalize this return to match what analysis service expects or update analysis service.
        # Better to update analysis service to handle this cleaner structure.
        
        # Special handling for BSC: Wrapper seems to return empty or 404
        # Fallback to direct scrape if chain is bsc
        if chain == "bsc":
            try:
                direct_data = await self._get_fallback_bsc(timeframe)
                if direct_data:
                    return direct_data
            except Exception as e:
                print(f"Direct BSC fallback failed: {e}")
                # Fallthrough to wrapper just in case
        
        return await self._get(f"/{chain_path}/trending-tokens?timeframe={timeframe}")

    async def get_tokens_by_completion(self, limit: int = 50, chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        return await self._get(f"/{chain_path}/tokens-by-completion?limit={limit}")

    async def find_sniped_tokens(self, size: int = 10, chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        return await self._get(f"/{chain_path}/sniped-tokens?size={size}")

    async def get_gas_fee(self, chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        return await self._get(f"/{chain_path}/gas-fee")

    async def get_token_usd_price(self, contract_address: str, chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        return await self._get(f"/{chain_path}/token-usd-price/{contract_address}")

    async def get_top_buyers(self, contract_address: str, chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        try:
            data = await self._get(f"/{chain_path}/top-buyers/{contract_address}")
            if "error" in data and chain == "bsc":
                raise Exception("Wrapper failed for BSC")
            return data
        except Exception:
            if chain == "bsc":
                return await self._get_fallback_bsc_top_buyers(contract_address)
            raise

    async def _get_fallback_bsc_top_buyers(self, address: str) -> Dict[str, Any]:
        import tls_client
        from fake_useragent import UserAgent
        import random
        
        # Use simpler identifiers to avoid 403
        identifier = "chrome_120"
        session = tls_client.Session(client_identifier=identifier)
        
        headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json',
            'user-agent': UserAgent().random,
            'referer': 'https://gmgn.ai/?chain=bsc',
            'cookie': '_ga=GA1.1.123456789.1234567890' # Mock cookie sometimes helps
        }
        
        url = f"https://gmgn.ai/defi/quotation/v1/tokens/top_buyers/bsc/{address}"
        
        loop = asyncio.get_event_loop()
        def _sync_req():
            try:
                # 403 usually means WAF block. 
                # If we fail, return empty list structure so deep analysis doesn't crash
                resp = session.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0 and "data" in data:
                        return data["data"]
                return {"top_buyers": [], "error": f"Direct scrape restricted: {resp.status_code}"}
            except Exception as e:
                return {"top_buyers": [], "error": f"Direct scrape exception: {str(e)}"}

        return await loop.run_in_executor(self.executor, _sync_req)

    async def get_security_info(self, contract_address: str, chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        try:
            data = await self._get(f"/{chain_path}/security-info/{contract_address}")
            if "error" in data and chain == "bsc":
                raise Exception("Wrapper failed for BSC")
            return data
        except Exception:
            if chain == "bsc":
                return await self._get_fallback_bsc_security_info(contract_address)
            raise

    async def _get_fallback_bsc_security_info(self, address: str) -> Dict[str, Any]:
        # Fallback for BSC security info
        import tls_client
        from fake_useragent import UserAgent
        import random
        
        identifier = random.choice(tls_client.settings.ClientIdentifiers.__args__)
        session = tls_client.Session(client_identifier=identifier)
        
        headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json',
            'user-agent': UserAgent().random,
            'referer': 'https://gmgn.ai/?chain=bsc'
        }
        
        url = f"https://gmgn.ai/defi/quotation/v1/tokens/security/bsc/{address}"
        
        loop = asyncio.get_event_loop()
        def _sync_req():
            resp = session.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and "data" in data:
                    return data["data"]
            return {}

        return await loop.run_in_executor(self.executor, _sync_req)

    async def get_wallet_info(self, wallet_address: str, period: str = "7d", chain: str = "sol") -> Dict[str, Any]:
        chain_path = self._get_chain_path(chain)
        return await self._get(f"/{chain_path}/wallet-info/{wallet_address}?period={period}")

gmgn_client = GMGNClient()
