from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models.experience import Experience
from app.services.storage_service import StorageService
from app.services.ai_service import RetellAIService
from app.utils.decorators import login_required, host_required

experiences_bp = Blueprint('experiences', __name__, url_prefix='/experiences')

@experiences_bp.route('/')
def list_experiences():
    experiences = Experience.get_all_published()
    return render_template('pages/experiences_list.html', experiences=experiences)

@experiences_bp.route('/<exp_id>')
def view_experience(exp_id):
    from app.models.review import Review
    experience = Experience.get_by_id(exp_id)
    if not experience:
        return render_template('errors/404.html'), 404
    reviews = Review.get_by_listing(exp_id)
    already_reviewed = Review.has_reviewed(session.get('user_id', ''), exp_id) if session.get('user_id') else False
    return render_template('pages/listing_detail.html', listing=experience, listing_type='experience',
                           reviews=reviews, already_reviewed=already_reviewed)

@experiences_bp.route('/create', methods=['GET', 'POST'])
@login_required
@host_required
def create_experience():
    if request.method == 'POST':
        images = []
        if 'images' in request.files:
            images = StorageService.upload_multiple(
                request.files.getlist('images'),
                f"experiences/{session['user_id']}"
            )
        ai_enabled = request.form.get('ai_enabled') == 'on'
        listing_data = {
            **request.form.to_dict(),
            'images': images,
            'ai_enabled': ai_enabled,
        }
        exp_id = Experience.create(session['user_id'], listing_data)
        if ai_enabled:
            agent_id = RetellAIService.create_agent(exp_id, 'experience', listing_data)
            if agent_id:
                Experience.update(exp_id, {'aiConfig': {'enabled': True, 'agentId': agent_id}})
        return redirect(url_for('experiences.view_experience', exp_id=exp_id))
    return render_template('pages/create_listing.html', listing_type='experience')

@experiences_bp.route('/<exp_id>/edit', methods=['GET', 'POST'])
@login_required
@host_required
def edit_experience(exp_id):
    experience = Experience.get_by_id(exp_id)
    if not experience or experience.get('hostId') != session['user_id']:
        return redirect(url_for('index'))
    if request.method == 'POST':
        images = experience.get('images', [])
        if 'images' in request.files and request.files.getlist('images')[0].filename:
            images = StorageService.upload_multiple(
                request.files.getlist('images'),
                f"experiences/{session['user_id']}"
            )
        Experience.update(exp_id, {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'category': request.form.get('category', 'other'),
            'price': float(request.form.get('price', 0)),
            'duration': {
                'value': int(request.form.get('duration_value', 2)),
                'unit': request.form.get('duration_unit', 'hours'),
            },
            'maxGroupSize': int(request.form.get('max_group_size', 10)),
            'location': {
                'address': request.form.get('address', ''),
                'city': request.form.get('city', ''),
                'country': request.form.get('country', ''),
            },
            'images': images,
        })
        return redirect(url_for('experiences.view_experience', exp_id=exp_id))
    return render_template('pages/create_listing.html', listing=experience, listing_type='experience')

@experiences_bp.route('/<exp_id>/publish', methods=['POST'])
@login_required
@host_required
def publish_experience(exp_id):
    experience = Experience.get_by_id(exp_id)
    if experience and experience.get('hostId') == session['user_id']:
        Experience.update(exp_id, {'status': 'published'})
    return redirect(url_for('experiences.view_experience', exp_id=exp_id))
