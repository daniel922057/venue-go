from flask import Blueprint, jsonify, render_template, request, flash, redirect, url_for
from app.models import Venue, Reservation, User, ConflictLog # Added Reservation, User, ConflictLog
from app.services import reservation_service # Added reservation_service
from app import db
import datetime # Added datetime

bp = Blueprint('main', __name__)

# ... (home_page, list_venues_ui routes remain the same) ...
@bp.route('/')
def home_page():
    return render_template('home.html', title="Home")

@bp.route('/ui/venues', methods=['GET'])
def list_venues_ui():
    try:
        venues_data = Venue.query.order_by(Venue.name).all()
        return render_template('venues.html', venues=venues_data, title="All Venues")
    except Exception as e:
        flash(f"Error fetching venues: {str(e)}", "error")
        return render_template('venues.html', venues=[], title="All Venues")


@bp.route('/ui/venues/<int:venue_id>', methods=['GET'])
def view_venue_ui(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    selected_date_str = request.args.get('date')
    available_slots = None
    error_message = None

    if selected_date_str:
        try:
            # Validate date format early
            datetime.date.fromisoformat(selected_date_str)
            slots_or_error, status_code = reservation_service.get_available_slots(venue_id, selected_date_str)
            if status_code == 200:
                available_slots = slots_or_error
            else:
                error_message = slots_or_error.get('error', 'Could not fetch slots.')
        except ValueError:
            error_message = "Invalid date format. Please use YYYY-MM-DD."
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
    else:
        # Default to today's date or no date selected
        selected_date_str = datetime.date.today().isoformat()


    return render_template('venue_detail.html', 
                           venue=venue, 
                           selected_date=selected_date_str, 
                           available_slots=available_slots,
                           error_message=error_message,
                           title=venue.name)

@bp.route('/ui/make-reservation', methods=['POST'])
def make_reservation_ui():
    # This is a simplified version of the API endpoint for reservation creation
    # It assumes user_id=1 for now (matching the placeholder in the form)
    venue_id = request.form.get('venue_id', type=int)
    start_time_str = request.form.get('start_time') # Expected format: YYYY-MM-DDTHH:MM:SS
    end_time_str = request.form.get('end_time')   # Expected format: YYYY-MM-DDTHH:MM:SS
    user_id_form = request.form.get('user_id', type=int, default=1) # Get user_id from form

    # Basic validation
    if not all([venue_id, start_time_str, end_time_str, user_id_form]):
        flash("Missing data for reservation.", "error")
        return redirect(request.referrer or url_for('main.home_page'))

    try:
        start_time_dt = datetime.datetime.fromisoformat(start_time_str)
        end_time_dt = datetime.datetime.fromisoformat(end_time_str)
    except ValueError:
        flash("Invalid date/time format for reservation.", "error")
        return redirect(request.referrer or url_for('main.view_venue_ui', venue_id=venue_id))
    
    # Ensure User exists (especially for the hardcoded/default user ID)
    user = User.query.get(user_id_form)
    if not user:
        # Try creating the default user if it's user_id 1 and doesn't exist
        if user_id_form == 1:
            user = User(id=1, username=f'testuser{user_id_form}')
            db.session.add(user)
            # db.session.commit() # Commit separately or along with reservation
        else:
            flash(f"User with ID {user_id_form} not found.", "error")
            return redirect(request.referrer or url_for('main.view_venue_ui', venue_id=venue_id))
    
    # Check for conflicts (re-using service logic)
    if reservation_service.check_reservation_conflict(venue_id, start_time_dt, end_time_dt):
        # Log conflict (optional here, as API does it, but good for UI feedback if direct)
        conflict_log = ConflictLog( # Assuming ConflictLog is accessible
            venue_id=venue_id, 
            attempted_start_time=start_time_dt, 
            attempted_end_time=end_time_dt,
            attempted_by_user_id=user_id_form
        )
        db.session.add(conflict_log)
        db.session.commit()
        flash("This time slot is already booked or overlaps with another reservation.", "error")
    else:
        # Create reservation
        new_reservation = Reservation(
            user_id=user_id_form,
            venue_id=venue_id,
            start_time=start_time_dt,
            end_time=end_time_dt,
            status='confirmed'
        )
        db.session.add(new_reservation)
        db.session.commit()
        flash("Reservation successful!", "success")
        # Redirect to a confirmation page or back to venue detail for the same date
        return redirect(url_for('main.view_venue_ui', venue_id=venue_id, date=start_time_dt.date().isoformat()))

    return redirect(url_for('main.view_venue_ui', venue_id=venue_id, date=start_time_dt.date().isoformat()))
