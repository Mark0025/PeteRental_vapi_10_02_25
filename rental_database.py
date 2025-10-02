#!/usr/bin/env python3
"""
Simple Rental Database with JSON Storage
Stores rental data and updates daily for instant responses
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from loguru import logger
import asyncio
import schedule
import time
from pathlib import Path

class RentalDatabase:
    def __init__(self, db_file: str = "rental_data.json"):
        self.db_file = db_file
        self.last_update = None
        self.update_interval = timedelta(days=1)
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Create database file if it doesn't exist"""
        if not os.path.exists(self.db_file):
            initial_data = {
                "last_updated": None,
                "rentals": {},
                "websites": {}
            }
            self.save_data(initial_data)
            logger.info(f"Created new rental database: {self.db_file}")
    
    def load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(f"Database file {self.db_file} not found or corrupted, creating new one")
            return {"last_updated": None, "rentals": {}, "websites": {}}
    
    def save_data(self, data: Dict[str, Any]):
        """Save data to JSON file"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save database: {e}")
    
    def add_rental(self, website: str, rental_data: Dict[str, Any]):
        """Add or update rental data for a website - only if it's new or changed"""
        data = self.load_data()
        
        # Clean website URL for storage
        clean_website = website.replace('https://', '').replace('http://', '').split('/')[0]
        
        # Initialize website entry if it doesn't exist
        if clean_website not in data["websites"]:
            data["websites"][clean_website] = {
                "url": website,
                "last_scraped": None,
                "rental_count": 0
            }
        
        # Check if this rental already exists (by comparing key data)
        existing_rental = self._find_existing_rental(clean_website, rental_data)
        
        if existing_rental:
            # Update existing rental if data has changed
            if self._has_data_changed(existing_rental["data"], rental_data):
                existing_rental["data"] = rental_data
                existing_rental["scraped_at"] = datetime.now().isoformat()
                self.save_data(data)
                logger.info(f"Updated existing rental {existing_rental['id']} for {clean_website}")
            else:
                logger.info(f"Rental already exists and unchanged for {clean_website}")
            return existing_rental["id"]
        else:
            # Generate unique rental ID for new rental
            rental_id = f"{clean_website}_{len(data['rentals']) + 1}"
            
            # Store rental data with metadata
            rental_entry = {
                "id": rental_id,
                "website": clean_website,
                "source_url": website,
                "scraped_at": datetime.now().isoformat(),
                "data": rental_data
            }
            
            data["rentals"][rental_id] = rental_entry
            data["websites"][clean_website]["last_scraped"] = datetime.now().isoformat()
            data["websites"][clean_website]["rental_count"] = len([r for r in data["rentals"].values() if r["website"] == clean_website])
            
            self.save_data(data)
            logger.info(f"Added new rental {rental_id} for {clean_website}")
            return rental_id
    
    def _find_existing_rental(self, website: str, rental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Find existing rental by matching key identifying fields"""
        data = self.load_data()
        
        # Look for existing rentals with same key identifying information
        for rental in data["rentals"].values():
            if rental["website"] == website:
                existing_data = rental["data"]
                
                # Check if this is the same rental by comparing key fields
                if self._is_same_rental(existing_data, rental_data):
                    return rental
        
        return None
    
    def _is_same_rental(self, existing: Dict[str, Any], new: Dict[str, Any]) -> bool:
        """Check if two rental entries represent the same property"""
        # Use address as the primary identifier since it's unique
        if 'address' in existing and 'address' in new:
            existing_addr = str(existing['address']).lower().strip()
            new_addr = str(new['address']).lower().strip()
            return existing_addr == new_addr
        
        # Fallback: compare multiple fields only if address is missing
        key_fields = ['bedrooms', 'bathrooms', 'price']
        matches = 0
        
        for field in key_fields:
            if field in existing and field in new:
                if str(existing[field]).lower() == str(new[field]).lower():
                    matches += 1
        
        # Only consider it the same if most fields match (and address is missing)
        return matches >= 2
    
    def _has_data_changed(self, existing: Dict[str, Any], new: Dict[str, Any]) -> bool:
        """Check if rental data has changed significantly"""
        # Compare all fields to see if anything important changed
        important_fields = ['price', 'available_date', 'amenities', 'description']
        
        for field in important_fields:
            if field in existing and field in new:
                if str(existing[field]) != str(new[field]):
                    return True
            elif field in existing or field in new:
                return True
        
        return False
    
    def get_rentals_for_website(self, website: str) -> List[Dict[str, Any]]:
        """Get all rentals for a specific website"""
        data = self.load_data()
        clean_website = website.replace('https://', '').replace('http://', '').split('/')[0]
        
        rentals = []
        for rental in data["rentals"].values():
            if rental["website"] == clean_website:
                rentals.append(rental)
        
        return rentals
    
    def get_all_rentals(self) -> List[Dict[str, Any]]:
        """Get all rentals from database"""
        data = self.load_data()
        return list(data["rentals"].values())
    
    def is_update_needed(self) -> bool:
        """Check if database needs updating"""
        data = self.load_data()
        if not data["last_updated"]:
            return True
        
        last_update = datetime.fromisoformat(data["last_updated"])
        return datetime.now() - last_update > self.update_interval
    
    def mark_updated(self):
        """Mark database as updated"""
        data = self.load_data()
        data["last_updated"] = datetime.now().isoformat()
        self.save_data(data)
        logger.info("Database marked as updated")
    
    def clear_old_data(self, days_old: int = 7):
        """Clear rental data older than specified days"""
        data = self.load_data()
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        old_rentals = []
        for rental_id, rental in data["rentals"].items():
            scraped_at = datetime.fromisoformat(rental["scraped_at"])
            if scraped_at < cutoff_date:
                old_rentals.append(rental_id)
        
        for rental_id in old_rentals:
            del data["rentals"][rental_id]
        
        if old_rentals:
            self.save_data(data)
            logger.info(f"Cleared {len(old_rentals)} old rental entries")
    
    def sync_rentals(self, website: str, current_rentals: List[Dict[str, Any]]):
        """Sync database with current rental data - remove unavailable ones, add new ones"""
        data = self.load_data()
        clean_website = website.replace('https://', '').replace('http://', '').split('/')[0]
        
        # Get existing rentals for this website
        existing_rentals = {rental["id"]: rental for rental in data["rentals"].values() 
                           if rental["website"] == clean_website}
        
        # Track which current rentals we've processed
        processed_rentals = set()
        
        # Process current rentals (add new ones, update existing ones)
        for rental_data in current_rentals:
            rental_id = self.add_rental(website, rental_data)
            if rental_id:
                processed_rentals.add(rental_id)
        
        # Remove rentals that are no longer available
        removed_count = 0
        for rental_id, rental in existing_rentals.items():
            if rental_id not in processed_rentals:
                del data["rentals"][rental_id]
                removed_count += 1
        
        if removed_count > 0:
            self.save_data(data)
            logger.info(f"Removed {removed_count} unavailable rentals for {clean_website}")
        
        return len(current_rentals), removed_count
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        data = self.load_data()
        return {
            "total_rentals": len(data["rentals"]),
            "websites_tracked": len(data["websites"]),
            "last_updated": data["last_updated"],
            "websites": {
                website: {
                    "rental_count": info["rental_count"],
                    "last_scraped": info["last_scraped"]
                }
                for website, info in data["websites"].items()
            }
        }

# Global database instance
rental_db = RentalDatabase()

def update_rental_database():
    """Update rental database with fresh data"""
    logger.info("Starting daily rental database update...")
    
    # This would be called by your main scraping logic
    # For now, just mark as updated
    rental_db.mark_updated()
    
    # Clear old data (older than 7 days)
    rental_db.clear_old_data(days_old=7)
    
    logger.info("Daily rental database update completed")

def start_scheduler():
    """Start the daily scheduler"""
    schedule.every().day.do(update_rental_database)
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

if __name__ == "__main__":
    # Test the database
    print("Testing Rental Database...")
    
    # Show database stats
    stats = rental_db.get_database_stats()
    print(f"Database Stats: {json.dumps(stats, indent=2)}")
    
    # Show any existing rental data (will be empty initially)
    rentals = rental_db.get_all_rentals()
    if rentals:
        print(f"Existing Rental Data: {json.dumps(rentals, indent=2)}")
    else:
        print("No rental data found - database is empty and ready for real data")
