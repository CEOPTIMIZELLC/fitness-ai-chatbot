from typing import List, Dict, Any, Optional
from app import db

def get_all_items(model_class) -> List[Dict[str, Any]]:
    """Generic function to get all items from a model class"""
    items = model_class.query.all()
    return [item.to_dict() for item in items]

def get_item_by_id(model_class, item_id) -> Optional[Dict[str, Any]]:
    """Generic function to get an item by ID"""
    item = db.session.get(model_class, item_id)
    if not item:
        return None
    return item.to_dict()