from app import db
from app.models import Venue, VenueAvailability, SpecialDate, Reservation, ReservationSettings
import datetime
from sqlalchemy import and_, or_

DEFAULT_SLOT_DURATION_MINUTES = 60
DEFAULT_BOOKING_WINDOW_DAYS = 7

def get_reservation_setting(setting_name, default_value):
    setting = ReservationSettings.query.filter_by(setting_name=setting_name).first()
    if setting:
        # Assuming value is stored appropriately (e.g., integer for these settings)
        try:
            return int(setting.value)
        except ValueError:
            return default_value # Fallback if parsing fails
    return default_value

def get_available_slots(venue_id, target_date_str):
    try:
        target_date = datetime.date.fromisoformat(target_date_str)
    except ValueError:
        return {'error': 'Invalid date format. Use YYYY-MM-DD.'}, 400

    venue = Venue.query.get(venue_id)
    if not venue:
        return {'error': 'Venue not found.'}, 404

    # Check booking window
    booking_window_days = get_reservation_setting('booking_window_days', DEFAULT_BOOKING_WINDOW_DAYS)
    current_date = datetime.date.today()
    if not (current_date <= target_date <= current_date + datetime.timedelta(days=booking_window_days)):
        return {'error': f'Date is outside the booking window (today to {booking_window_days} days in advance).'}, 400

    slot_duration_minutes = get_reservation_setting('slot_duration_minutes', DEFAULT_SLOT_DURATION_MINUTES)
    
    applicable_open_time = None
    applicable_close_time = None
    
    # 1. Check SpecialDate for the venue or system-wide (system-wide not implemented yet, focusing on venue-specific)
    special_day_entry = SpecialDate.query.filter_by(venue_id=venue.id, date=target_date).first()
    if special_day_entry:
        if special_day_entry.is_closed:
            return [], 200 # Venue is closed on this special date
        if special_day_entry.open_time and special_day_entry.close_time:
            applicable_open_time = special_day_entry.open_time
            applicable_close_time = special_day_entry.close_time
    
    # 2. If no special date applies, check VenueAvailability
    if applicable_open_time is None:
        day_of_week = target_date.weekday() # Monday is 0 and Sunday is 6
        availability_entry = VenueAvailability.query.filter_by(
            venue_id=venue.id, 
            day_of_week=day_of_week
        ).first() # Assuming one entry per day_of_week for simplicity, or take the first if multiple
        
        if not availability_entry:
            return [], 200 # No availability defined for this day
        
        applicable_open_time = availability_entry.open_time
        applicable_close_time = availability_entry.close_time

    if not applicable_open_time or not applicable_close_time:
            return [], 200 # Should not happen if data is consistent, but as a safeguard

    # 3. Generate potential slots
    potential_slots = []
    current_slot_start_dt = datetime.datetime.combine(target_date, applicable_open_time)
    final_close_dt = datetime.datetime.combine(target_date, applicable_close_time)
    slot_delta = datetime.timedelta(minutes=slot_duration_minutes)

    while current_slot_start_dt + slot_delta <= final_close_dt:
        slot_end_dt = current_slot_start_dt + slot_delta
        potential_slots.append({
            'start_time': current_slot_start_dt.time().isoformat(),
            'end_time': slot_end_dt.time().isoformat()
        })
        current_slot_start_dt = slot_end_dt
        
    if not potential_slots:
        return [], 200

    # 4. Filter out booked slots
    # Convert potential_slots times to full datetimes for easier comparison with Reservation datetimes
    
    reservations_on_date = Reservation.query.filter(
        Reservation.venue_id == venue.id,
        Reservation.status == 'confirmed', # Only consider confirmed reservations
        db.func.date(Reservation.start_time) == target_date
    ).all()

    available_slots = []
    for slot in potential_slots:
        slot_start_dt = datetime.datetime.combine(target_date, datetime.time.fromisoformat(slot['start_time']))
        slot_end_dt = datetime.datetime.combine(target_date, datetime.time.fromisoformat(slot['end_time']))
        
        is_booked = False
        for res in reservations_on_date:
            # Check for overlap: (ResStart < SlotEnd) and (ResEnd > SlotStart)
            if res.start_time < slot_end_dt and res.end_time > slot_start_dt:
                is_booked = True
                break
        if not is_booked:
            available_slots.append(slot)
            
    return available_slots, 200

def check_reservation_conflict(venue_id, start_time_dt, end_time_dt):
    # Check for existing reservations that conflict with the given timeslot
    conflicting_reservations = Reservation.query.filter(
        Reservation.venue_id == venue_id,
        Reservation.status == 'confirmed',
        # (ExistingStart < NewEnd) AND (ExistingEnd > NewStart)
        Reservation.start_time < end_time_dt,
        Reservation.end_time > start_time_dt
    ).count()
    return conflicting_reservations > 0

def populate_default_reservation_settings():
    default_settings = {
        'booking_window_days': str(DEFAULT_BOOKING_WINDOW_DAYS),
        'slot_duration_minutes': str(DEFAULT_SLOT_DURATION_MINUTES)
    }
    for name, value in default_settings.items():
        setting = ReservationSettings.query.filter_by(setting_name=name).first()
        if not setting:
            new_setting = ReservationSettings(setting_name=name, value=value)
            db.session.add(new_setting)
    db.session.commit()
