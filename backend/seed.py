# backend/seed.py
from database import SessionLocal, Room, init_db

def seed_rooms():
    db = SessionLocal()
    
    # Check agar pehle se rooms hain toh dobara insert na kare
    if db.query(Room).count() > 0:
        print("Database already has rooms data.")
        db.close()
        return

    print("Populating 100 rooms...")
    
    # 1 se 50: Standard Rooms ($50/night)
    for i in range(1, 51):
        room = Room(room_number=i, category="Standard", price_per_night=50.0, status="Available")
        db.add(room)
        
    # 51 se 85: Deluxe Rooms ($100/night)
    for i in range(51, 86):
        room = Room(room_number=i, category="Deluxe", price_per_night=100.0, status="Available")
        db.add(room)
        
    # 86 se 100: Suite Rooms ($250/night)
    for i in range(86, 101):
        room = Room(room_number=i, category="Suite", price_per_night=250.0, status="Available")
        db.add(room)

    db.commit()
    db.close()
    print("100 Rooms successfully added to the database!")

if __name__ == "__main__":
    init_db()  # Pehle tables create karega
    seed_rooms()  # Phir rooms data daalega