from flask import Flask
import requests

app = Flask(__name__)

# Alain User ID
user_id = 242079

# Zoom API credentials
api_key = "6uziqPfATPasDDE2oN9fxQ"
api_secret = "f2uI3VvTuRsOcXOxogPg3rXi7Zlpwwef"

# Meeting ID
meeting_id = "438 396 7761"

# JWT Token for authentication
jwt_token = generate_jwt_token(api_key, api_secret)

# Make API request to retrieve meeting participants
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

def get_participants():
    participants_url = f"https://api.zoom.us/v2/past_meetings/{meeting_id}/participants"
    response = requests.get(participants_url, headers=headers)
    # Check response status
    if response.status_code == 200:
        participants = response.json()["participants"]
        for participant in participants:
            print(participant["name"], participant["email"])
    else:
        print("Failed to retrieve participants:", response.text)
        

# Function to generate pairs for a round while avoiding repeats
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

# Example usage
participants = get_participants()
previous_pairings = []  # Store previous pairings here
rounds = 3  # Number of rounds

@app.route("/")
def hello_world():
    for round_number in range(1, rounds + 1):
        round_pairs = generate_pairs(participants, previous_pairings)
        create_breakout_rooms(round_number, round_pairs)
        previous_pairings.extend(round_pairs)