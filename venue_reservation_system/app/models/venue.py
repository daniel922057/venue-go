from app import db

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    equipment_details = db.Column(db.Text, nullable=True)
    usage_notes = db.Column(db.Text, nullable=True)
    
    availabilities = db.relationship('VenueAvailability', backref='venue', lazy=True, cascade="all, delete-orphan")
    special_dates = db.relationship('SpecialDate', backref='venue', lazy=True, cascade="all, delete-orphan")
    reservations = db.relationship('Reservation', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.name}>'
