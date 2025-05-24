from flask import Blueprint, request, jsonify
from app import db
from app.models import Reservation, User, Venue, ConflictLog # Add ConflictLog
from app.services import reservation_service # Import the service
import datetime

bp = Blueprint('reservations', __name__, url_prefix='/api/reservations')

# Placeholder for user authentication - replace with actual auth later
def get_current_user_id():
    # In a real app, this would come from a session or token
    user_id = request.headers.get('X-User-Id') 
    if user_id:
        return int(user_id)
    # Fallback for testing if no header is provided.
    # Ensure User with ID 1 exists for testing, or create one.
    # This is NOT secure for production.
    user = User.query.get(1)
    if not user: # Create a dummy user for initial testing if it doesn't exist
        dummy_user = User(id=1, username='testuser')
        db.session.add(dummy_user)
        db.session.commit()
    return 1


@bp.route('/available-slots', methods=['GET'])
def query_available_slots():
    venue_id = request.args.get('venue_id', type=int)
    date_str = request.args.get('date')

    if not venue_id or not date_str:
        return jsonify({'error': 'Missing venue_id or date parameters'}), 400

    # Call the service function
    slots_or_error, status_code = reservation_service.get_available_slots(venue_id, date_str)
    
    if status_code == 200:
        return jsonify(slots_or_error), 200
    else:
        return jsonify(slots_or_error), status_code


@bp.route('/', methods=['POST'])
def create_reservation():
    data = request.get_json()
    user_id = get_current_user_id() # Placeholder for actual user ID

    if not data or not data.get('venue_id') or not data.get('start_time') or not data.get('end_time'):
        return jsonify({'error': 'Missing venue_id, start_time, or end_time'}), 400

    venue_id = data['venue_id']
    try:
        # Assuming start_time and end_time are full ISO datetime strings for reservations
        # e.g., "YYYY-MM-DDTHH:MM:SS"
        start_time_dt = datetime.datetime.fromisoformat(data['start_time'])
        end_time_dt = datetime.datetime.fromisoformat(data['end_time'])
        target_date = start_time_dt.date()
    except ValueError:
        return jsonify({'error': 'Invalid datetime format. Use ISO format YYYY-MM-DDTHH:MM:SS.'}), 400

    # Validate venue exists
    venue = Venue.query.get(venue_id)
    if not venue:
        return jsonify({'error': 'Venue not found'}), 404
    
    # Validate user exists
    user = User.query.get(user_id)
    if not user:
         # This should ideally not happen if get_current_user_id is robust
        return jsonify({'error': 'User not found'}), 404


    # Check booking window (using service logic indirectly via get_available_slots or directly)
    booking_window_days = reservation_service.get_reservation_setting('booking_window_days', reservation_service.DEFAULT_BOOKING_WINDOW_DAYS)
    current_date = datetime.date.today()
    if not (current_date <= target_date <= current_date + datetime.timedelta(days=booking_window_days)):
        return jsonify({'error': f'Date is outside the booking window.'}), 400
    
    # Check if the slot is actually available (re-check for safety and specific slot)
    # This requires comparing against venue operating hours and special dates as well.
    # The `get_available_slots` gives possible slots, but this POST confirms a specific one.
    
    # 1. Check against operating hours / special dates
    slot_duration_minutes = reservation_service.get_reservation_setting('slot_duration_minutes', reservation_service.DEFAULT_SLOT_DURATION_MINUTES)
    expected_duration = (end_time_dt - start_time_dt).total_seconds() / 60
    if not (expected_duration >= slot_duration_minutes and expected_duration % slot_duration_minutes == 0) :
        return jsonify({'error': f'Reservation duration must be a multiple of {slot_duration_minutes} minutes and at least that long.'}), 400

    # Simplified check: ensure chosen slot is within what get_available_slots would generate
    # A more robust check would re-verify against VenueAvailability/SpecialDate for the specific start/end times
    # For now, we rely on client choosing from get_available_slots and then check conflict.

    # 2. Check for conflicts
    if reservation_service.check_reservation_conflict(venue_id, start_time_dt, end_time_dt):
        # Log the conflict attempt
        conflict_log_entry = ConflictLog(
            venue_id=venue_id,
            attempted_start_time=start_time_dt,
            attempted_end_time=end_time_dt,
            attempted_by_user_id=user_id # Assuming user_id is available
        )
        db.session.add(conflict_log_entry)
        db.session.commit() # Commit the log entry
        return jsonify({'error': 'This time slot is already booked or overlaps with another reservation.'}), 409
    
    # Create and save the reservation
    new_reservation = Reservation(
        user_id=user_id,
        venue_id=venue_id,
        start_time=start_time_dt,
        end_time=end_time_dt,
        status='confirmed'
    )
    db.session.add(new_reservation)
    db.session.commit()
    
    return jsonify({
        'message': 'Reservation created successfully', 
        'id': new_reservation.id,
        'user_id': new_reservation.user_id,
        'venue_id': new_reservation.venue_id,
        'start_time': new_reservation.start_time.isoformat(),
        'end_time': new_reservation.end_time.isoformat(),
        'status': new_reservation.status
    }), 201


@bp.route('/my-reservations', methods=['GET'])
def get_my_reservations():
    user_id = get_current_user_id()
    
    # Optional query parameters for filtering (e.g., 'status', 'period')
    status_filter = request.args.get('status') # e.g., 'confirmed', 'cancelled'
    period_filter = request.args.get('period') # e.g., 'current', 'past', 'all' (default)

    query = Reservation.query.filter_by(user_id=user_id)

    if status_filter:
        query = query.filter(Reservation.status == status_filter)

    now = datetime.datetime.now()
    if period_filter == 'current':
        query = query.filter(Reservation.end_time > now, Reservation.status == 'confirmed')
    elif period_filter == 'past':
        query = query.filter(Reservation.end_time <= now)
    
    reservations = query.order_by(Reservation.start_time.desc()).all()

    return jsonify([{
        'id': r.id,
        'user_id': r.user_id,
        'venue_id': r.venue_id,
        'venue_name': r.venue.name, # Assuming backref 'venue' exists and is working
        'start_time': r.start_time.isoformat(),
        'end_time': r.end_time.isoformat(),
        'status': r.status
    } for r in reservations]), 200

@bp.route('/<int:reservation_id>/cancel', methods=['PUT']) # Changed to PUT as it's an update
def cancel_reservation(reservation_id):
    user_id = get_current_user_id()
    
    reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()

    if not reservation:
        return jsonify({'error': 'Reservation not found or you do not have permission to cancel it.'}), 404

    if reservation.status == 'cancelled':
        return jsonify({'message': 'Reservation is already cancelled.'}), 200 # Or 400 if preferred

    # Rule: Allow cancellation only if the reservation hasn't started yet.
    # This could be made more flexible (e.g., up to X hours before).
    if reservation.start_time <= datetime.datetime.now():
        return jsonify({'error': 'Cannot cancel a reservation that has already started or passed.'}), 400
    
    # Potentially add a check from ReservationSettings for cancellation window if needed

    reservation.status = 'cancelled'
    db.session.commit()
    
    return jsonify({
        'message': 'Reservation cancelled successfully.',
        'id': reservation.id,
        'status': reservation.status
    }), 200
