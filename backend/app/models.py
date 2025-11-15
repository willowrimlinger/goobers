from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import Text
from app import db

class Goober(db.Model):
    __tablename__ = 'goobers'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: so.Mapped[str] = db.mapped_column(Text)
    fingerprint: so.Mapped[str] = db.mapped_column(Text, index=True, unique=True)

    def __repr__(self):
        return f'<Goober {self.name}>'