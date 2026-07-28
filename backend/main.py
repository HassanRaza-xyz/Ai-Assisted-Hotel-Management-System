# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, Room, Booking
from pydantic import BaseModel
from datetime import datetime
from agent import run_hotel_agent
import os
import shutil

app = FastAPI(title="AI Hotel Management System API")

# CORS Setup: Frontend connection ke liye
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Pydantic Schemas (Data validation)
class BookingCreate(BaseModel):
    guest_name: str
    guest_email: str | None = None
    guest_phone: str | None = None
    cnic_passport: str | None = None
    room_number: int
    check_in: str  # Format: "YYYY-MM-DD HH:MM"
    check_out: str # Format: "YYYY-MM-DD HH:MM"

class AgentRequest(BaseModel):
    prompt: str

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Welcome to AI Hotel Management Backend!"}

# 1. Get All Rooms (Frontend grid ke liye)
@app.get("/rooms")
def get_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).all()
    return rooms

# 2. Check Room Availability API
@app.get("/rooms/check/{room_number}")
def check_availability(room_number: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {
        "room_number": room.room_number,
        "category": room.category,
        "price_per_night": room.price_per_night,
        "status": room.status  
    }

# 3. Create Draft Booking API
@app.post("/bookings/draft")
def create_draft_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_number == booking_data.room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.status != "Available":
        return {"status": "error", "message": f"Room {booking_data.room_number} is currently {room.status}."}
    
    try:
        c_in = datetime.strptime(booking_data.check_in, "%Y-%m-%d %H:%M")
        c_out = datetime.strptime(booking_data.check_out, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD HH:MM")

    days = (c_out - c_in).days
    if days <= 0:
        days = 1
        
    total_bill = days * room.price_per_night

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

# 4. Text/Voice Chat Agent Endpoint
@app.post("/agent/chat")
def chat_with_agent(request: AgentRequest):
    try:
        result = run_hotel_agent(request.prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. CV/ID Card Document Upload Endpoint
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/agent/upload-cv")
async def upload_cv_and_book(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        from agent import client, types, tools_map, check_room_availability, create_draft_booking
        
        # File ko Gemini standard storage par upload karna
        uploaded_file = client.files.upload(file=file_path)
        
        prompt = (
            "Analyze this attached document (CV/ID Card). Extract the guest's name, email, and phone if available. "
            "Then, automatically create a draft booking for them for Room 5 from 2026-06-15 to 2026-06-20. "
            "If Room 5 is busy or booked, find any other available standard or deluxe room instead."
        )
        
        config = types.GenerateContentConfig(
            tools=[check_room_availability, create_draft_booking],
            temperature=0.0,
            system_instruction="You are an expert front-desk data extractor. Read the document and trigger booking tools immediately."
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt],
            config=config
        )
        
        # Cleanup file after processing
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Check if agent triggered the tool calling
        if response.function_calls:
            for function_call in response.function_calls:
                name = function_call.name
                args = function_call.args
                if name in tools_map:
                    tool_result = tools_map[name](**args)
                    return {
                        "agent_response": f"Successfully extracted data from document and triggered action.",
                        "action_taken": name,
                        "result": tool_result
                    }
                    
        return {"agent_response": response.text, "action_taken": "None", "result": None}

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))