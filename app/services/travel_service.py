import os
import requests

GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
PLACES_BASE = 'https://places.googleapis.com/v1/places'


def _photo_url(photo_name, max_width=600):
    if not photo_name:
        return None
    return f'https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx={max_width}&key={GOOGLE_API_KEY}'


class TravelService:

    @staticmethod
    def search_hotels(destination, check_in=None, check_out=None, adults=2):
        if not GOOGLE_API_KEY:
            return [], 'GOOGLE_PLACES_API_KEY not configured in .env'
        try:
            resp = requests.post(
                f'{PLACES_BASE}:searchText',
                headers={
                    'X-Goog-Api-Key': GOOGLE_API_KEY,
                    'X-Goog-FieldMask': 'places.id,places.displayName,places.rating,places.userRatingCount,places.photos,places.formattedAddress,places.priceLevel,places.shortFormattedAddress',
                    'Content-Type': 'application/json',
                },
                json={
                    'textQuery': f'hotels in {destination}',
                    'includedType': 'hotel',
                    'maxResultCount': 20,
                    'languageCode': 'en',
                },
                timeout=15,
            )
            data = resp.json()
            if 'error' in data:
                return [], data['error'].get('message', 'Google Places error')

            hotels = []
            for p in data.get('places', []):
                photos = p.get('photos', [])
                photo_url = _photo_url(photos[0]['name']) if photos else None
                price_level = p.get('priceLevel', '')
                price_display = {
                    'PRICE_LEVEL_FREE': 'Free',
                    'PRICE_LEVEL_INEXPENSIVE': '$',
                    'PRICE_LEVEL_MODERATE': '$$',
                    'PRICE_LEVEL_EXPENSIVE': '$$$',
                    'PRICE_LEVEL_VERY_EXPENSIVE': '$$$$',
                }.get(price_level, '')
                hotels.append({
                    'id': p.get('id'),
                    'name': p.get('displayName', {}).get('text', 'Unknown Hotel'),
                    'address': p.get('shortFormattedAddress', p.get('formattedAddress', '')),
                    'rating': p.get('rating'),
                    'review_count': p.get('userRatingCount', 0),
                    'price_level': price_display,
                    'photo': photo_url,
                })
            return hotels, None
        except Exception as e:
            return [], str(e)

    @staticmethod
    def get_hotel_details(hotel_id, check_in=None, check_out=None, adults=2):
        if not GOOGLE_API_KEY:
            return None, 'GOOGLE_PLACES_API_KEY not configured'
        try:
            resp = requests.get(
                f'{PLACES_BASE}/{hotel_id}',
                headers={
                    'X-Goog-Api-Key': GOOGLE_API_KEY,
                    'X-Goog-FieldMask': 'id,displayName,rating,userRatingCount,formattedAddress,photos,priceLevel,reviews,websiteUri,nationalPhoneNumber,regularOpeningHours,editorialSummary',
                },
                timeout=15,
            )
            data = resp.json()
            if 'error' in data:
                return None, data['error'].get('message', 'Hotel not found')

            photos = data.get('photos', [])
            price_level = data.get('priceLevel', '')
            price_display = {
                'PRICE_LEVEL_FREE': 'Free',
                'PRICE_LEVEL_INEXPENSIVE': '$',
                'PRICE_LEVEL_MODERATE': '$$',
                'PRICE_LEVEL_EXPENSIVE': '$$$',
                'PRICE_LEVEL_VERY_EXPENSIVE': '$$$$',
            }.get(price_level, '')

            reviews = []
            for r in data.get('reviews', [])[:5]:
                reviews.append({
                    'author': r.get('authorAttribution', {}).get('displayName', 'Guest'),
                    'rating': r.get('rating'),
                    'text': r.get('text', {}).get('text', ''),
                    'time': r.get('relativePublishTimeDescription', ''),
                })

            return {
                'id': hotel_id,
                'name': data.get('displayName', {}).get('text', ''),
                'address': data.get('formattedAddress', ''),
                'rating': data.get('rating'),
                'review_count': data.get('userRatingCount', 0),
                'price_level': price_display,
                'phone': data.get('nationalPhoneNumber', ''),
                'website': data.get('websiteUri', ''),
                'summary': data.get('editorialSummary', {}).get('text', ''),
                'photos': [_photo_url(p['name'], 800) for p in photos[:8]],
                'reviews': reviews,
            }, None
        except Exception as e:
            return None, str(e)
