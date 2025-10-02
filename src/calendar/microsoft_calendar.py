#!/usr/bin/env python3
"""
Microsoft Calendar Manager - Graph API wrapper
Handles availability checks and appointment creation
"""

import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger


class MicrosoftCalendar:
    """Microsoft Graph API calendar operations"""

    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def get_availability(
        self,
        days_ahead: int = 7,
        start_hour: int = 9,
        end_hour: int = 17,
        slot_duration: int = 30
    ) -> List[Dict]:
        """
        Get available time slots for next N days during business hours
        Returns list of available 30-min slots
        """
        start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=days_ahead)

        # Use calendarView endpoint to get existing events
        events_url = f"{self.GRAPH_API_ENDPOINT}/me/calendarView"
        params = {
            "startDateTime": start_time.isoformat() + "Z",
            "endDateTime": end_time.isoformat() + "Z"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(events_url, headers=self.headers, params=params)
                response.raise_for_status()
                events_data = response.json()

            # Parse existing events as busy times
            busy_times = []
            for event in events_data.get("value", []):
                busy_times.append({
                    "start": datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00")),
                    "end": datetime.fromisoformat(event["end"]["dateTime"].replace("Z", "+00:00"))
                })

            # Generate available slots by excluding busy times
            available_slots = self._generate_free_slots(
                start_time, days_ahead, start_hour, end_hour, slot_duration, busy_times
            )

            logger.info(f"📅 Found {len(available_slots)} available slots")
            return available_slots[:10]  # Return top 10

        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to fetch availability: {e}")
            raise

    def _generate_free_slots(
        self, start_time: datetime, days_ahead: int, start_hour: int,
        end_hour: int, slot_duration: int, busy_times: List[Dict]
    ) -> List[Dict]:
        """Generate free time slots by excluding busy times"""

        # Generate all possible slots and filter out busy ones
        available_slots = []
        for day in range(days_ahead):
            current_day = start_time + timedelta(days=day)

            # Skip weekends
            if current_day.weekday() >= 5:
                continue

            # Generate time slots for business hours
            for hour in range(start_hour, end_hour):
                for minute in [0, 30] if slot_duration == 30 else [0]:
                    slot_start = current_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    slot_end = slot_start + timedelta(minutes=slot_duration)

                    # Skip past times
                    if slot_start < datetime.now():
                        continue

                    # Check if slot overlaps with any busy time
                    is_free = True
                    for busy in busy_times:
                        if not (slot_end <= busy["start"] or slot_start >= busy["end"]):
                            is_free = False
                            break

                    if is_free:
                        available_slots.append({
                            "start_time": slot_start.isoformat(),
                            "end_time": slot_end.isoformat(),
                            "duration_minutes": slot_duration,
                            "formatted_time": slot_start.strftime("%A, %B %d at %I:%M %p")
                        })

        return available_slots

    async def create_appointment(
        self,
        start_time: datetime,
        end_time: datetime,
        subject: str,
        body: str,
        attendee_email: Optional[str] = None
    ) -> Dict:
        """Create calendar appointment"""

        event_url = f"{self.GRAPH_API_ENDPOINT}/me/calendar/events"

        event_data = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body
            },
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            },
            "isOnlineMeeting": False,
            "reminderMinutesBeforeStart": 60
        }

        if attendee_email:
            event_data["attendees"] = [{
                "emailAddress": {"address": attendee_email},
                "type": "required"
            }]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(event_url, headers=self.headers, json=event_data)
                response.raise_for_status()
                event_result = response.json()

            logger.info(f"✅ Created appointment: {event_result['id']}")

            return {
                "event_id": event_result["id"],
                "subject": event_result["subject"],
                "start_time": event_result["start"]["dateTime"],
                "end_time": event_result["end"]["dateTime"],
                "web_link": event_result.get("webLink")
            }

        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to create appointment: {e}")
            raise

    async def check_conflict(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if time slot has a conflict"""

        schedule_url = f"{self.GRAPH_API_ENDPOINT}/me/calendar/getSchedule"

        payload = {
            "schedules": ["me"],
            "startTime": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "endTime": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(schedule_url, headers=self.headers, json=payload)
                response.raise_for_status()
                schedule_data = response.json()

            # Check for busy items
            schedules = schedule_data.get("value", [])
            if schedules:
                schedule_items = schedules[0].get("scheduleItems", [])
                return len(schedule_items) > 0

            return False

        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to check conflict: {e}")
            return True  # Assume conflict on error to be safe
