from app import db

class SpecialDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=True) # Nullable if system-wide
    date = db.Column(db.Date, nullable=False)
    is_closed = db.Column(db.Boolean, default=True) # True if closed, False if special open hours
    open_time = db.Column(db.Time, nullable=True) # Only if not closed and has special hours
    close_time = db.Column(db.Time, nullable=True) # Only if not closed and has special hours
    description = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<SpecialDate {self.date} Venue {self.venue_id or "System-wide"}>'
