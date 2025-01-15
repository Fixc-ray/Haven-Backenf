from flask import Flask, request, jsonify
from flask_cors import CORS
from extensions import db
from flask_migrate import Migrate
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rooms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, origins=["http://localhost:3000"])
db.init_app(app)
migrate = Migrate(app, db)

from model import Room, Booking

# Fetch all available rooms
@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    available_rooms = []

    for room in rooms:
        is_available = True
        for booking in room.bookings:
            if booking.start_date <= datetime.today().date() <= booking.end_date:
                is_available = False
                break
        if is_available:
            available_rooms.append({
                "id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "price_per_night": room.price_per_night
            })

    return jsonify({"rooms": available_rooms}), 200

# Book a room
@app.route('/book-room', methods=['POST'])
def book_room():
    data = request.get_json()
    user_name = data.get('user_name')
    user_email = data.get('user_email')
    phone_number = data.get('phone_number')
    room_id = data.get('room_id')
    start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()

    if not user_name or not user_email or not phone_number or not room_id or not start_date or not end_date:
        return jsonify({"error": "Missing required fields"}), 400

    if start_date >= end_date:
        return jsonify({"error": "Invalid date range"}), 400

    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    overlapping_booking = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.end_date > start_date,
        Booking.start_date < end_date
    ).first()

    if overlapping_booking:
        return jsonify({"error": "Room is already booked for the selected dates"}), 400

    new_booking = Booking(
        user_name=user_name,
        user_email=user_email,
        phone_number=phone_number,
        room_id=room_id,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(new_booking)
    db.session.commit()

    return jsonify({"message": "Room booked successfully"}), 201

# Seed initial room data
def seed_rooms():
    if Room.query.count() == 0:
        rooms_data = [
            {"room_number": "101", "room_type": "Standard", "price_per_night": 3500, "bedrooms_count": 1},
            {"room_number": "102", "room_type": "Standard", "price_per_night": 50000, "bedrooms_count": 2},
            {"room_number": "103", "room_type": "Deluxe", "price_per_night": 5000, "bedrooms_count": 2},
            {"room_number": "104", "room_type": "Suite", "price_per_night": 200.0, "bedrooms_count": 1}
        ]
        for room_data in rooms_data:
            room = Room(**room_data)
            db.session.add(room)
        db.session.commit()
        print("Rooms seeded successfully.")

if __name__ == "__main__":
    with app.app_context():
        seed_rooms()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=5000, debug=True)
