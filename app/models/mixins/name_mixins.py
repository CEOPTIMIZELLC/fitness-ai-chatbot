from app import db

class NameMixin:
    name = db.Column(db.String(255), unique=True, nullable=False)
    
    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name).first()