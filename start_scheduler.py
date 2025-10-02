#!/usr/bin/env python3
"""
Start the hourly rental database scheduler
Run this in the background to keep rental data fresh
"""

from rental_database import start_scheduler
import signal
import sys

def signal_handler(sig, frame):
    print('\n🛑 Shutting down rental scheduler...')
    sys.exit(0)

if __name__ == "__main__":
    print("🚀 Starting Rental Database Scheduler...")
    print("📅 Will update rental data every hour")
    print("💾 Database file: rental_data.json")
    print("⏰ Press Ctrl+C to stop")
    
    # Handle graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the scheduler
    start_scheduler()
