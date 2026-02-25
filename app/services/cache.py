import redis
import json
import hashlib
from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_cache_key(message: str, language: str) -> str:
    content = f"{message}:{language}"
    return f"cosmoai:chat:{hashlib.md5(content.encode()).hexdigest()}"

def get_cached_response(message: str, language: str):
    try:
        key = get_cache_key(message, language)
        cached = redis_client.get(key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    return None

def set_cached_response(message: str, language: str, response: str, ttl: int = 3600):
    try:
        key = get_cache_key(message, language)
        redis_client.setex(key, ttl, json.dumps(response))
    except Exception:
        pass

def clear_cache():
    try:
        keys = redis_client.keys("cosmoai:chat:*")
        if keys:
            redis_client.delete(*keys)
    except Exception:
        pass