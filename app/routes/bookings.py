import os
import stripe
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app import csrf
from app.models.booking import Booking
from app.models.home import Home
from app.models.experience import Experience
from app.models.party import Party
from app.utils.decorators import login_required

stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
SERVICE_FEE = 999  # $9.99 in cents

bookings_bp = Blueprint('bookings', __name__, url_prefix='/bookings')


def _get_listing(listing_id, listing_type):
    if listing_type == 'experience':
        return Experience.get_by_id(listing_id)
    elif listing_type == 'party':
        return Party.get_by_id(listing_id)
    return Home.get_by_id(listing_id)


@bookings_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    listing_id = request.form.get('listing_id')
    listing_type = request.form.get('listing_type', 'home')
    guests = request.form.get('guests', 1)
    check_in = request.form.get('check_in', '')
    check_out = request.form.get('check_out', '')

    listing = _get_listing(listing_id, listing_type)
    if not listing:
        return redirect(url_for('index'))

    listing_price = listing.get('price') or listing.get('ticketPrice') or 0
    listing_title = listing.get('title', 'Booking')

    base_url = request.host_url.rstrip('/')
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': listing_title,
                        'description': f'Service fee for your Air reservation',
                    },
                    'unit_amount': SERVICE_FEE,
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=f'{base_url}/bookings/success?session_id={{CHECKOUT_SESSION_ID}}&listing_id={listing_id}&listing_type={listing_type}&guests={guests}&check_in={check_in}&check_out={check_out}',
        cancel_url=f'{base_url}/{"homes" if listing_type == "home" else listing_type + "s"}/{listing_id}',
        customer_email=session.get('email'),
        metadata={
            'listing_id': listing_id,
            'listing_type': listing_type,
            'guest_id': session['user_id'],
            'check_in': check_in,
            'check_out': check_out,
            'guests': str(guests),
        }
    )
    return redirect(checkout_session.url, code=303)


@bookings_bp.route('/success')
@login_required
def success():
    stripe_session_id = request.args.get('session_id')
    listing_id = request.args.get('listing_id')
    listing_type = request.args.get('listing_type', 'home')
    guests = int(request.args.get('guests', 1))
    check_in = request.args.get('check_in', '')
    check_out = request.args.get('check_out', '')

    try:
        stripe_session = stripe.checkout.Session.retrieve(stripe_session_id)
        if stripe_session.payment_status != 'paid':
            return redirect(url_for('index'))
    except Exception:
        return redirect(url_for('index'))

    listing = _get_listing(listing_id, listing_type)
    listing_price = listing.get('price') or listing.get('ticketPrice') or 0

    booking_id = Booking.create(session['user_id'], listing_id, listing_type, {
        'check_in': check_in,
        'check_out': check_out,
        'guests': guests,
        'total_price': listing_price * guests,
        'payment_id': stripe_session.payment_intent,
    })
    Booking.update_status(booking_id, 'confirmed')

    booking = Booking.get_by_id(booking_id)
    return render_template('pages/booking_confirmation.html',
                           booking=booking,
                           listing=listing,
                           service_fee=SERVICE_FEE / 100)


@bookings_bp.route('/<booking_id>/confirmation')
@login_required
def confirmation(booking_id):
    booking = Booking.get_by_id(booking_id)
    if not booking or booking.get('guestId') != session['user_id']:
        return redirect(url_for('index'))
    listing = _get_listing(booking.get('listingId', ''), booking.get('listingType', 'home'))
    return render_template('pages/booking_confirmation.html', booking=booking, listing=listing, service_fee=9.99)


@bookings_bp.route('/<booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.get_by_id(booking_id)
    if booking and booking.get('guestId') == session['user_id'] and booking.get('status') != 'cancelled':
        Booking.update_status(booking_id, 'cancelled')
    return redirect(url_for('bookings.my_bookings'))

@bookings_bp.route('/my-bookings')
@login_required
def my_bookings():
    bookings = Booking.get_by_guest(session['user_id'])
    return render_template('pages/my_bookings.html', bookings=bookings)


@bookings_bp.route('/api/ai/start-call', methods=['POST'])
@csrf.exempt
@login_required
def start_ai_call():
    from app.services.ai_service import RetellAIService
    data = request.get_json()
    agent_id = data.get('agent_id')
    listing_id = data.get('listing_id')
    token = RetellAIService.create_call_token(agent_id, session['user_id'], listing_id)
    if token:
        return jsonify({'access_token': token})
    return jsonify({'error': 'Could not start call'}), 500
