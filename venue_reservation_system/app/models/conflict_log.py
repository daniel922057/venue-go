from app import db
import datetime

class ConflictLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    attempted_start_time = db.Column(db.DateTime, nullable=False)
    attempted_end_time = db.Column(db.DateTime, nullable=False)
    attempted_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Can be null if not logged in / identifiable
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships (optional, but can be useful)
    venue = db.relationship('Venue', backref=db.backref('conflict_logs', lazy=True))
    user = db.relationship('User', backref=db.backref('conflict_attempts', lazy=True))

    def __repr__(self):
        return f'<ConflictLog Venue {self.venue_id} {self.attempted_start_time}-{self.attempted_end_time}>'
