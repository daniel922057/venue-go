from flask import Blueprint, request, jsonify
from app import db
from app.models import Venue, Reservation, VenueAvailability, SpecialDate
import datetime
from sqlalchemy import func # For SUM and COUNT aggregates

bp = Blueprint('stats', __name__, url_prefix='/api/stats')

@bp.route('/venue-summary', methods=['GET'])
def get_venue_summary_stats():
    # Parameters for date range (optional, defaults to all time for simplicity here)
    # A production system would likely require a date range.
    # For example: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    
    # Query to get total confirmed reservations and total hours booked per venue
    # This example calculates total hours booked directly from reservations.
    # A full utilization percentage would be more complex.

    # Calculate duration in hours: (julianday(end_time) - julianday(start_time)) * 24 for SQLite
    # For PostgreSQL: EXTRACT(EPOCH FROM (end_time - start_time)) / 3600
    # Using a simple difference for now, assuming they are datetime objects
    # For precise hour calculation, platform-specific SQL might be better or iterate in Python.
    
    # Let's calculate duration in seconds first, then sum and convert to hours.
    # This is a simplification; robust calculation depends on DB and timezones.
    
    # For SQLite, we can use strftime to calculate duration.
    # For simplicity, this example will iterate and sum in Python.
    # This is not efficient for large datasets but demonstrates the logic.

    venues = Venue.query.all()
    stats_summary = []

    for venue in venues:
        confirmed_reservations = Reservation.query.filter_by(venue_id=venue.id, status='confirmed').all()
        
        total_reservations_count = len(confirmed_reservations)
        total_hours_booked = 0
        
        for res in confirmed_reservations:
            duration_seconds = (res.end_time - res.start_time).total_seconds()
            total_hours_booked += duration_seconds / 3600
        
        stats_summary.append({
            'venue_id': venue.id,
            'venue_name': venue.name,
            'total_confirmed_reservations': total_reservations_count,
            'total_hours_booked': round(total_hours_booked, 2)
            # 'utilization_percentage': TODO (requires calculating total available hours)
        })
        
    return jsonify(stats_summary), 200

# TODO: Endpoint for conflict logs (e.g., /api/stats/conflict-logs)
# This would query the ConflictLog table.

# TODO: More detailed utilization calculation
# This would involve:
# 1. For each venue and each day in a period:
#    a. Determine its open_time and close_time from VenueAvailability or SpecialDate.
#    b. Calculate total available seconds for that day.
# 2. Sum total available seconds for the period.
# 3. Sum total booked seconds (as done above).
# 4. Utilization = (total_booked_seconds / total_available_seconds) * 100
