#!/usr/bin/env python3
"""
Playwright-powered Rental Scraper
Handles JavaScript-heavy rental websites and extracts detailed rental information
"""

import asyncio
from playwright.async_api import async_playwright
from loguru import logger
import re
from typing import List, Dict, Any, Optional
import time

class PlaywrightRentalScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # Set to False for debugging
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        self.page = await self.context.new_page()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def scrape_rental_website(self, website: str) -> List[Dict[str, Any]]:
        """Scrape rental website using Playwright for JavaScript-heavy content"""
        try:
            logger.info(f"🌐 Loading website: {website}")
            
            # Navigate to the website
            await self.page.goto(website, wait_until='networkidle', timeout=30000)
            
            # Wait a bit for any dynamic content to load
            await asyncio.sleep(3)
            
            # Try to find rental listings with different strategies
            rental_listings = []
            
            # Strategy 1: Look for common rental listing patterns
            rental_listings.extend(await self._extract_rental_listings_strategy_1())
            
            # Strategy 2: Look for rental cards/containers
            if not rental_listings:
                rental_listings.extend(await self._extract_rental_listings_strategy_2())
            
            # Strategy 3: Look for rental tables
            if not rental_listings:
                rental_listings.extend(await self._extract_rental_listings_strategy_3())
            
            # Strategy 4: Extract from page content if no structured listings found
            if not rental_listings:
                rental_listings.extend(await self._extract_from_page_content())
            
            # Deduplicate rentals before returning
            unique_rentals = self._deduplicate_rentals(rental_listings)
            logger.info(f"✅ Found {len(unique_rentals)} unique rental listings using Playwright")
            return unique_rentals
            
        except Exception as e:
            logger.error(f"❌ Playwright scraping failed for {website}: {str(e)}")
            return []
    
    async def _extract_rental_listings_strategy_1(self) -> List[Dict[str, Any]]:
        """Strategy 1: Look for common rental listing patterns"""
        try:
            # Look for elements that might contain rental listings
            rental_selectors = [
                '[class*="rental"]',
                '[class*="listing"]',
                '[class*="property"]',
                '[class*="unit"]',
                '[class*="apartment"]',
                '[class*="house"]',
                '[class*="condo"]'
            ]
            
            listings = []
            for selector in rental_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements[:20]:  # Increased limit to capture more
                    try:
                        text = await element.text_content()
                        if text and self._is_rental_content(text):
                            listing = await self._extract_rental_details(element)
                            if listing:
                                listings.append(listing)
                    except Exception as e:
                        continue
            
            return listings
        except Exception as e:
            logger.warning(f"Strategy 1 failed: {e}")
            return []
    
    async def _extract_rental_listings_strategy_2(self) -> List[Dict[str, Any]]:
        """Strategy 2: Look for rental cards/containers"""
        try:
            # Look for card-like elements that might contain rental info
            card_selectors = [
                '[class*="card"]',
                '[class*="item"]',
                '[class*="tile"]',
                'article',
                'section',
                'div[class*="listing"]'
            ]
            
            listings = []
            for selector in card_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements[:25]:  # Increased limit to capture more
                    try:
                        text = await element.text_content()
                        if text and self._is_rental_content(text):
                            listing = await self._extract_rental_details(element)
                            if listing:
                                listings.append(listing)
                    except Exception as e:
                        continue
            
            return listings
        except Exception as e:
            logger.warning(f"Strategy 2 failed: {e}")
            return []
    
    async def _extract_rental_listings_strategy_3(self) -> List[Dict[str, Any]]:
        """Strategy 3: Look for rental tables"""
        try:
            # Look for table elements that might contain rental data
            table_selectors = ['table', '[class*="table"]', '[class*="grid"]']
            
            listings = []
            for selector in table_selectors:
                tables = await self.page.query_selector_all(selector)
                for table in tables[:5]:  # Limit to first 5 tables
                    try:
                        rows = await table.query_selector_all('tr')
                        for row in rows[1:]:  # Skip header row
                            text = await row.text_content()
                            if text and self._is_rental_content(text):
                                listing = await self._extract_rental_details(row)
                                if listing:
                                    listings.append(listing)
                    except Exception as e:
                        continue
            
            return listings
        except Exception as e:
            logger.warning(f"Strategy 3 failed: {e}")
            return []
    
    async def _extract_from_page_content(self) -> List[Dict[str, Any]]:
        """Strategy 4: Extract rental info from general page content"""
        try:
            # Get the main content of the page
            main_content = await self.page.query_selector('main') or await self.page.query_selector('body')
            if not main_content:
                return []
            
            text = await main_content.text_content()
            if not text:
                return []
            
            # Look for rental patterns in the text
            rental_patterns = [
                r'(\d+)\s*(?:bed|br|bedroom)',
                r'(\d+)\s*(?:bath|bathroom)',
                r'\$([\d,]+)',
                r'(\d+)\s*sq\s*ft',
                r'(apartment|condo|house|townhouse|studio)',
                r'(\d+)\s*(?:street|st|avenue|ave|road|rd|drive|dr)'
            ]
            
            # Extract what we can find
            listing = {}
            
            for pattern in rental_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    if 'bed' in pattern:
                        listing['bedrooms'] = matches[0]
                    elif 'bath' in pattern:
                        listing['bathrooms'] = matches[0]
                    elif '$' in pattern:
                        listing['price'] = f"${matches[0]}"
                    elif 'sq' in pattern:
                        listing['sqft'] = f"{matches[0]} sq ft"
                    elif pattern in ['apartment|condo|house|townhouse|studio']:
                        listing['type'] = matches[0].title()
            
            if listing:
                listing['title'] = 'Rental Property'
                listing['description'] = text[:200] + '...' if len(text) > 200 else text
                return [listing]
            
            return []
            
        except Exception as e:
            logger.warning(f"Strategy 4 failed: {e}")
            return []
    
    async def _extract_rental_details(self, element) -> Optional[Dict[str, Any]]:
        """Extract rental details from a specific element"""
        try:
            text = await element.text_content()
            if not text or len(text) < 50:  # Skip very short content
                return None
            
            # Extract rental information using regex patterns
            details = {}
            
            # Extract price
            price_match = re.search(r'\$([\d,]+)', text)
            if price_match:
                details['price'] = f"${price_match.group(1)}"
            
            # Extract bedrooms
            bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', text.lower())
            if bed_match:
                details['bedrooms'] = bed_match.group(1)
            
            # Extract bathrooms
            bath_match = re.search(r'(\d+)\s*(?:bath|bathroom)', text.lower())
            if bath_match:
                details['bathrooms'] = bath_match.group(1)
            
            # Extract square footage
            sqft_match = re.search(r'(\d+)\s*sq\s*ft', text.lower())
            if sqft_match:
                details['sqft'] = f"{sqft_match.group(1)} sq ft"
            
            # Extract property type
            type_match = re.search(r'\b(apartment|condo|house|townhouse|studio)\b', text.lower())
            if type_match:
                details['type'] = type_match.group(1).title()
            
            # Extract location/address
            address_patterns = [
                r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr|blvd|boulevard)',
                r'[\w\s]+,\s*[A-Z]{2}\s*\d{5}',  # City, ST 12345
                r'[\w\s]+(?:Oaks|Way|Street|Avenue|Road|Drive|Boulevard)',  # Specific patterns like "Rambling Oaks"
            ]
            
            for pattern in address_patterns:
                addr_match = re.search(pattern, text, re.IGNORECASE)
                if addr_match:
                    details['location'] = addr_match.group(0).strip()
                    break
            
            # Extract availability date - this is crucial!
            availability_patterns = [
                r'available\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?)',  # "Available July 15"
                r'available\s+([A-Za-z]+\s+\d{1,2})',  # "Available July 15"
                r'([A-Za-z]+\s+\d{1,2})\s+available',  # "July 15 available"
                r'move[-\s]in\s+([A-Za-z]+\s+\d{1,2})',  # "Move-in July 15"
                r'ready\s+([A-Za-z]+\s+\d{1,2})',  # "Ready July 15"
            ]
            
            for pattern in availability_patterns:
                avail_match = re.search(pattern, text, re.IGNORECASE)
                if avail_match:
                    details['available_date'] = avail_match.group(1).strip()
                    break
            
            # Extract immediate availability
            if 'immediate' in text.lower() or 'now' in text.lower():
                details['available_date'] = 'Immediate'
            
            # Extract title/description
            lines = text.split('\n')
            if lines:
                details['title'] = lines[0][:100] if lines[0] else 'Rental Property'
                details['description'] = text[:300] + '...' if len(text) > 300 else text
            
            # Only return if we found some useful information
            if len(details) >= 2:  # At least title + one other field
                return details
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract rental details: {e}")
            return None
    
    def _is_rental_content(self, text: str) -> bool:
        """Check if text contains rental-related content"""
        if not text or len(text) < 50:  # Increased minimum length
            return False
        
        # Must have at least 2 key rental indicators
        rental_keywords = [
            'rent', 'lease', 'available', 'property', 'apartment', 'condo',
            'house', 'townhouse', 'studio', 'bedroom', 'bathroom', 'sq ft',
            'monthly', 'deposit', 'move-in', 'furnished', 'unfurnished'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in rental_keywords if keyword in text_lower)
        
        # Must have at least 2 rental keywords AND some useful data
        has_useful_data = any([
            '$' in text,  # Has price
            re.search(r'\d+\s*(?:bed|br|bedroom)', text.lower()),  # Has bedrooms
            re.search(r'\d+\s*(?:bath|bathroom)', text.lower()),  # Has bathrooms
            re.search(r'\d+\s*sq\s*ft', text.lower()),  # Has square footage
        ])
        
        return keyword_count >= 2 and has_useful_data
    
    def _deduplicate_rentals(self, rentals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate rentals based on key identifying information"""
        unique_rentals = []
        seen_identifiers = set()
        
        for rental in rentals:
            # Create a unique identifier based on key fields
            location = rental.get('location', '').lower().replace('\n', ' ').strip()
            price = rental.get('price', '')
            beds = rental.get('bedrooms', '')
            baths = rental.get('bathrooms', '')
            
            # Skip rentals with no useful identifying info
            if not location and not price:
                continue
                
            # Create identifier: location + price + beds + baths
            identifier = f"{location}|{price}|{beds}|{baths}"
            
            if identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                unique_rentals.append(rental)
            else:
                logger.debug(f"Skipping duplicate rental: {identifier}")
        
        logger.info(f"Removed {len(rentals) - len(unique_rentals)} duplicate rentals")
        return unique_rentals

# Async function to use the scraper
async def scrape_rentals_with_playwright(website: str) -> List[Dict[str, Any]]:
    """Main function to scrape rentals using Playwright"""
    async with PlaywrightRentalScraper() as scraper:
        return await scraper.scrape_rental_website(website)

# Synchronous wrapper for use in your existing code
def scrape_rentals_sync(website: str) -> List[Dict[str, Any]]:
    """Synchronous wrapper for the async Playwright scraper"""
    try:
        # Check if we're already in an event loop (like in FastAPI)
        try:
            loop = asyncio.get_running_loop()
            # We're in an event loop, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, scrape_rentals_with_playwright(website))
                return future.result(timeout=60)  # 60 second timeout
        except RuntimeError:
            # No event loop running, we can use asyncio.run
            return asyncio.run(scrape_rentals_with_playwright(website))
    except Exception as e:
        logger.error(f"Failed to run Playwright scraper: {e}")
        return []

if __name__ == "__main__":
    # Test the scraper
    test_website = "https://nolenpropertiesllc.managebuilding.com"
    print(f"Testing Playwright scraper with: {test_website}")
    
    results = scrape_rentals_sync(test_website)
    print(f"Found {len(results)} rental listings:")
    
    for i, listing in enumerate(results, 1):
        print(f"\n{i}. {listing.get('title', 'Rental Property')}")
        for key, value in listing.items():
            if key != 'title':
                print(f"   {key}: {value}")
