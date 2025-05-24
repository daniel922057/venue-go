from flask import Blueprint, request, jsonify
from app import db
from app.models import Venue, VenueAvailability, SpecialDate # Make sure all are listed
import datetime # For date/time conversions

bp = Blueprint('venues', __name__, url_prefix='/api/venues')

# Create a new venue
@bp.route('/', methods=['POST'])
def create_venue():
    data = request.get_json()
    if not data or not data.get('name') or data.get('capacity') is None:
        return jsonify({'error': 'Missing name or capacity'}), 400
    
    new_venue = Venue(
        name=data['name'],
        capacity=data['capacity'],
        description=data.get('description'),
        equipment_details=data.get('equipment_details'),
        usage_notes=data.get('usage_notes')
    )
    db.session.add(new_venue)
    db.session.commit()
    return jsonify({'message': 'Venue created successfully', 'id': new_venue.id}), 201

# Get all venues
@bp.route('/', methods=['GET'])
def get_venues():
    venues = Venue.query.all()
    return jsonify([{
        'id': v.id,
        'name': v.name,
        'capacity': v.capacity,
        'description': v.description,
        'equipment_details': v.equipment_details,
        'usage_notes': v.usage_notes
    } for v in venues]), 200

# Get a specific venue by ID
@bp.route('/<int:venue_id>', methods=['GET'])
def get_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    return jsonify({
        'id': venue.id,
        'name': venue.name,
        'capacity': venue.capacity,
        'description': venue.description,
        'equipment_details': venue.equipment_details,
        'usage_notes': venue.usage_notes
    }), 200

# Update an existing venue
@bp.route('/<int:venue_id>', methods=['PUT'])
def update_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    venue.name = data.get('name', venue.name)
    venue.capacity = data.get('capacity', venue.capacity)
    venue.description = data.get('description', venue.description)
    venue.equipment_details = data.get('equipment_details', venue.equipment_details)
    venue.usage_notes = data.get('usage_notes', venue.usage_notes)
    
    db.session.commit()
    return jsonify({'message': 'Venue updated successfully'}), 200

# Delete a venue (or mark as inactive - for now, direct delete)
# Consider soft delete later if needed.
@bp.route('/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    db.session.delete(venue)
    db.session.commit()
    return jsonify({'message': 'Venue deleted successfully'}), 200


# --- VenueAvailability Routes ---

@bp.route('/<int:venue_id>/availability', methods=['POST'])
def add_venue_availability(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    data = request.get_json()

    if not data or data.get('day_of_week') is None or not data.get('open_time') or not data.get('close_time'):
        return jsonify({'error': 'Missing day_of_week, open_time, or close_time'}), 400

    try:
        open_time = datetime.time.fromisoformat(data['open_time'])
        close_time = datetime.time.fromisoformat(data['close_time'])
    except ValueError:
        return jsonify({'error': 'Invalid time format. Use HH:MM:SS'}), 400

    if open_time >= close_time:
        return jsonify({'error': 'Open time must be before close time'}), 400
    
    # Check for overlapping availability for the same day
    existing_availability = VenueAvailability.query.filter_by(venue_id=venue_id, day_of_week=data['day_of_week']).filter(
        ((VenueAvailability.open_time <= open_time) & (VenueAvailability.close_time > open_time)) |
        ((VenueAvailability.open_time < close_time) & (VenueAvailability.close_time >= close_time)) |
        ((VenueAvailability.open_time >= open_time) & (VenueAvailability.close_time <= close_time))
    ).first()

    if existing_availability:
        return jsonify({'error': 'Overlapping availability exists for this day and time'}), 409

    availability = VenueAvailability(
        venue_id=venue.id,
        day_of_week=data['day_of_week'],
        open_time=open_time,
        close_time=close_time
    )
    db.session.add(availability)
    db.session.commit()
    return jsonify({'message': 'Venue availability added', 'id': availability.id}), 201

@bp.route('/<int:venue_id>/availability', methods=['GET'])
def get_venue_availability(venue_id):
    Venue.query.get_or_404(venue_id) # Ensure venue exists
    availabilities = VenueAvailability.query.filter_by(venue_id=venue_id).order_by(VenueAvailability.day_of_week, VenueAvailability.open_time).all()
    return jsonify([{
        'id': avail.id,
        'day_of_week': avail.day_of_week,
        'open_time': avail.open_time.isoformat(),
        'close_time': avail.close_time.isoformat()
    } for avail in availabilities]), 200

@bp.route('/availability/<int:availability_id>', methods=['PUT'])
def update_venue_availability(availability_id):
    availability = VenueAvailability.query.get_or_404(availability_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        if 'open_time' in data:
            availability.open_time = datetime.time.fromisoformat(data['open_time'])
        if 'close_time' in data:
            availability.close_time = datetime.time.fromisoformat(data['close_time'])
    except ValueError:
        return jsonify({'error': 'Invalid time format. Use HH:MM:SS'}), 400
    
    if availability.open_time and availability.close_time and availability.open_time >= availability.close_time:
            return jsonify({'error': 'Open time must be before close time'}), 400

    availability.day_of_week = data.get('day_of_week', availability.day_of_week)
    
    # Add overlap check here as well if day_of_week, open_time or close_time changes
    # For brevity, this example omits re-checking for overlaps on PUT, but it's important for production.

    db.session.commit()
    return jsonify({'message': 'Venue availability updated'}), 200

@bp.route('/availability/<int:availability_id>', methods=['DELETE'])
def delete_venue_availability(availability_id):
    availability = VenueAvailability.query.get_or_404(availability_id)
    db.session.delete(availability)
    db.session.commit()
    return jsonify({'message': 'Venue availability deleted'}), 200


# --- SpecialDate Routes ---

@bp.route('/<int:venue_id>/special-dates', methods=['POST'])
def add_special_date(venue_id):
    Venue.query.get_or_404(venue_id) # Ensure venue exists
    data = request.get_json()

    if not data or not data.get('date') or data.get('is_closed') is None:
        return jsonify({'error': 'Missing date or is_closed status'}), 400

    try:
        date = datetime.date.fromisoformat(data['date'])
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    open_time = None
    close_time = None
    if not data['is_closed']:
        if not data.get('open_time') or not data.get('close_time'):
            return jsonify({'error': 'open_time and close_time required if not closed'}), 400
        try:
            open_time = datetime.time.fromisoformat(data['open_time'])
            close_time = datetime.time.fromisoformat(data['close_time'])
            if open_time >= close_time:
                return jsonify({'error': 'Open time must be before close time'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid time format for open/close times. Use HH:MM:SS'}), 400
    
    special_date = SpecialDate(
        venue_id=venue_id,
        date=date,
        is_closed=data['is_closed'],
        open_time=open_time,
        close_time=close_time,
        description=data.get('description')
    )
    db.session.add(special_date)
    db.session.commit()
    return jsonify({'message': 'Special date added', 'id': special_date.id}), 201

@bp.route('/<int:venue_id>/special-dates', methods=['GET'])
def get_special_dates(venue_id):
    Venue.query.get_or_404(venue_id) # Ensure venue exists
    special_dates = SpecialDate.query.filter_by(venue_id=venue_id).order_by(SpecialDate.date).all()
    return jsonify([{
        'id': sd.id,
        'date': sd.date.isoformat(),
        'is_closed': sd.is_closed,
        'open_time': sd.open_time.isoformat() if sd.open_time else None,
        'close_time': sd.close_time.isoformat() if sd.close_time else None,
        'description': sd.description
    } for sd in special_dates]), 200

@bp.route('/special-dates/<int:special_date_id>', methods=['PUT']) # Changed path for clarity
def update_special_date(special_date_id):
    special_date = SpecialDate.query.get_or_404(special_date_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'date' in data:
        try:
            special_date.date = datetime.date.fromisoformat(data['date'])
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    special_date.is_closed = data.get('is_closed', special_date.is_closed)
    special_date.description = data.get('description', special_date.description)

    open_time = special_date.open_time
    close_time = special_date.close_time

    if not special_date.is_closed:
        if 'open_time' in data:
            try:
                open_time = datetime.time.fromisoformat(data['open_time'])
            except ValueError:
                return jsonify({'error': 'Invalid open_time format. Use HH:MM:SS'}), 400
        if 'close_time' in data:
            try:
                close_time = datetime.time.fromisoformat(data['close_time'])
            except ValueError:
                return jsonify({'error': 'Invalid close_time format. Use HH:MM:SS'}), 400
        
        if not open_time or not close_time:
                return jsonify({'error': 'open_time and close_time required if not closed'}), 400
        if open_time >= close_time:
            return jsonify({'error': 'Open time must be before close time'}), 400
        special_date.open_time = open_time
        special_date.close_time = close_time
    else:
        special_date.open_time = None
        special_date.close_time = None
        
    db.session.commit()
    return jsonify({'message': 'Special date updated'}), 200

@bp.route('/special-dates/<int:special_date_id>', methods=['DELETE']) # Changed path for clarity
def delete_special_date(special_date_id):
    special_date = SpecialDate.query.get_or_404(special_date_id)
    db.session.delete(special_date)
    db.session.commit()
    return jsonify({'message': 'Special date deleted'}), 200
