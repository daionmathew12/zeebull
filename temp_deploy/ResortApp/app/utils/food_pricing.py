import json
from datetime import datetime, time
from typing import Optional, List, Dict

def get_food_item_price_at_time(food_item, order_time: Optional[datetime] = None, order_type: str = "dine_in") -> float:
    """
    Calculate the correct price for a food item based on time-wise pricing rules.
    If no time-wise rule matches, returns the base price (dine-in or room_service).
    """
    if not order_time:
        # Default to current time in IST (standard for the app)
        from datetime import timedelta
        order_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    
    current_time = order_time.time()
    
    # Check time-wise prices
    twp_str = getattr(food_item, 'time_wise_prices', None)
    if twp_str:
        try:
            # Handle both string and list
            if isinstance(twp_str, str):
                rules = json.loads(twp_str)
            else:
                rules = twp_str
                
            if isinstance(rules, list):
                for rule in rules:
                    from_t = datetime.strptime(rule.get('from_time'), '%H:%M').time()
                    to_t = datetime.strptime(rule.get('to_time'), '%H:%M').time()
                    
                    # Handle ranges that cross midnight
                    if from_t <= to_t:
                        if from_t <= current_time <= to_t:
                            return float(rule.get('price'))
                    else:
                        if current_time >= from_t or current_time <= to_t:
                            return float(rule.get('price'))
        except Exception as e:
            print(f"Error parsing time_wise_prices for item {food_item.id if hasattr(food_item, 'id') else 'unknown'}: {e}")
            
    # Default to base price based on order type
    if order_type == "room_service" and getattr(food_item, 'room_service_price', 0) > 0:
        return float(food_item.room_service_price)
        
    return float(food_item.price or 0.0)
