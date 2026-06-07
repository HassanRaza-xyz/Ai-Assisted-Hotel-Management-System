# In imports ko agent.py ke top par replace kar do
import os
from google import genai
from google.genai import types  # types ko is tarah import karna ha
from dotenv import load_dotenv
from database import SessionLocal, Room, Booking
from datetime import datetime
load_dotenv()

# Gemini Client Initialize karna
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --AGENT TOOLS (Python functions jo AI use karega) ---

def check_room_availability(room_number: int) -> str:
    """Checks the current availability and details of a specific room number."""
    db = SessionLocal()
    room = db.query(Room).filter(Room.room_number == room_number).first()
    db.close()
    
    if not room:
        return f"Room {room_number} does not exist in our hotel."
    return f"Room {room_number} ({room.category}) is currently {room.status}. Price per night is ${room.price_per_night}."


def create_draft_booking(guest_name: str, room_number: int, check_in_date: str, check_out_date: str, guest_email: str = None) -> str:
    """Creates a draft booking request. Dates should be in YYYY-MM-DD format."""
    db = SessionLocal()
    room = db.query(Room).filter(Room.room_number == room_number).first()
    
    if not room:
        db.close()
        return f"Error: Room {room_number} not found."
    
    if room.status != "Available":
        db.close()
        return f"Error: Room {room_number} is already {room.status}."
    
    try:
        # Formatting dates
        c_in = datetime.strptime(f"{check_in_date} 12:00", "%Y-%m-%d %H:%M")
        c_out = datetime.strptime(f"{check_out_date} 11:00", "%Y-%m-%d %H:%M")
    except ValueError:
        db.close()
        return "Error: Invalid date format. Please use YYYY-MM-DD."

    days = (c_out - c_in).days
    if days <= 0: days = 1
    total_bill = days * room.price_per_night

    # Create Draft Booking
    new_booking = Booking(
        guest_name=guest_name,
        guest_email=guest_email,
        room_id=room.id,
        check_in=c_in,
        check_out=c_out,
        total_bill=total_bill,
        booking_status="Draft"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    db.close()

    return f"Success! Draft booking ID {new_booking.id} created for {guest_name} in Room {room_number}. Total Bill: ${total_bill}. Needs admin confirmation."

# Tools mapping dictionary taake model call handle ho sake
tools_map = {
    "check_room_availability": check_room_availability,
    "create_draft_booking": create_draft_booking
}

# --- THE AGENT EXECUTION LOGIC ---

def run_hotel_agent(user_prompt: str) -> str:
    # 2026 Recommended model for low-latency speed & structured tool calling
    model_id = "gemini-2.5-flash"
    # agent.py ke andar run_hotel_agent function ke andar ye replace karo:
    config = types.GenerateContentConfig(
        tools=[check_room_availability, create_draft_booking],
        temperature=0.0,
        system_instruction=(
            "You are an autonomous AI front-desk agent for a 100-room luxury hotel. "
            "Your job is to manage room bookings. Use the provided tools to check room availability "
            "and create draft bookings. If a room is already booked, kindly suggest alternative rooms. "
            "Today's date reference is June 2026."
        )
    )
    
    # Gemini ko prompt bhejna
    response = client.models.generate_content(
        model=model_id,
        contents=user_prompt,
        config=config
    )
    
    # Check agar Gemini kisi Tool/Function ko call karna chahta ha
    if response.function_calls:
        for function_call in response.function_calls:
            name = function_call.name
            args = function_call.args
            
            # Function dynamically execute karna map se
            if name in tools_map:
                tool_result = tools_map[name](**args)
                return {
                    "agent_response": response.text if response.text else f"Executing action: {name}",
                    "action_taken": name,
                    "result": tool_result
                }
                
    return {"agent_response": response.text, "action_taken": "None", "result": None}