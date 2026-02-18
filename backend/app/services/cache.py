import json
import redis.asyncio as redis
from typing import Dict, Any
import os
from datetime import datetime
from decimal import Decimal

# Initialize Redis client (typically configured centrally).
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

async def get_revenue_summary(property_id: str, tenant_id: str, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
    """
    Fetches revenue summary, utilizing caching to improve performance.
    """
    # Create a cache key that includes the time range to prevent data overlap
    date_key = ""
    if start_date and end_date:
        date_key = f":{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
        
    cache_key = f"revenue:{tenant_id}:{property_id}{date_key}"
    
    # Try to get from cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Revenue calculation is delegated to the reservation service.
    from app.services.reservations import calculate_total_revenue
    
    # Calculate revenue
    result = await calculate_total_revenue(property_id, tenant_id, start_date, end_date)
    


    
    from app.core.money import Money
    
    if 'total' in result and isinstance(result['total'], Decimal):
        result['total'] = Money.to_string(result['total'])
    
    # Cache the result for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result
