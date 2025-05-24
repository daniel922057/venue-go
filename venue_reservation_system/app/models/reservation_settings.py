from app import db

class ReservationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Name of the setting, e.g., 'booking_window_days', 'slot_duration_minutes'
    setting_name = db.Column(db.String(50), unique=True, nullable=False) 
    value = db.Column(db.String(100), nullable=False) # Store value as string, parse as needed

    def __repr__(self):
        return f'<ReservationSettings {self.setting_name}: {self.value}>'
