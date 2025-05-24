from app import db

class VenueAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    # Day of the week (0=Monday, 6=Sunday)
    day_of_week = db.Column(db.Integer, nullable=False) 
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'<VenueAvailability {self.venue_id} Day {self.day_of_week} {self.open_time}-{self.close_time}>'
