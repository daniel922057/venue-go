import pytest
import json
from app.models import Venue, VenueAvailability, SpecialDate, Reservation, User, ConflictLog, ReservationSettings # Add these
import datetime
from app.services.reservation_service import DEFAULT_BOOKING_WINDOW_DAYS, DEFAULT_SLOT_DURATION_MINUTES # For reference

# --- Venue CRUD Tests ---
def test_create_venue_api(client, init_database, db_session): # Use client and init_database
    data = {
        "name": "API Test Venue",
        "capacity": 75,
        "description": "Venue created via API test",
        "equipment_details": "API Test Equipment",
        "usage_notes": "API Test Notes"
    }
    response = client.post('/api/venues/', json=data)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == 'Venue created successfully'
    assert 'id' in json_data
    
    venue = db_session.query(Venue).get(json_data['id'])
    assert venue is not None
    assert venue.name == data['name']

def test_get_all_venues_api(client, init_database, db_session):
    # Create a venue first using the API for a more integrated test
    client.post('/api/venues/', json={"name": "Venue Alpha", "capacity": 10})
    client.post('/api/venues/', json={"name": "Venue Beta", "capacity": 20})

    response = client.get('/api/venues/')
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    # init_database might create a default venue if we add that to conftest, adjust count if so
    # For now, assuming only the two created here (or more if other tests added some and DB isn't perfectly clean for this exact call)
    # A better check would be for the names of the venues we just created.
    names = [v['name'] for v in json_data]
    assert "Venue Alpha" in names
    assert "Venue Beta" in names

def test_get_specific_venue_api(client, init_database, db_session):
    res = client.post('/api/venues/', json={"name": "Specific Venue", "capacity": 5})
    venue_id = res.get_json()['id']

    response = client.get(f'/api/venues/{venue_id}')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['name'] == "Specific Venue"
    assert json_data['id'] == venue_id

def test_get_specific_venue_not_found_api(client, init_database):
    response = client.get('/api/venues/9999') # Non-existent ID
    assert response.status_code == 404

def test_update_venue_api(client, init_database, db_session):
    res = client.post('/api/venues/', json={"name": "Old Name", "capacity": 10})
    venue_id = res.get_json()['id']

    update_data = {"name": "New Updated Name", "capacity": 15}
    response = client.put(f'/api/venues/{venue_id}', json=update_data)
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Venue updated successfully'

    updated_venue = db_session.query(Venue).get(venue_id)
    assert updated_venue.name == "New Updated Name"
    assert updated_venue.capacity == 15

def test_delete_venue_api(client, init_database, db_session):
    res = client.post('/api/venues/', json={"name": "To Be Deleted", "capacity": 10})
    venue_id = res.get_json()['id']

    response = client.delete(f'/api/venues/{venue_id}')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Venue deleted successfully'
    
    deleted_venue = db_session.query(Venue).get(venue_id)
    assert deleted_venue is None


# --- VenueAvailability API Tests ---
def test_add_venue_availability_api(client, init_database, db_session):
    res = client.post('/api/venues/', json={"name": "Venue For Avail", "capacity": 10}) # Create venue
    venue_id = res.get_json()['id']

    avail_data = {"day_of_week": 0, "open_time": "09:00:00", "close_time": "17:00:00"}
    response = client.post(f'/api/venues/{venue_id}/availability', json=avail_data)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == 'Venue availability added'
    assert 'id' in json_data

    avail_entry = db_session.query(VenueAvailability).get(json_data['id'])
    assert avail_entry is not None
    assert avail_entry.day_of_week == 0
    assert avail_entry.open_time == datetime.time(9,0)

def test_get_venue_availability_api(client, init_database, db_session):
    res_venue = client.post('/api/venues/', json={"name": "Venue Avail Get", "capacity": 10})
    venue_id = res_venue.get_json()['id']
    client.post(f'/api/venues/{venue_id}/availability', json={"day_of_week": 1, "open_time": "10:00:00", "close_time": "16:00:00"})
    
    response = client.get(f'/api/venues/{venue_id}/availability')
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) >= 1 # Can be more if other tests added some for same venue or default data
    assert json_data[0]['day_of_week'] == 1
    assert json_data[0]['open_time'] == "10:00:00"


# --- SpecialDate API Tests ---
def test_add_special_date_api(client, init_database, db_session):
    res_venue = client.post('/api/venues/', json={"name": "Venue For SpecialDate", "capacity": 10})
    venue_id = res_venue.get_json()['id']
    
    today_str = datetime.date.today().isoformat()
    sd_data = {
        "date": today_str, 
        "is_closed": True, 
        "description": "API Test Holiday"
    }
    response = client.post(f'/api/venues/{venue_id}/special-dates', json=sd_data)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == 'Special date added'
    
    sd_entry = db_session.query(SpecialDate).filter_by(venue_id=venue_id, date=datetime.date.today()).first()
    assert sd_entry is not None
    assert sd_entry.description == "API Test Holiday"

def test_get_special_dates_api(client, init_database, db_session):
    res_venue = client.post('/api/venues/', json={"name": "Venue SpecialDate Get", "capacity": 10})
    venue_id = res_venue.get_json()['id']
    
    date1_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    client.post(f'/api/venues/{venue_id}/special-dates', json={"date": date1_str, "is_closed": True})

    response = client.get(f'/api/venues/{venue_id}/special-dates')
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) >= 1
    assert json_data[0]['date'] == date1_str

# Note: PUT and DELETE for VenueAvailability and SpecialDate by their own IDs 
# (e.g. /api/venues/availability/<avail_id>) can also be added.
# For brevity, focusing on main CRUD and creation/listing for sub-entities here.

# --- Reservation API Tests ---

def test_query_available_slots_api(client, init_database, db_session):
    # Setup: Create a venue and its availability
    venue_res = client.post('/api/venues/', json={"name": "Slot Test Venue", "capacity": 10})
    venue_id = venue_res.get_json()['id']
    
    target_date_obj = datetime.date.today() + datetime.timedelta(days=1)
    target_date_str = target_date_obj.isoformat()
    day_of_week = target_date_obj.weekday()

    avail_data = {"day_of_week": day_of_week, "open_time": "09:00:00", "close_time": "12:00:00"} # 3 slots of 1hr
    client.post(f'/api/venues/{venue_id}/availability', json=avail_data)

    response = client.get(f'/api/reservations/available-slots?venue_id={venue_id}&date={target_date_str}')
    assert response.status_code == 200
    slots = response.get_json()
    assert isinstance(slots, list)
    assert len(slots) == 3 # Expect 3 one-hour slots from 9 to 12
    assert slots[0]['start_time'] == '09:00:00'

def test_create_reservation_api_successful(client, init_database, db_session):
    # User ID 1 is created by init_database fixture
    headers = {'X-User-Id': '1'} # Simulate user 1 making the request

    venue_res = client.post('/api/venues/', json={"name": "Reserve Venue", "capacity": 10})
    venue_id = venue_res.get_json()['id']
    
    target_date_obj = datetime.date.today() + datetime.timedelta(days=1)
    target_date_str = target_date_obj.isoformat()
    day_of_week = target_date_obj.weekday()
    client.post(f'/api/venues/{venue_id}/availability', json={"day_of_week": day_of_week, "open_time": "10:00:00", "close_time": "11:00:00"})

    reservation_data = {
        "venue_id": venue_id,
        "start_time": f"{target_date_str}T10:00:00",
        "end_time": f"{target_date_str}T11:00:00"
    }
    response = client.post('/api/reservations/', json=reservation_data, headers=headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == 'Reservation created successfully'
    assert json_data['venue_id'] == venue_id
    assert json_data['user_id'] == 1 # Assuming user_id from header worked

    res_entry = db_session.query(Reservation).get(json_data['id'])
    assert res_entry is not None
    assert res_entry.status == 'confirmed'

def test_create_reservation_api_conflict(client, init_database, db_session):
    headers = {'X-User-Id': '1'}
    venue_res = client.post('/api/venues/', json={"name": "Conflict Test Venue", "capacity": 10})
    venue_id = venue_res.get_json()['id']
    
    target_date_obj = datetime.date.today() + datetime.timedelta(days=1)
    target_date_str = target_date_obj.isoformat()
    day_of_week = target_date_obj.weekday()
    client.post(f'/api/venues/{venue_id}/availability', json={"day_of_week": day_of_week, "open_time": "10:00:00", "close_time": "11:00:00"})

    reservation_data = {"venue_id": venue_id, "start_time": f"{target_date_str}T10:00:00", "end_time": f"{target_date_str}T11:00:00"}
    
    # First reservation - should succeed
    client.post('/api/reservations/', json=reservation_data, headers=headers)
    
    # Second reservation for the same slot - should conflict
    response_conflict = client.post('/api/reservations/', json=reservation_data, headers=headers)
    assert response_conflict.status_code == 409
    assert "overlaps with another reservation" in response_conflict.get_json()['error']
    
    # Check ConflictLog
    assert db_session.query(ConflictLog).filter_by(venue_id=venue_id).count() == 1


def test_get_my_reservations_api(client, init_database, db_session):
    user_id = 1 # Default user from init_database
    headers = {'X-User-Id': str(user_id)}

    venue_res = client.post('/api/venues/', json={"name": "MyRes Venue", "capacity": 5})
    venue_id = venue_res.get_json()['id']
    
    date_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    client.post(f'/api/venues/{venue_id}/availability', json={"day_of_week": (datetime.date.today() + datetime.timedelta(days=1)).weekday(), "open_time": "14:00:00", "close_time": "15:00:00"})
    client.post('/api/reservations/', json={"venue_id": venue_id, "start_time": f"{date_str}T14:00:00", "end_time": f"{date_str}T15:00:00"}, headers=headers)

    response = client.get('/api/reservations/my-reservations', headers=headers)
    assert response.status_code == 200
    my_res_data = response.get_json()
    assert isinstance(my_res_data, list)
    assert len(my_res_data) >= 1
    assert my_res_data[0]['user_id'] == user_id
    assert my_res_data[0]['venue_id'] == venue_id
    assert my_res_data[0]['venue_name'] == "MyRes Venue"

def test_cancel_reservation_api(client, init_database, db_session):
    user_id = 1
    headers = {'X-User-Id': str(user_id)}
    venue_res = client.post('/api/venues/', json={"name": "CancelRes Venue", "capacity": 5})
    venue_id = venue_res.get_json()['id']

    # Make reservation far enough in the future to be cancellable
    future_start_obj = datetime.datetime.now() + datetime.timedelta(days=2, hours=1)
    future_end_obj = future_start_obj + datetime.timedelta(hours=1)
    
    # Ensure availability for this future slot
    day_of_week = future_start_obj.weekday()
    client.post(f'/api/venues/{venue_id}/availability', json={"day_of_week": day_of_week, "open_time": future_start_obj.time().strftime("%H:%M:%S"), "close_time": (future_end_obj + datetime.timedelta(hours=1)).time().strftime("%H:%M:%S") })


    res_data = {"venue_id": venue_id, "start_time": future_start_obj.isoformat(), "end_time": future_end_obj.isoformat()}
    creation_response = client.post('/api/reservations/', json=res_data, headers=headers)
    assert creation_response.status_code == 201 # Ensure creation worked
    reservation_id = creation_response.get_json()['id']

    cancel_response = client.put(f'/api/reservations/{reservation_id}/cancel', headers=headers)
    assert cancel_response.status_code == 200
    assert cancel_response.get_json()['message'] == 'Reservation cancelled successfully.'
    
    cancelled_res_db = db_session.query(Reservation).get(reservation_id)
    assert cancelled_res_db.status == 'cancelled'

# --- Stats API Tests ---
def test_get_venue_summary_stats_api(client, init_database, db_session):
    headers = {'X-User-Id': '1'}
    # Create a venue and a reservation
    venue_res = client.post('/api/venues/', json={"name": "Stats Venue", "capacity": 20})
    venue_id = venue_res.get_json()['id']
    date_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    day_of_week = (datetime.date.today() + datetime.timedelta(days=1)).weekday()
    
    client.post(f'/api/venues/{venue_id}/availability', json={"day_of_week": day_of_week, "open_time": "10:00:00", "close_time": "12:00:00"}) # 2 hours
    client.post('/api/reservations/', json={"venue_id": venue_id, "start_time": f"{date_str}T10:00:00", "end_time": f"{date_str}T11:00:00"}, headers=headers) # 1 hour booked

    response = client.get('/api/stats/venue-summary')
    assert response.status_code == 200
    stats_data = response.get_json()
    assert isinstance(stats_data, list)
    
    found_venue_stats = False
    for item in stats_data:
        if item['venue_id'] == venue_id:
            assert item['venue_name'] == "Stats Venue"
            assert item['total_confirmed_reservations'] == 1
            assert item['total_hours_booked'] == 1.0 
            found_venue_stats = True
            break
    assert found_venue_stats, "Stats for the test venue not found in summary."
