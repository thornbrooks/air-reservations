from flask import Blueprint, request, redirect, session, url_for
from app.models.review import Review
from app.models.home import Home
from app.models.experience import Experience
from app.models.party import Party
from app.utils.decorators import login_required

reviews_bp = Blueprint('reviews', __name__, url_prefix='/reviews')


def _update_listing_rating(listing_id, listing_type):
    reviews = Review.get_by_listing(listing_id)
    if not reviews:
        return
    avg = round(sum(r.get('rating', 0) for r in reviews) / len(reviews), 1)
    count = len(reviews)
    data = {'ratings': {'average': avg, 'count': count}}
    if listing_type == 'experience':
        Experience.update(listing_id, data)
    elif listing_type == 'party':
        Party.update(listing_id, data)
    else:
        Home.update(listing_id, data)


@reviews_bp.route('/create', methods=['POST'])
@login_required
def create_review():
    listing_id = request.form.get('listing_id')
    listing_type = request.form.get('listing_type', 'home')
    rating = request.form.get('rating', 5)
    comment = request.form.get('comment', '').strip()

    if not listing_id or not comment:
        return redirect(request.referrer or url_for('index'))

    if Review.has_reviewed(session['user_id'], listing_id):
        return redirect(request.referrer or url_for('index'))

    Review.create(session['user_id'], listing_id, listing_type, {
        'rating': rating,
        'comment': comment,
        'reviewer_name': session.get('name') or session.get('email', 'Guest'),
    })
    _update_listing_rating(listing_id, listing_type)

    listing_url = f'/{listing_type}s/{listing_id}' if listing_type != 'home' else f'/homes/{listing_id}'
    return redirect(listing_url + '#reviews')
