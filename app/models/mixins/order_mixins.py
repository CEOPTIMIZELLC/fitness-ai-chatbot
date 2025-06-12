from app import db

class OrderedMixin:
    order = db.Column(
        db.Integer, 
        nullable=False)