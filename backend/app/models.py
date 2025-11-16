from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import Text
from app import db
import random
from datetime import datetime, timedelta

class Fingerprint(db.Model):
    __tablename__ = 'fingerprints'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    fingerprint: so.Mapped[str] = db.mapped_column(Text, index=True, unique=True)

    @classmethod
    def get_by_fingerprint(cls, fingerprint: str):
        return db.session.scalar(sa.select(cls).where(cls.fingerprint == fingerprint))
    
    @classmethod
    def get_available_fingerprints(cls):
        used_fingerprints = db.session.scalars(sa.select(cls.fingerprint)).all()
        return random.choice([num for num in range(80) if str(num) not in used_fingerprints])
    
    def __repr__(self):
        return f'<Fingerprint {self.fingerprint}>'

class Goober(db.Model):
    __tablename__ = 'goobers'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: so.Mapped[str] = db.mapped_column(Text)
    fingerprint_id: so.Mapped[int] = db.mapped_column(db.Integer, db.ForeignKey('fingerprints.id'))
    image: so.Mapped[str] = db.mapped_column(Text)

    fingerprint: so.Mapped[Fingerprint] = db.relationship('Fingerprint', backref='goobers')

    @classmethod
    def get_by_fingerprint(cls, fingerprint: Fingerprint):
        return db.session.scalar(sa.select(cls).where(Goober.fingerprint_id == fingerprint.id))
    
    @classmethod
    def get_all(cls):
        return db.session.scalars(sa.select(cls)).all()
    
    def to_json(self):
        goober_history = GooberHistory.get_by_fingerprint(self.id)
        return {
            'name': self.name,
            'fingerprint': self.fingerprint.fingerprint,
            'image': self.image,
            'last_seen': goober_history[0].timestamp if goober_history else None,
            'events': [{'event': history.event.name, 'description': history.event.description} for history in goober_history],
            'stats': [  
                {'stat_name': history.event.stat_name, 'stat_value': history.event.value_float} if history.event.type == 'float' else 
                {'stat_name': history.event.stat_name, 'stat_value': history.event.value_string} 
                for history in goober_history]
        }
    
    def go_on_adventure(self):
        history = GooberHistory.get_by_fingerprint(self.id)

        if not history or (datetime.now() - history[0].timestamp) > timedelta(seconds=30):
            event: Event = Event.get_random_event()
            db.session.add(GooberHistory(goober_id=self.id, event_id=event.id, timestamp=datetime.now()))
            db.session.commit()


    def __repr__(self):
        return f'<Goober {self.name}>'
    
class CheckIn(db.Model):
    __tablename__ = 'checkins'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    fingerprint_id: so.Mapped[int] = db.mapped_column(db.Integer, db.ForeignKey('fingerprints.id'))
    timestamp: so.Mapped[sa.DateTime] = db.mapped_column(db.DateTime, index=True)

    fingerprint: so.Mapped[Fingerprint] = db.relationship('Fingerprint', backref='checkins')

    @classmethod
    def get_latest(cls):
        return db.session.scalars(sa.select(cls).order_by(CheckIn.timestamp.desc())).first()

    def __repr__(self):
        return f'<CheckIn {self.goober.name} at {self.timestamp}>'

class Event(db.Model):
    __tablename__ = 'events'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: so.Mapped[str] = db.mapped_column(Text)
    description: so.Mapped[str] = db.mapped_column(Text)
    stat_name: so.Mapped[str] = db.mapped_column(Text)
    type: so.Mapped[str] = db.mapped_column(Text)
    value_float: so.Mapped[Optional[float]] = db.mapped_column(db.Float)
    value_string: so.Mapped[Optional[str]] = db.mapped_column(Text)

    @classmethod
    def get_all_ids(cls):
        return db.session.scalars(sa.select(cls.id)).all()
    
    @classmethod
    def get_random_event(cls):
        return random.choice(db.session.scalars(sa.select(cls)).all())
    
    def __repr__(self):
        return f'<Event {self.name}>'
      
class GooberHistory(db.Model):
    __tablename__ = 'goober_history'

    id: so.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    goober_id: so.Mapped[int] = db.mapped_column(db.Integer, db.ForeignKey('goobers.id'))
    event_id: so.Mapped[int] = db.mapped_column(db.Integer, db.ForeignKey('events.id'))
    timestamp: so.Mapped[sa.DateTime] = db.mapped_column(db.DateTime, index=True)

    goober: so.Mapped[Goober] = db.relationship('Goober', backref='goober_history')
    event: so.Mapped[Event] = db.relationship('Event', backref='goober_history')

    @classmethod
    def get_by_fingerprint(cls, goober_id: int):
        return db.session.scalars(sa.select(cls).where(cls.goober_id == goober_id).order_by(GooberHistory.timestamp.desc())).all()

    def __repr__(self):
        return f'<GooberHistory {self.goober.name} - {self.event.name} at {self.timestamp}>'