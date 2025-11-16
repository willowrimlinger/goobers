from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import Text
from app import db

class Fingerprint(db.Model):
    __tablename__ = 'fingerprints'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    fingerprint: so.Mapped[str] = db.mapped_column(Text, index=True, unique=True)

    def __repr__(self):
        return f'<Fingerprint {self.fingerprint}>'

class Goober(db.Model):
    __tablename__ = 'goobers'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: so.Mapped[str] = db.mapped_column(Text)
    fingerprint_id: so.Mapped[int] = db.mapped_column(db.Integer, db.ForeignKey('fingerprints.id'))

    fingerprint: so.Mapped[Fingerprint] = db.relationship('Fingerprint', backref='goobers')

    def __repr__(self):
        return f'<Goober {self.name}>'
    
class CheckIn(db.Model):
    __tablename__ = 'checkins'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    fingerprint_id: so.Mapped[int] = db.mapped_column(db.Integer, db.ForeignKey('fingerprints.id'))
    timestamp: so.Mapped[sa.DateTime] = db.mapped_column(db.DateTime, index=True)

    fingerprint: so.Mapped[Fingerprint] = db.relationship('Fingerprint', backref='checkins')

    def __repr__(self):
        return f'<CheckIn {self.goober.name} at {self.timestamp}>'

class Event(db.Model):
    __tablename__ = 'events'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: so.Mapped[str] = db.mapped_column(Text)
    description: so.Mapped[str] = db.mapped_column(Text)
    name: so.Mapped[str] = db.mapped_column(Text)
    type: so.Mapped[str] = db.mapped_column(Text)
    value_float: so.Mapped[Optional[float]] = db.mapped_column(db.Float)
    value_string: so.Mapped[Optional[str]] = db.mapped_column(Text)
    
    def __repr__(self):
        return f'<Event {self.name} at {self.timestamp}>'
      
class GooberHistory(db.Model):
    __tablename__ = 'goober_history'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    goober_id: so.Mapped[int] = db.mapped_column(db.Integer, db.ForeignKey('goobers.id'))
    event_id: so.Mapped[int] = db.mapped_column(db.Integer, db.ForeignKey('events.id'))
    timestamp: so.Mapped[sa.DateTime] = db.mapped_column(db.DateTime, index=True)

    goober: so.Mapped[Goober] = db.relationship('Goober', backref='goober_history')
    event: so.Mapped[Event] = db.relationship('Event', backref='goober_history')

    def __repr__(self):
        return f'<GooberHistory {self.goober.name} - {self.event.name} at {self.timestamp}>'