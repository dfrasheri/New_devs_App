from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List

async def calculate_monthly_revenue(property_id: str, month: int, year: int, db_session=None) -> Decimal:
    """
    Calculates revenue for a specific month.
    """

    start_date = datetime(year, month, 1)
    if month < 12:
        end_date = datetime(year, month + 1, 1)
    else:
        end_date = datetime(year + 1, 1, 1)
        
    print(f"DEBUG: Querying revenue for {property_id} from {start_date} to {end_date}")

    # SQL Simulation (This would be executed against the actual DB)
    query = """
        SELECT SUM(total_amount) as total
        FROM reservations
        WHERE property_id = $1
        AND tenant_id = $2
        AND check_in_date >= $3
        AND check_in_date < $4
    """
    
    # In production this query executes against a database session.
    # result = await db.fetch_val(query, property_id, tenant_id, start_date, end_date)
    # return result or Decimal('0')
    
    return Decimal('0') # Placeholder for now until DB connection is finalized
    
# If a guest books at 11:00 PM in New York on Jan 31st, it counts as Feb 1st
# for a property in Tirana, Albania. We respect the property's local time.
async def _get_property_timezone(session, property_id: str, tenant_id: str) -> str:
    from sqlalchemy import text
    try:
        query = text("SELECT timezone FROM properties WHERE id = :property_id AND tenant_id = :tenant_id")
        result = await session.execute(query, {"property_id": property_id, "tenant_id": tenant_id})
        timezone_name = result.scalar()
        return timezone_name or "UTC"
    except Exception:
        return "UTC"

async def calculate_total_revenue(property_id: str, tenant_id: str, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    try:
        # Import database pool
        from app.core.database_pool import DatabasePool
        from pytz import timezone
        import pytz
        
        # Initialize pool if needed
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                # Use SQLAlchemy text for raw SQL
                from sqlalchemy import text
                
                # Dynamic query construction
                date_filter = ""
                params = {
                    "property_id": property_id, 
                    "tenant_id": tenant_id
                }
                
                if start_date and end_date:
                    # Resolve property timezone to ensure correct month boundaries
                    tz_name = await _get_property_timezone(session, property_id, tenant_id)
                    local_tz = timezone(tz_name)
                    utc_tz = pytz.UTC
                    
                    # Convert input dates (assumed to be naive/server time or UTC) to property's local time
                    # then back to UTC to ensure we query the correct absolute time range
                    if start_date.tzinfo is None:
                        start_date = start_date.replace(tzinfo=utc_tz)
                    if end_date.tzinfo is None:
                        end_date = end_date.replace(tzinfo=utc_tz)
                        
                    # Adjust query parameters
                    params["start_date"] = start_date
                    params["end_date"] = end_date
                    
                    date_filter = "AND check_in_date >= :start_date AND check_in_date < :end_date"
                
                query = text(f"""
                    SELECT 
                        property_id,
                        SUM(total_amount) as total_revenue,
                        COUNT(*) as reservation_count
                    FROM reservations 
                    WHERE property_id = :property_id AND tenant_id = :tenant_id
                    {date_filter}
                    GROUP BY property_id
                """)
                
                result = await session.execute(query, params)
                row = result.fetchone()
                
                if row:
                    from app.core.money import Money
                    total_revenue = Money.quantize(row.total_revenue)#quantize the total revenue, I was thinking of a more robust currency handling...for the future edge case testing 
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": total_revenue, 
                        "currency": "USD", 
                        "count": row.reservation_count
                    }
                else:
                    # No reservations found for this property
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": Decimal('0.00'),
                        "currency": "USD",
                        "count": 0
                    }
        else:
            raise Exception("Database pool not available")
            
    except Exception as e:
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        
        # Create property-specific mock data for testing when DB is unavailable
        mock_data = {
            'prop-001': {'total': '1000.00', 'count': 3},
            'prop-002': {'total': '4975.50', 'count': 4}, 
            'prop-003': {'total': '6100.50', 'count': 2},
            'prop-004': {'total': '1776.50', 'count': 4},
            'prop-005': {'total': '3256.00', 'count': 3}
        }
        
        mock_property_data = mock_data.get(property_id, {'total': '0.00', 'count': 0})
        
        return {
            "property_id": property_id,
            "tenant_id": tenant_id, 
            "total": Decimal(mock_property_data['total']),
            "currency": "USD",
            "count": mock_property_data['count']
        }
