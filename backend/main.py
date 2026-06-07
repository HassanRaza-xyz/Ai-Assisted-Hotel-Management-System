# backend/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, Room, Booking
from pydantic import BaseModel
from datetime import datetime
from agent import run_hotel_agent
app = FastAPI(title="AI Hotel Management System API")

# CORS Setup: Taake hamara Next.js frontend is backend se easily connect ho sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production me isko specific frontend URL par set karenge
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Pydantic Schemas (Data validation ke liye)
class BookingCreate(BaseModel):
    guest_name: str
    guest_email: str | None = None
    guest_phone: str | None = None
    cnic_passport: str | None = None
    room_number: int
    check_in: str  # Format: "YYYY-MM-DD HH:MM"
    check_out: str # Format: "YYYY-MM-DD HH:MM"

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Welcome to AI Hotel Management Backend!"}

# 1. Get All Rooms (Frontend ke grid view ke liye)
@app.get("/rooms")
def get_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).all()
    return rooms

# 2. Check Room Availability API (AI Agent isko use karega)
@app.get("/rooms/check/{room_number}")
def check_availability(room_number: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_with_code=404, detail="Room not found")
    
    return {
        "room_number": room.room_number,
        "category": room.category,
        "price_per_night": room.price_per_night,
        "status": room.status  # Available, Booked, Maintenance
    }

# 3. Create Draft Booking API (HITL - Human in the Loop concept)
@app.post("/bookings/draft")
def create_draft_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
    # Pehle check karo room exist karta ha ya nahi
    room = db.query(Room).filter(Room.room_number == booking_data.room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.status != "Available":
        return {"status": "error", "message": f"Room {booking_data.room_number} is currently {room.status}."}
    
    # Date string ko python datetime object me convert karna
    try:
        c_in = datetime.strptime(booking_data.check_in, "%Y-%m-%d %H:%M")
        c_out = datetime.strptime(booking_data.check_out, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD HH:MM")

    # Total days aur bill calculate karna
    days = (c_out - c_in).days
    if days <= 0:
        days = 1 # Minimum 1 night charge hogi agar same day checkout ho
        
    total_bill = days * room.price_per_night

    # Draft booking entry create karna (Yahan status 'Draft' hoga)
    new_booking = Booking(
        guest_name=booking_data.guest_name,
        guest_email=booking_data.guest_email,
        guest_phone=booking_data.guest_phone,
        cnic_passport=booking_data.cnic_passport,
        room_id=room.id,
        check_in=c_in,
        check_out=c_out,
        total_bill=total_bill,
        booking_status="Draft" 
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return {
        "status": "success",
        "message": f"Draft booking created for {booking_data.guest_name}.",
        "booking_id": new_booking.id,
        "total_bill": total_bill,
        "requires_confirmation": True
    }
class AgentRequest(BaseModel):
    prompt: str

@app.post("/agent/chat")
def chat_with_agent(request: AgentRequest):
    try:
        result = run_hotel_agent(request.prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))