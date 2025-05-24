import pytest
from app.services import reservation_service
from app.models import ReservationSettings, Venue, Reservation, User, VenueAvailability, SpecialDate # Add these
import datetime # Add this
from app import db # For direct db interaction if needed, though fixtures are preferred

# Using init_database to ensure settings table is clean and defaults are populated
def test_get_reservation_setting_existing(init_database, db_session):
    # Defaults are populated by init_database fixture via populate_default_reservation_settings
    # Default booking_window_days is '7'
    val = reservation_service.get_reservation_setting('booking_window_days', '30') # Provide a different default
    assert val == 7 # Expecting integer conversion

    # Default slot_duration_minutes is '60'
    val2 = reservation_service.get_reservation_setting('slot_duration_minutes', '15')
    assert val2 == 60

def test_get_reservation_setting_non_existing_uses_default(init_database, db_session):
    val = reservation_service.get_reservation_setting('non_existent_setting', 'my_default_value')
    # The service function tries to convert to int, so if default is not int, test accordingly
    # Current implementation of get_reservation_setting attempts int conversion.
    # If we expect string default for a non-numeric setting, the service function would need adjustment
    # For now, assuming numeric settings or testing the int conversion path.
    # Let's test with an int default.
    val_int = reservation_service.get_reservation_setting('non_existent_setting_int', 123)
    assert val_int == 123

def test_get_reservation_setting_invalid_stored_value_uses_default(init_database, db_session):
    # Add a setting with a non-integer value manually
    setting = ReservationSettings(setting_name="invalid_value_setting", value="not_an_int")
    db_session.add(setting)
    db_session.commit()

    val = reservation_service.get_reservation_setting("invalid_value_setting", 999) # Default fallback
    assert val == 999

def test_populate_default_reservation_settings_no_duplicates(init_database, db_session):
    # init_database already calls populate_default_reservation_settings once.
    # Calling it again should not create duplicate settings or raise an error.
    initial_count_bw = ReservationSettings.query.filter_by(setting_name='booking_window_days').count()
    initial_count_sd = ReservationSettings.query.filter_by(setting_name='slot_duration_minutes').count()
    
    assert initial_count_bw == 1
    assert initial_count_sd == 1

    reservation_service.populate_default_reservation_settings() # Call again

    assert ReservationSettings.query.filter_by(setting_name='booking_window_days').count() == 1
    assert ReservationSettings.query.filter_by(setting_name='slot_duration_minutes').count() == 1

def test_populate_default_reservation_settings_creates_if_missing(db_session): # Deliberately not using init_database to start fresh
    # Ensure table is empty first
    db_session.query(ReservationSettings).delete()
    db_session.commit()

    assert ReservationSettings.query.count() == 0
    reservation_service.populate_default_reservation_settings()
    
    assert ReservationSettings.query.filter_by(setting_name='booking_window_days').first() is not None
    assert ReservationSettings.query.filter_by(setting_name='slot_duration_minutes').first() is not None
    assert ReservationSettings.query.filter_by(setting_name='booking_window_days').first().value == str(reservation_service.DEFAULT_BOOKING_WINDOW_DAYS)
    assert ReservationSettings.query.filter_by(setting_name='slot_duration_minutes').first().value == str(reservation_service.DEFAULT_SLOT_DURATION_MINUTES)

# Helper function to create a venue for testing if one doesn't exist
def _ensure_venue(db_session, venue_id=1, name="Test Venue Conflict", capacity=10):
    venue = db_session.query(Venue).get(venue_id)
    if not venue:
        venue = Venue(id=venue_id, name=name, capacity=capacity)
        db_session.add(venue)
        db_session.commit()
    return venue

# Helper function to create a user if one doesn't exist
def _ensure_user(db_session, user_id=1, username="test_conflict_user"):
    user = db_session.query(User).get(user_id)
    if not user:
        user = User(id=user_id, username=username)
        db_session.add(user)
        db_session.commit()
    return user


# Tests for check_reservation_conflict()
def test_check_reservation_conflict_no_conflict(init_database, db_session):
    venue = _ensure_venue(db_session)
    
    # New reservation times
    start_dt = datetime.datetime(2024, 5, 1, 10, 0, 0)
    end_dt = datetime.datetime(2024, 5, 1, 11, 0, 0)
    
    assert not reservation_service.check_reservation_conflict(venue.id, start_dt, end_dt)

def test_check_reservation_conflict_exact_match(init_database, db_session):
    venue = _ensure_venue(db_session)
    user = _ensure_user(db_session) # User ID 1 is created by init_database, this ensures it if not
    
    start_dt = datetime.datetime(2024, 5, 1, 10, 0, 0)
    end_dt = datetime.datetime(2024, 5, 1, 11, 0, 0)
    
    # Existing reservation
    existing_res = Reservation(venue_id=venue.id, user_id=user.id, start_time=start_dt, end_time=end_dt, status='confirmed')
    db_session.add(existing_res)
    db_session.commit()
    
    assert reservation_service.check_reservation_conflict(venue.id, start_dt, end_dt)

def test_check_reservation_conflict_new_overlaps_existing_start(init_database, db_session):
    venue = _ensure_venue(db_session)
    user = _ensure_user(db_session)
    
    # Existing: 10:00 - 11:00
    existing_start = datetime.datetime(2024, 5, 1, 10, 0, 0)
    existing_end = datetime.datetime(2024, 5, 1, 11, 0, 0)
    db_session.add(Reservation(venue_id=venue.id, user_id=user.id, start_time=existing_start, end_time=existing_end, status='confirmed'))
    db_session.commit()

    # New: 09:30 - 10:30 (overlaps start of existing)
    new_start = datetime.datetime(2024, 5, 1, 9, 30, 0)
    new_end = datetime.datetime(2024, 5, 1, 10, 30, 0)
    assert reservation_service.check_reservation_conflict(venue.id, new_start, new_end)

def test_check_reservation_conflict_new_overlaps_existing_end(init_database, db_session):
    venue = _ensure_venue(db_session)
    user = _ensure_user(db_session)

    # Existing: 10:00 - 11:00
    existing_start = datetime.datetime(2024, 5, 1, 10, 0, 0)
    existing_end = datetime.datetime(2024, 5, 1, 11, 0, 0)
    db_session.add(Reservation(venue_id=venue.id, user_id=user.id, start_time=existing_start, end_time=existing_end, status='confirmed'))
    db_session.commit()

    # New: 10:30 - 11:30 (overlaps end of existing)
    new_start = datetime.datetime(2024, 5, 1, 10, 30, 0)
    new_end = datetime.datetime(2024, 5, 1, 11, 30, 0)
    assert reservation_service.check_reservation_conflict(venue.id, new_start, new_end)

def test_check_reservation_conflict_new_within_existing(init_database, db_session):
    venue = _ensure_venue(db_session)
    user = _ensure_user(db_session)

    # Existing: 10:00 - 12:00
    existing_start = datetime.datetime(2024, 5, 1, 10, 0, 0)
    existing_end = datetime.datetime(2024, 5, 1, 12, 0, 0)
    db_session.add(Reservation(venue_id=venue.id, user_id=user.id, start_time=existing_start, end_time=existing_end, status='confirmed'))
    db_session.commit()

    # New: 10:30 - 11:30 (completely within existing)
    new_start = datetime.datetime(2024, 5, 1, 10, 30, 0)
    new_end = datetime.datetime(2024, 5, 1, 11, 30, 0)
    assert reservation_service.check_reservation_conflict(venue.id, new_start, new_end)

def test_check_reservation_conflict_existing_within_new(init_database, db_session):
    venue = _ensure_venue(db_session)
    user = _ensure_user(db_session)

    # Existing: 10:30 - 11:30
    existing_start = datetime.datetime(2024, 5, 1, 10, 30, 0)
    existing_end = datetime.datetime(2024, 5, 1, 11, 30, 0)
    db_session.add(Reservation(venue_id=venue.id, user_id=user.id, start_time=existing_start, end_time=existing_end, status='confirmed'))
    db_session.commit()

    # New: 10:00 - 12:00 (completely contains existing)
    new_start = datetime.datetime(2024, 5, 1, 10, 0, 0)
    new_end = datetime.datetime(2024, 5, 1, 12, 0, 0)
    assert reservation_service.check_reservation_conflict(venue.id, new_start, new_end)

def test_check_reservation_conflict_no_conflict_adjacent_before(init_database, db_session):
    venue = _ensure_venue(db_session)
    user = _ensure_user(db_session)

    # Existing: 10:00 - 11:00
    existing_start = datetime.datetime(2024, 5, 1, 10, 0, 0)
    existing_end = datetime.datetime(2024, 5, 1, 11, 0, 0)
    db_session.add(Reservation(venue_id=venue.id, user_id=user.id, start_time=existing_start, end_time=existing_end, status='confirmed'))
    db_session.commit()

    # New: 09:00 - 10:00 (ends exactly when existing starts)
    new_start = datetime.datetime(2024, 5, 1, 9, 0, 0)
    new_end = datetime.datetime(2024, 5, 1, 10, 0, 0)
    assert not reservation_service.check_reservation_conflict(venue.id, new_start, new_end)

def test_check_reservation_conflict_no_conflict_adjacent_after(init_database, db_session):
    venue = _ensure_venue(db_session)
    user = _ensure_user(db_session)

    # Existing: 10:00 - 11:00
    existing_start = datetime.datetime(2024, 5, 1, 10, 0, 0)
    existing_end = datetime.datetime(2024, 5, 1, 11, 0, 0)
    db_session.add(Reservation(venue_id=venue.id, user_id=user.id, start_time=existing_start, end_time=existing_end, status='confirmed'))
    db_session.commit()

    # New: 11:00 - 12:00 (starts exactly when existing ends)
    new_start = datetime.datetime(2024, 5, 1, 11, 0, 0)
    new_end = datetime.datetime(2024, 5, 1, 12, 0, 0)
    assert not reservation_service.check_reservation_conflict(venue.id, new_start, new_end)

def test_check_reservation_conflict_different_venue(init_database, db_session):
    venue1 = _ensure_venue(db_session, venue_id=1, name="Venue 1 Conflict")
    venue2 = _ensure_venue(db_session, venue_id=2, name="Venue 2 Conflict") # Create a second venue
    user = _ensure_user(db_session)

    start_dt = datetime.datetime(2024, 5, 1, 10, 0, 0)
    end_dt = datetime.datetime(2024, 5, 1, 11, 0, 0)
    
    # Existing reservation in Venue 1
    db_session.add(Reservation(venue_id=venue1.id, user_id=user.id, start_time=start_dt, end_time=end_dt, status='confirmed'))
    db_session.commit()
    
    # Check for conflict in Venue 2 for the same time slot
    assert not reservation_service.check_reservation_conflict(venue2.id, start_dt, end_dt)

def test_check_reservation_conflict_ignores_cancelled_reservations(init_database, db_session):
    venue = _ensure_venue(db_session)
    user = _ensure_user(db_session)
    
    start_dt = datetime.datetime(2024, 5, 1, 10, 0, 0)
    end_dt = datetime.datetime(2024, 5, 1, 11, 0, 0)
    
    # Existing CANCELLED reservation
    existing_res = Reservation(venue_id=venue.id, user_id=user.id, start_time=start_dt, end_time=end_dt, status='cancelled')
    db_session.add(existing_res)
    db_session.commit()
    
    # Should not conflict with a new reservation for the same time
    assert not reservation_service.check_reservation_conflict(venue.id, start_dt, end_dt)

# Tests for get_available_slots()
# These tests will require more setup for VenueAvailability, SpecialDate, and existing Reservations.

def test_get_available_slots_venue_not_found(init_database, db_session):
    slots, status = reservation_service.get_available_slots(999, "2024-07-01") # Non-existent venue
    assert status == 404
    assert slots['error'] == 'Venue not found.'

def test_get_available_slots_invalid_date_format(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    slots, status = reservation_service.get_available_slots(venue.id, "invalid-date")
    assert status == 400
    assert slots['error'] == 'Invalid date format. Use YYYY-MM-DD.'

def test_get_available_slots_outside_booking_window_past(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    past_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    slots, status = reservation_service.get_available_slots(venue.id, past_date)
    assert status == 400
    assert "Date is outside the booking window" in slots['error']

def test_get_available_slots_outside_booking_window_future(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    booking_window_days = reservation_service.get_reservation_setting('booking_window_days', reservation_service.DEFAULT_BOOKING_WINDOW_DAYS)
    future_date = (datetime.date.today() + datetime.timedelta(days=booking_window_days + 1)).isoformat()
    slots, status = reservation_service.get_available_slots(venue.id, future_date)
    assert status == 400
    assert "Date is outside the booking window" in slots['error']

def test_get_available_slots_venue_closed_on_special_date(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    target_date = (datetime.date.today() + datetime.timedelta(days=1))
    # Add a SpecialDate marking the venue as closed
    db_session.add(SpecialDate(venue_id=venue.id, date=target_date, is_closed=True, description="Venue Maintenance"))
    db_session.commit()

    slots, status = reservation_service.get_available_slots(venue.id, target_date.isoformat())
    assert status == 200
    assert slots == []

def test_get_available_slots_special_hours_on_special_date(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    target_date = (datetime.date.today() + datetime.timedelta(days=1))
    # Special hours: 10:00 to 12:00. Default slot duration is 60 mins.
    db_session.add(SpecialDate(
        venue_id=venue.id, date=target_date, is_closed=False, 
        open_time=datetime.time(10,0), close_time=datetime.time(12,0), 
        description="Holiday Special Hours"
    ))
    db_session.commit()

    slots, status = reservation_service.get_available_slots(venue.id, target_date.isoformat())
    assert status == 200
    assert len(slots) == 2
    assert slots[0] == {'start_time': '10:00:00', 'end_time': '11:00:00'}
    assert slots[1] == {'start_time': '11:00:00', 'end_time': '12:00:00'}

def test_get_available_slots_no_venue_availability_defined(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    # Ensure no VenueAvailability for this venue on the target day
    target_date = (datetime.date.today() + datetime.timedelta(days=2)) # A day that's likely not a weekend
    # weekday() Monday is 0 and Sunday is 6
    db_session.query(VenueAvailability).filter_by(venue_id=venue.id, day_of_week=target_date.weekday()).delete()
    db_session.commit()
    
    slots, status = reservation_service.get_available_slots(venue.id, target_date.isoformat())
    assert status == 200
    assert slots == []

def test_get_available_slots_with_regular_availability(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    target_date = (datetime.date.today() + datetime.timedelta(days=3))
    day_of_week = target_date.weekday()

    # Clear any existing availability for this day and add a specific one
    db_session.query(VenueAvailability).filter_by(venue_id=venue.id, day_of_week=day_of_week).delete()
    db_session.add(VenueAvailability(
        venue_id=venue.id, day_of_week=day_of_week, 
        open_time=datetime.time(9,0), close_time=datetime.time(12,0) # 3 hours, 60 min slots = 3 slots
    ))
    db_session.commit()

    slots, status = reservation_service.get_available_slots(venue.id, target_date.isoformat())
    assert status == 200
    assert len(slots) == 3
    assert slots[0] == {'start_time': '09:00:00', 'end_time': '10:00:00'}
    assert slots[1] == {'start_time': '10:00:00', 'end_time': '11:00:00'}
    assert slots[2] == {'start_time': '11:00:00', 'end_time': '12:00:00'}

def test_get_available_slots_with_booked_slot(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    user = _ensure_user(db_session, user_id=1) # User 1 is created by init_database
    target_date = (datetime.date.today() + datetime.timedelta(days=4))
    day_of_week = target_date.weekday()

    db_session.query(VenueAvailability).filter_by(venue_id=venue.id, day_of_week=day_of_week).delete()
    db_session.add(VenueAvailability(
        venue_id=venue.id, day_of_week=day_of_week, 
        open_time=datetime.time(9,0), close_time=datetime.time(12,0)
    ))
    # Book the 10:00 - 11:00 slot
    booked_start_dt = datetime.datetime.combine(target_date, datetime.time(10,0))
    booked_end_dt = datetime.datetime.combine(target_date, datetime.time(11,0))
    db_session.add(Reservation(
        venue_id=venue.id, user_id=user.id, 
        start_time=booked_start_dt, end_time=booked_end_dt, status='confirmed'
    ))
    db_session.commit()

    slots, status = reservation_service.get_available_slots(venue.id, target_date.isoformat())
    assert status == 200
    assert len(slots) == 2
    assert {'start_time': '09:00:00', 'end_time': '10:00:00'} in slots
    assert {'start_time': '11:00:00', 'end_time': '12:00:00'} in slots
    assert {'start_time': '10:00:00', 'end_time': '11:00:00'} not in slots 

def test_get_available_slots_custom_slot_duration(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    target_date = (datetime.date.today() + datetime.timedelta(days=5))
    day_of_week = target_date.weekday()

    # Set slot duration to 30 minutes
    setting = db_session.query(ReservationSettings).filter_by(setting_name='slot_duration_minutes').first()
    setting.value = "30" 
    db_session.commit()

    db_session.query(VenueAvailability).filter_by(venue_id=venue.id, day_of_week=day_of_week).delete()
    db_session.add(VenueAvailability(
        venue_id=venue.id, day_of_week=day_of_week, 
        open_time=datetime.time(9,0), close_time=datetime.time(10,0) # 1 hour open = 2 slots of 30 mins
    ))
    db_session.commit()

    slots, status = reservation_service.get_available_slots(venue.id, target_date.isoformat())
    assert status == 200
    assert len(slots) == 2
    assert slots[0] == {'start_time': '09:00:00', 'end_time': '09:30:00'}
    assert slots[1] == {'start_time': '09:30:00', 'end_time': '10:00:00'}

    # Reset slot duration to default for other tests (or rely on init_database)
    setting.value = str(reservation_service.DEFAULT_SLOT_DURATION_MINUTES)
    db_session.commit()


def test_get_available_slots_no_slots_if_open_time_equals_close_time(init_database, db_session):
    venue = _ensure_venue(db_session, venue_id=1)
    target_date = (datetime.date.today() + datetime.timedelta(days=1))
    day_of_week = target_date.weekday()
    db_session.query(VenueAvailability).filter_by(venue_id=venue.id, day_of_week=day_of_week).delete()
    db_session.add(VenueAvailability(
        venue_id=venue.id, day_of_week=day_of_week,
        open_time=datetime.time(9,0), close_time=datetime.time(9,0)
    ))
    db_session.commit()
    slots, status = reservation_service.get_available_slots(venue.id, target_date.isoformat())
    assert status == 200
    assert slots == []

def test_get_available_slots_no_slots_if_open_time_after_close_time(init_database, db_session):
    # Note: Model or route validation should ideally prevent this data state.
    # This test checks service robustness.
    venue = _ensure_venue(db_session, venue_id=1)
    target_date = (datetime.date.today() + datetime.timedelta(days=1))
    day_of_week = target_date.weekday()
    db_session.query(VenueAvailability).filter_by(venue_id=venue.id, day_of_week=day_of_week).delete()
    db_session.add(VenueAvailability(
        venue_id=venue.id, day_of_week=day_of_week,
        open_time=datetime.time(10,0), close_time=datetime.time(9,0)
    ))
    db_session.commit()
    slots, status = reservation_service.get_available_slots(venue.id, target_date.isoformat())
    assert status == 200
    assert slots == []
