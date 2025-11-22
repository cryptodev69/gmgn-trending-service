from cachetools import TTLCache
import threading

# Thread-safe cache with 60-second TTL and max 500 items
_cache = TTLCache(maxsize=500, ttl=60)
_cache_lock = threading.Lock()

def get_cached(key: str):
    """Get a value from cache."""
    with _cache_lock:
        return _cache.get(key)

def set_cached(key: str, value):
    """Set a value in cache."""
    with _cache_lock:
        _cache[key] = value

def clear_cache():
    """Clear all cached values (useful for testing)."""
    with _cache_lock:
        _cache.clear()
