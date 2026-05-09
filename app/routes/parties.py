from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models.party import Party
from app.services.storage_service import StorageService
from app.services.ai_service import RetellAIService
from app.utils.decorators import login_required, host_required

parties_bp = Blueprint('parties', __name__, url_prefix='/parties')

@parties_bp.route('/')
def list_parties():
    parties = Party.get_all_published()
    return render_template('pages/parties_list.html', parties=parties)

@parties_bp.route('/<party_id>')
def view_party(party_id):
    from app.models.review import Review
    party = Party.get_by_id(party_id)
    if not party:
        return render_template('errors/404.html'), 404
    reviews = Review.get_by_listing(party_id)
    already_reviewed = Review.has_reviewed(session.get('user_id', ''), party_id) if session.get('user_id') else False
    return render_template('pages/listing_detail.html', listing=party, listing_type='party',
                           reviews=reviews, already_reviewed=already_reviewed)

@parties_bp.route('/create', methods=['GET', 'POST'])
@login_required
@host_required
def create_party():
    if request.method == 'POST':
        images = []
        if 'images' in request.files:
            images = StorageService.upload_multiple(
                request.files.getlist('images'),
                f"parties/{session['user_id']}"
            )
        ai_enabled = request.form.get('ai_enabled') == 'on'
        listing_data = {
            **request.form.to_dict(),
            'images': images,
            'ai_enabled': ai_enabled,
        }
        party_id = Party.create(session['user_id'], listing_data)
        if ai_enabled:
            agent_id = RetellAIService.create_agent(party_id, 'party', listing_data)
            if agent_id:
                Party.update(party_id, {'aiConfig': {'enabled': True, 'agentId': agent_id}})
        return redirect(url_for('parties.view_party', party_id=party_id))
    return render_template('pages/create_listing.html', listing_type='party')

@parties_bp.route('/<party_id>/edit', methods=['GET', 'POST'])
@login_required
@host_required
def edit_party(party_id):
    party = Party.get_by_id(party_id)
    if not party or party.get('hostId') != session['user_id']:
        return redirect(url_for('index'))
    if request.method == 'POST':
        images = party.get('images', [])
        if 'images' in request.files and request.files.getlist('images')[0].filename:
            images = StorageService.upload_multiple(
                request.files.getlist('images'),
                f"parties/{session['user_id']}"
            )
        Party.update(party_id, {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'eventType': request.form.get('event_type', 'other'),
            'dateTime': request.form.get('date_time', ''),
            'ticketPrice': float(request.form.get('ticket_price', 0)),
            'capacity': int(request.form.get('capacity', 100)),
            'location': {
                'address': request.form.get('address', ''),
                'city': request.form.get('city', ''),
                'country': request.form.get('country', ''),
            },
            'images': images,
        })
        return redirect(url_for('parties.view_party', party_id=party_id))
    return render_template('pages/create_listing.html', listing=party, listing_type='party')

@parties_bp.route('/<party_id>/publish', methods=['POST'])
@login_required
@host_required
def publish_party(party_id):
    party = Party.get_by_id(party_id)
    if party and party.get('hostId') == session['user_id']:
        Party.update(party_id, {'status': 'published'})
    return redirect(url_for('parties.view_party', party_id=party_id))
