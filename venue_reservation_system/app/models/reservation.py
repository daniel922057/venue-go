from app import db

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='confirmed') # e.g., confirmed, cancelled

    def __repr__(self):
        return f'<Reservation {self.id} User {self.user_id} Venue {self.venue_id} {self.start_time}-{self.end_time}>'
