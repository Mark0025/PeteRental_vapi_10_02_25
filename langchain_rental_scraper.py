#!/usr/bin/env python3
"""
LangChain-based Rental Scraper using Playwright Tools
Intelligent rental data extraction with AI-powered understanding
"""

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from langchain_community.tools.playwright import (
    NavigateTool, ExtractTextTool, GetElementsTool, ClickTool, CurrentWebPageTool
)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from playwright.async_api import async_playwright
from pydantic import BaseModel, Field, ValidationError
import json
import re
import os

class RentalListing(BaseModel):
    """Structured rental listing data"""
    title: str = Field(description="Property title or name")
    address: str = Field(description="Full property address")
    city: str = Field(description="City name")
    state: str = Field(description="State abbreviation")
    zip_code: str = Field(description="ZIP code")
    price: str = Field(description="Monthly rent price")
    bedrooms: int = Field(description="Number of bedrooms")
    bathrooms: int = Field(description="Number of bathrooms")
    square_feet: Optional[str] = Field(description="Square footage if available")
    property_type: str = Field(description="Type of property (apartment, condo, house, etc.)")
    available_date: str = Field(description="When the property becomes available")
    description: str = Field(description="Property description")
    amenities: Optional[List[str]] = Field(description="List of amenities if available")

class LangChainRentalScraper:
    """Intelligent rental scraper using LangChain Playwright tools"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.navigate_tool = None
        self.extract_text_tool = None
        self.get_elements_tool = None
        self.click_tool = None
        self.current_page_tool = None
        
        # Initialize LLM for rental extraction
        self.llm = None
        self.rental_parser = None
        
    async def initialize(self):
        """Initialize the Playwright browser and tools"""
        try:
            # Launch browser
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
            
            # Initialize tools with the browser instance
            self.navigate_tool = NavigateTool(async_browser=self.browser)
            self.extract_text_tool = ExtractTextTool(async_browser=self.browser)
            self.get_elements_tool = GetElementsTool(async_browser=self.browser)
            self.click_tool = ClickTool(async_browser=self.browser)
            self.current_page_tool = CurrentWebPageTool(async_browser=self.browser)
            
            # Initialize LLM for rental extraction using OpenRouter
            api_key = os.getenv("OPENROUTER_API_KEY")
            if api_key:
                try:
                    self.llm = ChatOpenAI(
                        model="openai/gpt-4o",  # OpenRouter will auto-route to best available
                        temperature=0,
                        openai_api_key=api_key,
                        base_url="https://openrouter.ai/api/v1",
                        default_headers={
                            "HTTP-Referer": "https://peterental-vapi.local",
                            "X-Title": "PeteRental VAPI"
                        }
                    )
                    
                    # Set up rental extraction prompt and parser
                    self.rental_parser = self._setup_rental_parser()
                    logger.info("✅ LLM agent initialized with OpenRouter")
                except Exception as e:
                    logger.warning(f"Failed to initialize LLM agent: {e}")
                    self.llm = None
                    self.rental_parser = None
            else:
                logger.warning("OPENROUTER_API_KEY not set, LLM agent disabled")
                self.llm = None
                self.rental_parser = None
            
            logger.info("✅ LangChain Playwright tools and LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}")
            raise
    
    def _setup_rental_parser(self):
        """Set up the rental extraction prompt and parser"""
        prompt = ChatPromptTemplate.from_template("""
        You are an expert rental property analyst. Extract all available rental properties from the following text.

        IMPORTANT RULES:
        1. Extract ONLY currently available rental properties (not office info, not sign-in pages)
        2. Each property should have a unique address
        3. Skip any entries that are not actual rental properties
        4. Focus on properties with complete information (price, beds, baths, availability)

        TEXT TO ANALYZE:
        {text}

        Return the data as a JSON array of rental objects with this exact structure:
        [
          {{
            "address": "full street address including unit number if available",
            "price": "monthly rent price (e.g., $975, $1,400)",
            "bedrooms": number,
            "bathrooms": number,
            "square_feet": "square footage if available",
            "available_date": "when the property becomes available",
            "property_type": "apartment/condo/house/townhouse"
          }}
        ]

        Only return valid JSON. If no rentals found, return empty array [].
        """)
        
        return prompt | self.llm | JsonOutputParser()
    
    async def scrape_rentals(self, website: str) -> List[Dict[str, Any]]:
        """Scrape rental listings using LangChain Playwright tools"""
        try:
            await self.initialize()
            
            logger.info(f"🌐 Using LangChain Playwright tools to scrape: {website}")
            
            # Navigate to the website
            await self.page.goto(website, wait_until="networkidle")
            logger.info(f"✅ Navigated to {website}")
            
            # Get the current page content
            page_title = await self.page.title()
            logger.info(f"✅ Got page info: {page_title}")
            
            # Extract text from the page
            page_text = await self.page.text_content("body")
            logger.info(f"✅ Extracted {len(page_text)} characters of text")
            
            # Look for rental-specific elements
            rental_elements = await self.page.query_selector_all("[class*='rental'], [class*='listing'], [class*='property'], [class*='unit'], [class*='card']")
            logger.info(f"✅ Found {len(rental_elements)} potential rental elements")
            
            # Use LLM agent to extract rental data from the page content
            if self.rental_parser:
                try:
                    logger.info("🤖 Using LLM agent to extract rental information...")
                    rentals = await self.rental_parser.ainvoke({"text": page_text})
                    
                    if isinstance(rentals, list):
                        logger.info(f"✅ LLM agent extracted {len(rentals)} rental listings")
                        return rentals
                    else:
                        logger.warning("LLM returned non-list format, attempting to parse...")
                        if isinstance(rentals, str):
                            # Try to extract JSON from string response
                            import json
                            try:
                                parsed_rentals = json.loads(rentals)
                                if isinstance(parsed_rentals, list):
                                    return parsed_rentals
                            except:
                                pass
                        
                        logger.error("Failed to parse LLM response")
                        return []
                        
                except Exception as e:
                    logger.error(f"LLM extraction failed: {e}")
                    # Fallback to regex method
                    logger.info("🔄 Falling back to regex extraction...")
                    return self._extract_rentals_from_text(page_text)
            else:
                logger.info("🔄 LLM agent not available, using regex extraction...")
                return self._extract_rentals_from_text(page_text)
            
        except Exception as e:
            logger.error(f"LangChain scraping failed: {e}")
            return []
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            logger.info("✅ Browser resources cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    def _extract_rentals_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract rental information from page text using intelligent parsing"""
        try:
            # Look for rental card patterns - each rental is typically separated by clear boundaries
            rental_patterns = [
                # Pattern 1: Address followed by details
                r'(\d+\s+[\w\s]+(?:Oaks|Way|Street|Avenue|Road|Drive|Boulevard)[^$]*?)(?=\d+\s+[\w\s]+(?:Oaks|Way|Street|Avenue|Road|Drive|Boulevard)|$)',
                # Pattern 2: Price followed by details
                r'(\$\d+(?:,\d+)?[^$]*?)(?=\$\d+(?:,\d+)?|$)',
                # Pattern 3: Bed/Bath followed by details
                r'((?:\d+\s*(?:Bed|Bath|bed|bath))[^$]*?)(?=(?:\d+\s*(?:Bed|Bath|bed|bath))|$)',
            ]
            
            all_rentals = []
            
            for pattern in rental_patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 50:  # Only process substantial matches
                        rental_data = self._extract_single_rental(match.strip())
                        if rental_data and len(rental_data) >= 4:  # Must have at least 4 fields
                            all_rentals.append(rental_data)
            
            # Also try to find rentals by looking for key rental sections
            sections = text.split('\n\n')  # Split by double newlines
            for section in sections:
                if len(section.strip()) > 100:  # Only substantial sections
                    if any(keyword in section.lower() for keyword in ['bed', 'bath', 'sq ft', '$', 'available']):
                        rental_data = self._extract_single_rental(section)
                        if rental_data and len(rental_data) >= 4:
                            all_rentals.append(rental_data)
            
            # Remove duplicates and return
            unique_rentals = self._deduplicate_rentals(all_rentals)
            
            logger.info(f"Extracted {len(unique_rentals)} unique rentals from text")
            return unique_rentals
            
        except Exception as e:
            logger.error(f"Failed to extract rentals from text: {e}")
            return []
    
    def _extract_single_rental(self, text: str) -> Dict[str, Any]:
        """Extract complete rental information from a single rental section"""
        try:
            rental = {}
            
            # Clean the text first - remove HTML artifacts and normalize
            clean_text = self._clean_text(text)
            
            # Extract price - look for $ followed by numbers (fix truncated prices)
            price_match = re.search(r'\$([\d,]+(?:,\d+)?)', clean_text)
            if price_match:
                rental['price'] = f"${price_match.group(1)}"
            
            # Extract bedrooms
            bed_match = re.search(r'(\d+)\s*(?:Bed|bed|BR|br)', clean_text)
            if bed_match:
                rental['bedrooms'] = int(bed_match.group(1))
            
            # Extract bathrooms
            bath_match = re.search(r'(\d+)\s*(?:Bath|bath|BA|ba)', clean_text)
            if bath_match:
                rental['bathrooms'] = int(bath_match.group(1))
            
            # Extract square footage
            sqft_match = re.search(r'(\d+)\s*sq\s*ft', clean_text, re.IGNORECASE)
            if sqft_match:
                rental['square_feet'] = f"{sqft_match.group(1)} sq ft"
            
            # Extract availability date - multiple patterns
            avail_patterns = [
                r'Available\s+([A-Za-z]+\s+\d{1,2})',
                r'AVAILABLE\s+([A-ZA-Z]+\s+\d{1,2})',
                r'available\s+([A-Za-z]+\s+\d{1,2})',
                r'([A-Za-z]+\s+\d{1,2})\s+available',
            ]
            
            for pattern in avail_patterns:
                avail_match = re.search(pattern, clean_text, re.IGNORECASE)
                if avail_match:
                    rental['available_date'] = avail_match.group(1).strip()
                    break
            
            # Extract complete address using helper method
            complete_address = self._extract_complete_address(clean_text)
            if complete_address:
                rental['address'] = complete_address
            
            # Extract city and state from the full text
            city_state_match = re.search(r',\s*([A-Za-z\s]+),\s*([A-Z]{2})\s*(\d{5})', clean_text)
            if city_state_match:
                rental['city'] = city_state_match.group(1).strip()
                rental['state'] = city_state_match.group(2).strip()
                rental['zip_code'] = city_state_match.group(3).strip()
            
            # Extract property type
            type_match = re.search(r'\b(apartment|condo|house|townhouse|studio)\b', clean_text, re.IGNORECASE)
            if type_match:
                rental['property_type'] = type_match.group(1).title()
            
            # Create a clean description
            rental['description'] = self._create_clean_description(clean_text)
            
            # Set clean title based on address
            if 'address' in rental:
                rental['title'] = rental['address']
            else:
                rental['title'] = 'Rental Property'
            
            # Simple check: exclude office addresses
            description = rental.get('description', '').lower()
            if any(keyword in description for keyword in ['resident sign in', 'email address', 'password', 'system']):
                return {}
            
            # Clean up title to just show address
            if 'address' in rental:
                rental['title'] = rental['address']
            
            return rental
            
        except Exception as e:
            logger.error(f"Failed to extract single rental: {e}")
            return {}
    
    def _clean_text(self, text: str) -> str:
        """Clean HTML artifacts and normalize text"""
        # Remove HTML tags and artifacts
        clean = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace and newlines
        clean = re.sub(r'\s+', ' ', clean)
        # Remove special characters that aren't useful
        clean = re.sub(r'[^\w\s\$\-,\.,]', '', clean)
        # Normalize spacing around commas and periods
        clean = re.sub(r'\s*([,\.])\s*', r'\1 ', clean)
        return clean.strip()
    
    def _create_clean_description(self, text: str) -> str:
        """Create a clean, readable description"""
        # Look for the actual property description
        desc_patterns = [
            r'(?:This|Newly remodeled|Available)[^\.]+\.',
            r'(?:bedroom|bathroom|condo|apartment|home)[^\.]+\.',
            r'(?:Features|Residents have access to)[^\.]+\.',
        ]
        
        for pattern in desc_patterns:
            desc_match = re.search(pattern, text, re.IGNORECASE)
            if desc_match:
                desc = desc_match.group(0).strip()
                # Clean up the description
                desc = re.sub(r'\s+', ' ', desc)
                desc = desc[:300] + '...' if len(desc) > 300 else desc
                return desc
        
        # Fallback: use the first meaningful sentence
        sentences = text.split('.')
        for sentence in sentences:
            if len(sentence.strip()) > 20 and any(keyword in sentence.lower() for keyword in ['bed', 'bath', 'sq ft', 'available']):
                return sentence.strip()[:300] + '...' if len(sentence.strip()) > 300 else sentence.strip()
        
        return text[:200] + '...' if len(text) > 200 else text
    
    def _extract_complete_address(self, text: str) -> str:
        """Extract complete address including unit numbers and suffixes"""
        # Look for complete address patterns
        address_patterns = [
            # Pattern 1: Full address with unit (e.g., "1000 Rambling Oaks - 12")
            r'(\d+\s+[\w\s]+(?:Oaks|Way|Street|Avenue|Road|Drive|Boulevard)(?:\s*-\s*\d+)?)',
            # Pattern 2: Full address with direction (e.g., "13910 Crossing Way East - 1")
            r'(\d+\s+[\w\s]+(?:Oaks|Way|Street|Avenue|Road|Drive|Boulevard)\s+(?:East|West|North|South|N|S|E|W)(?:\s*-\s*\d+)?)',
            # Pattern 3: Standard street address
            r'(\d+\s+[\w\s]+(?:Street|Avenue|Road|Drive|Boulevard|Blvd|St|Ave|Rd|Dr))',
        ]
        
        for pattern in address_patterns:
            addr_match = re.search(pattern, text, re.IGNORECASE)
            if addr_match:
                address = addr_match.group(1).strip()
                # Clean up the address
                address = re.sub(r'\s+', ' ', address)  # Remove extra whitespace
                return address
        
        return ""
    
    def _deduplicate_rentals(self, rentals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate rentals based on key identifying information"""
        unique_rentals = []
        seen_identifiers = set()
        
        for rental in rentals:
            # Create a unique identifier based on key fields
            location = rental.get('address', '').lower().replace('\n', ' ').strip()
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

# Synchronous wrapper for easy integration
def scrape_rentals_with_langchain(website: str) -> List[Dict[str, Any]]:
    """Synchronous wrapper for the async LangChain scraper"""
    try:
        scraper = LangChainRentalScraper()
        return asyncio.run(scraper.scrape_rentals(website))
    except Exception as e:
        logger.error(f"Failed to run LangChain scraper: {e}")
        return []

if __name__ == "__main__":
    # Test the LangChain scraper
    test_website = "https://nolenpropertiesllc.managebuilding.com"
    print(f"Testing LangChain Playwright tools with: {test_website}")
    
    results = scrape_rentals_with_langchain(test_website)
    print(f"Found {len(results)} rental listings:")
    
    for i, listing in enumerate(results, 1):
        print(f"\n{i}. {listing.get('title', 'Rental Property')}")
        for key, value in listing.items():
            if key != 'title':
                print(f"   {key}: {value}")
