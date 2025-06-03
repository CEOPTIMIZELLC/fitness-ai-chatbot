from sqlalchemy.ext.declarative import declared_attr

class TableNameMixin:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()