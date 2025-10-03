#!/usr/bin/env python3
"""
VAPI Calendar Custom Functions - Production handlers for voice agent
Integrates with Microsoft Calendar for appointment booking
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.calendar.microsoft_oauth import MicrosoftOAuth
from src.calendar.microsoft_calendar import MicrosoftCalendar
from src.calendar.token_manager import TokenManager
from src.calendar.simple_calendar import SimpleCalendar


class CalendarFunctions:
    """VAPI custom function handlers - mirrors existing vapi_router pattern"""

    def __init__(self):
        self.oauth = MicrosoftOAuth()
        self.token_manager = TokenManager()

    async def _ensure_valid_token(self, user_id: str) -> tuple[Optional[Dict], Optional[str]]:
        """
        DRY helper: Get valid token or return error message
        Returns: (token_data, error_message)
        """
        token_data = self.token_manager.get_token(user_id)

        if not token_data:
            return None, "You haven't connected your calendar yet. Would you like me to send you an authorization link?"

        # Auto-refresh if expired
        if token_data.get("is_expired"):
            try:
                logger.info(f"🔄 Refreshing expired token for {user_id}")
                new_token = await self.oauth.refresh_access_token(token_data["refresh_token"])
                self.token_manager.store_token(user_id, new_token)
                token_data = self.token_manager.get_token(user_id)
            except Exception as e:
                logger.error(f"❌ Token refresh failed: {e}")
                return None, "Your calendar authorization expired. Please re-authorize calendar access."

        return token_data, None

    async def handle_get_availability(self, parameters: Dict[str, Any]) -> Dict:
        """
        VAPI Function: get_availability
        Check available viewing times from property manager's calendar
        """
        try:
            user_id = parameters.get("user_id", "pete_admin")  # Default to pete_admin
            property_address = parameters.get("property_address", "the property")

            logger.info(f"📅 get_availability called with user_id={user_id}, property={property_address}")

            # Get valid token
            token_data, error = await self._ensure_valid_token(user_id)
            if error:
                return {"result": error}

            # Use Microsoft Calendar with valid token
            calendar = MicrosoftCalendar(token_data["access_token"])
            available_slots = await calendar.get_availability()

            if not available_slots:
                return {
                    "result": f"Unfortunately, there are no available viewing times in the next week for {property_address}. Would you like to leave your contact information?"
                }

            # Format for voice (natural response)
            response = f"I have several viewing times available for {property_address}. "
            response += "Here are the next available slots: "

            for i, slot in enumerate(available_slots[:3], 1):
                response += f"{slot['formatted_time']}, "

            response += "Which time works best for you?"

            logger.info(f"✅ Returned {len(available_slots)} slots for {user_id}")

            # VAPI Server Function expects ONLY "result" key with string response
            return {
                "result": response
            }

        except Exception as e:
            logger.error(f"❌ get_availability error: {e}")
            return {
                "result": "I'm having trouble checking availability right now. Can I help you with something else?"
            }

    async def handle_set_appointment(self, parameters: Dict[str, Any]) -> Dict:
        """
        VAPI Function: set_appointment
        Book property viewing appointment
        """
        try:
            user_id = parameters.get("user_id", "pete_admin")  # Default to pete_admin
            property_address = parameters.get("property_address", "the property")
            start_time_str = parameters.get("start_time")
            attendee_name = parameters.get("attendee_name", "Guest")
            attendee_email = parameters.get("attendee_email")

            logger.info(f"📅 set_appointment called with user_id={user_id}, property={property_address}, time={start_time_str}")

            # Get valid token
            token_data, error = await self._ensure_valid_token(user_id)
            if error:
                return {"result": error}

            # Parse start time
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_time = start_time + timedelta(minutes=30)

            # Use Microsoft Calendar with valid token
            calendar = MicrosoftCalendar(token_data["access_token"])
            appointment = await calendar.create_appointment(
                start_time=start_time,
                end_time=end_time,
                subject=f"Property Viewing: {property_address}",
                body=f"Viewing appointment with {attendee_name}",
                attendee_email=attendee_email
            )

            # Success response
            formatted_time = start_time.strftime("%I:%M %p on %A, %B %d")
            response = f"Perfect! I've booked your viewing for {formatted_time} at {property_address}. "
            response += "You'll receive a calendar invitation shortly. Is there anything else I can help you with?"

            logger.info(f"✅ Booked appointment {appointment['event_id']} for {user_id}")

            return {
                "result": response
            }

        except Exception as e:
            logger.error(f"❌ set_appointment error: {e}")
            return {
                "result": "I couldn't complete the booking right now. Would you like me to take your information and have someone call you back?"
            }


# Singleton instance for imports
calendar_functions = CalendarFunctions()
