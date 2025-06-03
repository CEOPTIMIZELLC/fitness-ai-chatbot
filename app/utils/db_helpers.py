from typing import List, Dict, Any, Optional
from app import db
from sqlalchemy.exc import IntegrityError, NoResultFound

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

def get_or_create(session, model, defaults=None, **kwargs):
	"""Get or create a model instance while preserving integrity."""
	try:
		return session.query(model).filter_by(**kwargs).one(), False
	except NoResultFound:
		if defaults is not None:
			kwargs.update(defaults)
		try:
			with session.begin_nested():
				instance = model(**kwargs)
				session.add(instance)
				return instance, True
		except IntegrityError:
			return session.query(model).filter_by(**kwargs).one(), False