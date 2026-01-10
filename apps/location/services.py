"""
Location Service
Handles reverse geocoding and service area validation
"""
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from django.core.cache import cache
from datetime import timedelta
import logging
import hashlib

logger = logging.getLogger(__name__)

class LocationService:
    
    # Nominatim geolocator (OpenStreetMap)
    geolocator = Nominatim(
        user_agent="ecommerce_nizamabad_v1",
        timeout=5
    )
    
    # Cache geocode results for 7 days
    CACHE_TTL = 60 * 60 * 24 * 7
    
    @classmethod
    def reverse_geocode(cls, latitude, longitude):
        """
        Convert coordinates to location details
        Uses caching to reduce API calls
        """
        # Generate cache key
        cache_key = cls._get_cache_key(latitude, longitude)
        
        # Check cache
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Geocode cache hit for {latitude}, {longitude}")
            return cached_result
        
        # Call geocoding API
        try:
            location = cls.geolocator.reverse(
                f"{latitude}, {longitude}",
                language='en',
                exactly_one=True
            )
            
            if not location:
                raise ValueError("No location found for coordinates")
            
            # Parse address components
            address = location.raw.get('address', {})
            
            result = {
                'city': cls._extract_city(address),
                'district': address.get('state_district', ''),
                'state': address.get('state', ''),
                'country': address.get('country', ''),
                'full_address': location.address,
                'latitude': latitude,
                'longitude': longitude
            }
            
            # Cache result
            cache.set(cache_key, result, cls.CACHE_TTL)
            
            logger.info(f"Geocoded: {result['city']}, {result['state']}")
            return result
        
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding API error: {e}")
            raise ValueError("Location service temporarily unavailable")
        
        except Exception as e:
            logger.error(f"Geocoding failed: {e}")
            raise ValueError("Unable to verify location")
    
    @classmethod
    def _extract_city(cls, address):
        """
        Extract city name from address components
        Handles various OSM naming conventions
        """
        # Try different city fields
        for field in ['city', 'town', 'village', 'municipality', 'suburb']:
            if field in address:
                return address[field]
        
        # Fallback to county or state_district
        return address.get('county', address.get('state_district', ''))
    
    @classmethod
    def _get_cache_key(cls, lat, long):
        """
        Generate cache key for coordinates
        Rounded to 4 decimal places (~11m precision)
        """
        lat_rounded = round(lat, 4)
        long_rounded = round(long, 4)
        key_str = f"geocode:{lat_rounded}:{long_rounded}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @classmethod
    def validate_coordinates(cls, latitude, longitude):
        """
        Basic coordinate validation
        Check if within India's approximate bounds
        """
        # India bounds (approximate)
        INDIA_LAT_MIN = 6.5
        INDIA_LAT_MAX = 35.5
        INDIA_LONG_MIN = 68.0
        INDIA_LONG_MAX = 97.5
        
        if not (INDIA_LAT_MIN <= latitude <= INDIA_LAT_MAX):
            raise ValueError("Latitude out of India bounds")
        
        if not (INDIA_LONG_MIN <= longitude <= INDIA_LONG_MAX):
            raise ValueError("Longitude out of India bounds")
        
        return True
    
    @classmethod
    def check_service_availability(cls, geocoded_data):
        """
        Check if location is within any active service area
        Returns (is_available, matched_area, denial_reason)
        """
        from apps.location.models import ServiceArea
        
        # Get all active service areas
        active_areas = ServiceArea.objects.filter(is_active=True)
        
        if not active_areas.exists():
            return False, None, "Service not yet available in any region"
        
        # Check each service area
        for area in active_areas:
            if area.matches_location(geocoded_data):
                return True, area, None
        
        # Build denial message
        available_areas = [str(area) for area in active_areas[:3]]
        denial_reason = (
            f"Service not available in {geocoded_data.get('city', 'your location')}, "
            f"{geocoded_data.get('state', '')}. "
            f"Currently serving: {', '.join(available_areas)}"
        )
        
        return False, None, denial_reason
