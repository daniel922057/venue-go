import pytest
from app.models import User, Venue, ReservationSettings
from app.models import VenueAvailability, SpecialDate, Reservation, ConflictLog # Add these
import datetime
from app import db # For db.session access if needed, though fixtures are preferred

# Tests for the User model
def test_create_user(db_session): # Use the db_session fixture
    username = "testuser"
    user = User(username=username)
    db_session.add(user)
    db_session.commit()

    retrieved_user = User.query.filter_by(username=username).first()
    assert retrieved_user is not None
    assert retrieved_user.username == username
    assert retrieved_user.id is not None

def test_user_representation(db_session):
    user = User(username="repr_user")
    db_session.add(user)
    db_session.commit()
    assert repr(user) == '<User repr_user>'

# Tests for the Venue model
def test_create_venue(db_session):
    venue_name = "Test Conference Hall"
    capacity = 100
    description = "A large hall for conferences."
    equipment = "Projector, Stage, Microphones"
    notes = "Catering available upon request."

    venue = Venue(
        name=venue_name,
        capacity=capacity,
        description=description,
        equipment_details=equipment,
        usage_notes=notes
    )
    db_session.add(venue)
    db_session.commit()

    retrieved_venue = Venue.query.filter_by(name=venue_name).first()
    assert retrieved_venue is not None
    assert retrieved_venue.name == venue_name
    assert retrieved_venue.capacity == capacity
    assert retrieved_venue.description == description
    assert retrieved_venue.equipment_details == equipment
    assert retrieved_venue.usage_notes == notes
    assert retrieved_venue.id is not None

def test_venue_representation(db_session):
    venue = Venue(name="Rep_Venue", capacity=50)
    db_session.add(venue)
    db_session.commit()
    assert repr(venue) == '<Venue Rep_Venue>'

# Tests for the ReservationSettings model
def test_create_reservation_setting(db_session):
    setting_name = "test_booking_window"
    value = "14" # Stored as string as per model design

    setting = ReservationSettings(setting_name=setting_name, value=value)
    db_session.add(setting)
    db_session.commit()

    retrieved_setting = ReservationSettings.query.filter_by(setting_name=setting_name).first()
    assert retrieved_setting is not None
    assert retrieved_setting.setting_name == setting_name
    assert retrieved_setting.value == value
    assert retrieved_setting.id is not None

def test_reservation_settings_representation(db_session):
    setting = ReservationSettings(setting_name="repr_setting", value="true")
    db_session.add(setting)
    db_session.commit()
    assert repr(setting) == '<ReservationSettings repr_setting: true>'

# Example of a test that might require the init_database fixture
# if it relies on pre-populated settings by populate_default_reservation_settings
def test_default_booking_window_setting_exists(init_database, db_session):
    # init_database ensures populate_default_reservation_settings has run
    setting = db_session.query(ReservationSettings).filter_by(setting_name='booking_window_days').first()
    assert setting is not None
    assert setting.value == "7" # Default value set in reservation_service

def test_default_slot_duration_setting_exists(init_database, db_session):
    setting = db_session.query(ReservationSettings).filter_by(setting_name='slot_duration_minutes').first()
    assert setting is not None
    assert setting.value == "60" # Default value set in reservation_service

# Tests for the VenueAvailability model
def test_create_venue_availability(db_session, init_database): # init_database ensures default venue/user can be created if needed
    # First, ensure a venue exists (or create one)
    venue = db_session.query(Venue).first()
    if not venue:
        venue = Venue(name="Test Venue for Availability", capacity=10)
        db_session.add(venue)
        db_session.commit()

    open_t = datetime.time(9, 0, 0)
    close_t = datetime.time(17, 0, 0)
    avail = VenueAvailability(
        venue_id=venue.id,
        day_of_week=1, # Tuesday
        open_time=open_t,
        close_time=close_t
    )
    db_session.add(avail)
    db_session.commit()

    retrieved_avail = db_session.query(VenueAvailability).filter_by(venue_id=venue.id, day_of_week=1).first()
    assert retrieved_avail is not None
    assert retrieved_avail.venue_id == venue.id
    assert retrieved_avail.open_time == open_t
    assert retrieved_avail.close_time == close_t
    assert retrieved_avail.venue == venue # Test relationship

def test_venue_availability_representation(db_session):
    # Requires a venue to exist for venue_id
    venue = Venue.query.filter_by(name="Rep_Venue").first() # from previous test
    if not venue: # Create if it wasn't created or if tests run in different order/isolation
        venue = Venue(id=100, name="Rep_Venue_Avail", capacity=10) # Use a distinct ID if needed
        db_session.add(venue)
        db_session.commit()
        
    avail = VenueAvailability(venue_id=venue.id, day_of_week=0, open_time=datetime.time(8,0), close_time=datetime.time(12,0))
    # Representation doesn't require commit to db_session
    assert repr(avail) == f'<VenueAvailability {venue.id} Day 0 08:00:00-12:00:00>'


# Tests for the SpecialDate model
def test_create_special_date_closed(db_session, init_database):
    venue = db_session.query(Venue).first()
    if not venue:
        venue = Venue(name="Test Venue for SpecialDate", capacity=10)
        db_session.add(venue)
        db_session.commit()

    special_day = datetime.date(2023, 12, 25)
    sd = SpecialDate(
        venue_id=venue.id,
        date=special_day,
        is_closed=True,
        description="Christmas Day - Closed"
    )
    db_session.add(sd)
    db_session.commit()

    retrieved_sd = db_session.query(SpecialDate).filter_by(venue_id=venue.id, date=special_day).first()
    assert retrieved_sd is not None
    assert retrieved_sd.is_closed is True
    assert retrieved_sd.description == "Christmas Day - Closed"
    assert retrieved_sd.venue == venue

def test_create_special_date_open_special_hours(db_session, init_database):
    venue = db_session.query(Venue).first() # Use existing or create new
    if not venue:
        venue = Venue(name="Test Venue for SpecialDate Open", capacity=10)
        db_session.add(venue)
        db_session.commit()

    special_day = datetime.date(2024, 1, 1)
    open_t = datetime.time(10,0,0)
    close_t = datetime.time(14,0,0)
    sd = SpecialDate(
        venue_id=venue.id,
        date=special_day,
        is_closed=False,
        open_time=open_t,
        close_time=close_t,
        description="New Year's Day - Special Hours"
    )
    db_session.add(sd)
    db_session.commit()
    retrieved_sd = db_session.query(SpecialDate).filter_by(venue_id=venue.id, date=special_day).first()
    assert retrieved_sd is not None
    assert retrieved_sd.is_closed is False
    assert retrieved_sd.open_time == open_t
    assert retrieved_sd.close_time == close_t

def test_special_date_representation(db_session):
    sd = SpecialDate(date=datetime.date(2024,7,4), venue_id=None, description="System Holiday")
    assert repr(sd) == '<SpecialDate 2024-07-04 Venue System-wide>'


# Tests for the Reservation model
def test_create_reservation(db_session, init_database): # init_database ensures user 1 and a venue might exist
    user = db_session.query(User).get(1) # Relies on user ID 1 from init_database
    assert user is not None, "Default user (ID 1) not found in init_database."

    venue = db_session.query(Venue).first()
    if not venue:
        venue = Venue(name="Test Venue for Reservation", capacity=10)
        db_session.add(venue)
        db_session.commit() # Commit venue first to get its ID

    start_dt = datetime.datetime(2024, 3, 10, 10, 0, 0)
    end_dt = datetime.datetime(2024, 3, 10, 12, 0, 0)
    
    reservation = Reservation(
        user_id=user.id,
        venue_id=venue.id,
        start_time=start_dt,
        end_time=end_dt,
        status="confirmed"
    )
    db_session.add(reservation)
    db_session.commit()

    retrieved_res = db_session.query(Reservation).filter_by(user_id=user.id, venue_id=venue.id).first()
    assert retrieved_res is not None
    assert retrieved_res.start_time == start_dt
    assert retrieved_res.end_time == end_dt
    assert retrieved_res.status == "confirmed"
    assert retrieved_res.user == user
    assert retrieved_res.venue == venue


# Tests for the ConflictLog model
def test_create_conflict_log(db_session, init_database):
    user = db_session.query(User).get(1)
    assert user is not None

    venue = db_session.query(Venue).first()
    if not venue:
        venue = Venue(name="Test Venue for ConflictLog", capacity=10)
        db_session.add(venue)
        db_session.commit()

    attempt_start = datetime.datetime(2024, 3, 11, 14, 0, 0)
    attempt_end = datetime.datetime(2024, 3, 11, 15, 0, 0)

    log_entry = ConflictLog(
        venue_id=venue.id,
        attempted_start_time=attempt_start,
        attempted_end_time=attempt_end,
        attempted_by_user_id=user.id
    )
    db_session.add(log_entry)
    db_session.commit()

    retrieved_log = db_session.query(ConflictLog).first()
    assert retrieved_log is not None
    assert retrieved_log.venue_id == venue.id
    assert retrieved_log.attempted_start_time == attempt_start
    assert retrieved_log.attempted_by_user_id == user.id
    assert retrieved_log.timestamp is not None
    assert retrieved_log.user == user
    assert retrieved_log.venue == venue
