from flask import Blueprint, render_template, request
from app.services.travel_service import TravelService
from datetime import datetime, timedelta

travel_bp = Blueprint('travel', __name__, url_prefix='/hotels')

@travel_bp.route('/')
def hotel_search():
    destination = request.args.get('destination', '').strip()
    today = datetime.today()
    check_in = request.args.get('check_in', (today + timedelta(days=1)).strftime('%Y-%m-%d'))
    check_out = request.args.get('check_out', (today + timedelta(days=3)).strftime('%Y-%m-%d'))
    adults = request.args.get('adults', 2, type=int)

    hotels = []
    error = None

    if destination:
        hotels, error = TravelService.search_hotels(destination, check_in, check_out, adults)

    return render_template('pages/hotels_search.html',
                           hotels=hotels,
                           error=error,
                           destination=destination,
                           check_in=check_in,
                           check_out=check_out,
                           adults=adults)

@travel_bp.route('/<hotel_id>')
def hotel_detail(hotel_id):
    today = datetime.today()
    check_in = request.args.get('check_in', (today + timedelta(days=1)).strftime('%Y-%m-%d'))
    check_out = request.args.get('check_out', (today + timedelta(days=3)).strftime('%Y-%m-%d'))
    adults = request.args.get('adults', 2, type=int)

    hotel, error = TravelService.get_hotel_details(hotel_id, check_in, check_out, adults)
    if not hotel:
        return render_template('errors/404.html'), 404

    return render_template('pages/hotel_detail.html',
                           hotel=hotel,
                           check_in=check_in,
                           check_out=check_out,
                           adults=adults,
                           error=error)
