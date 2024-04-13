from flask import Flask, request, redirect, session, url_for, jsonify
import requests
import jwt
import datetime
import base64
import json

app = Flask(__name__)
app.secret_key = 'super secret key'
client_id = '7Pttnnj8SD2C78R86x6tbA'
client_secret = 'DxHKFBV5eFbLdVPvQdFIYuiWHsoyhjEH'
# Meeting ID
meeting_id = "85981236227"
# Zoom authorization endpoint
authorization_base_url = 'https://zoom.us/oauth/authorize'
redirect_uri = 'http://localhost:5000/callback'
token_url = 'https://zoom.us/oauth/token'
profile_url = 'https://api.zoom.us/v2/users/me'
meeting_participants_url = 'https://api.zoom.us/v2/report/meetings/{meeting_id}/participants'
curr_participants_url = 'https://api.zoom.us/v2/report/meetings/{meeting_id}/participants'
get_meeting_url = 'https://api.zoom.us/v2/meetings/{meeting_id}'
update_breakout_rooms_url = 'https://api.zoom.us/v2/meetings/{meeting_id}/breakoutRooms'


# Redirect users to Zoom authorization URL
@app.route('/login')
def login():
    scopes = [ 'meeting:read:participant','meeting:read:list_past_participants','meeting:read:meeting',]
    return redirect(authorization_base_url + f'?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}')

# Exchange authorization code for access token
@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_params = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    response = requests.post(token_url, data=token_params, auth=(client_id, client_secret))
    data = response.json()
    if 'access_token' in data:
        access_token = data['access_token']
        # Store access token in session
        session['access_token'] = access_token
        return redirect(url_for('get_participants'))
    else:
        error_message = data.get('error_description') or "Failed to get access token"
        return f"Error: {error_message}"

@app.route('/profile')
def get_profile():
    access_token = session.get('access_token')
    if access_token:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        try:
            profile_data = response.json()
            return jsonify(profile_data)
        except ValueError:
            return f"Error: {response.text}"
    else:
        return "Access token not found. Please login."

        # Function to find a partner for a participant, avoiding repeats

def find_partner(participant, remaining_participants, previous_pairings):
    for potential_partner in remaining_participants:
        if (participant, potential_partner) not in previous_pairings and (potential_partner, participant) not in previous_pairings:
            return potential_partner
    return None

# Function to create breakout rooms for a round
def create_breakout_rooms(round_number, pairs):
    for index, pair in enumerate(pairs):
        breakout_room_name = f"Round{round_number}_Room{index + 1}"
        # Create breakout room
        breakout_room_payload = {
            "name": breakout_room_name,
            "meeting_id": meeting_id,
            "participants": [{"email": participant} for participant in pair]
        }
        response = requests.post("https://api.zoom.us/v2/breakoutRooms", json=breakout_room_payload, headers={"Authorization": f"Bearer {jwt_token}"})
        if response.status_code == 201:
            print(f"Created breakout room '{breakout_room_name}' for participants: {pair}")
        else:
            print(f"Failed to create breakout room: {response.text}")

def generate_pairs(participants, previous_pairings):
    pairs = []
    remaining_participants = participants.copy()
    
    # Shuffle the list of participants to randomize pairings
    random.shuffle(remaining_participants)
    
    while len(remaining_participants) >= 2:
        participant1 = remaining_participants.pop()
        
        # Find a participant to pair with, avoiding repeats
        participant2 = find_partner(participant1, remaining_participants, previous_pairings)
        if participant2:
            pairs.append((participant1, participant2))
            remaining_participants.remove(participant2)
    
    return pairs

# Route to display user's Zoom profile
@app.route('/participants')
def get_participants():
    access_token = session.get('access_token')
    if access_token:
        # Fetch meeting participants
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(curr_participants_url.format(meeting_id=meeting_id), headers=headers)
        if response.status_code == 200:
            participants = response.json()
            print(participants)
            return jsonify(participants)
        else:
            return f"Failed to fetch meeting participants: {response.status_code}"
    else:
        return "Access token not found. Please login."

@app.route('/rooms')
def update_breakout_rooms():
    access_token = session.get('access_token')
    breakout_rooms = [
        {
            'id': '1',  # Breakout room ID
            'participants': ['Participant 1', 'Participant 2']  # List of participants in the breakout room
        },
        {
            'id': '2',
            'participants': ['Participant 3', 'Participant 4']
        }
    ]
    # Request headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Request body to update breakout room assignments
    data = {
        'action': 'assign',
        'breakout_rooms': breakout_rooms
    }

    # Send request to update breakout room assignments
    response = requests.put(update_breakout_rooms_url.format(meeting_id=meeting_id), headers=headers, data=json.dumps(data))

    # Check if request was successful
    if response.status_code == 204:
        print("Breakout rooms updated successfully")
    else:
        print(f"Failed to update breakout rooms: {response.status_code}")

@app.route('/meeting')
def get_meeting():
    # Request headers
    access_token = session.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Send request to get meeting details
    response = requests.get(get_meeting_url.format(meeting_id=meeting_id), headers=headers)

    # Check if request was successful
    if response.status_code == 200:
        meeting_details = response.json()
        return jsonify(meeting_details)
    else:
        print(f"Failed to get meeting details: {response.status_code}")
        return None

# Route to display index page with access token (for demonstration)
@app.route('/')
def index():
    access_token = session.get('access_token')
    return f'Access Token: {access_token}'
if __name__ == '__main__':
    app.run(debug=True)