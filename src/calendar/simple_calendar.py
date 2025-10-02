"""
Simple local calendar storage (no Microsoft account needed)
Stores appointments in JSON file for testing
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

class SimpleCalendar:
    def __init__(self, storage_file="data/appointments.json"):
        self.storage_file = storage_file
        Path(storage_file).parent.mkdir(exist_ok=True)
        if not Path(storage_file).exists():
            self._save({"appointments": []})
    
    def _load(self):
        with open(self.storage_file) as f:
            return json.load(f)
    
    def _save(self, data):
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def get_availability(self, days_ahead=7, start_hour=9, end_hour=17):
        """Generate available slots excluding booked appointments"""
        data = self._load()
        booked = data.get("appointments", [])
        
        # Generate all business hour slots
        slots = []
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day in range(days_ahead):
            current = start + timedelta(days=day)
            if current.weekday() >= 5:  # Skip weekends
                continue
            
            for hour in range(start_hour, end_hour):
                slot_time = current.replace(hour=hour, minute=0)
                
                # Check if slot is available
                is_available = True
                for apt in booked:
                    apt_time = datetime.fromisoformat(apt["start_time"].replace("Z", ""))
                    if abs((slot_time - apt_time).total_seconds()) < 1800:  # 30min buffer
                        is_available = False
                        break
                
                if is_available:
                    slots.append({
                        "start_time": slot_time.isoformat() + "Z",
                        "formatted_time": slot_time.strftime("%A, %B %d at %I:%M %p")
                    })
        
        return slots[:10]  # Return top 10
    
    async def create_appointment(self, start_time, property_address, attendee_name, attendee_email=None):
        """Book an appointment"""
        data = self._load()
        
        appointment = {
            "id": f"apt_{len(data['appointments']) + 1}",
            "start_time": start_time.isoformat() + "Z" if isinstance(start_time, datetime) else start_time,
            "property_address": property_address,
            "attendee_name": attendee_name,
            "attendee_email": attendee_email,
            "created_at": datetime.now().isoformat()
        }
        
        data["appointments"].append(appointment)
        self._save(data)
        
        return {
            "event_id": appointment["id"],
            "start_time": appointment["start_time"],
            "status": "confirmed"
        }
