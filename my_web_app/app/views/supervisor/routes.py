from functools import wraps
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.views.supervisor import supervisor
from app.models.institution import Institution
from app.models.control import Control, ControlGroup
from app.models.assessment import Assessment
from app.models.observation import ObservationPeriod, ObservationRating
from app.models.user import Role
from datetime import datetime, date
from sqlalchemy import func

# Supervisor access decorator
def supervisor_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_supervisor:
            flash('Access denied. This area is for supervisors only.')
            return redirect(url_for('bank.index'))
        return f(*args, **kwargs)
    return decorated_function

@supervisor.route('/')
@supervisor_required
def index():
    # Get count of institutions
    institutions_count = Institution.query.filter_by(is_active=True).count()
    
    # Get count of all controls
    total_controls = Control.query.count()
    
    # Get active observation periods
    active_periods = ObservationPeriod.query.filter(
        ObservationPeriod.start_date <= date.today(),
        ObservationPeriod.end_date >= date.today()
    ).count()
    
    # Get institutions with recent assessments (updated in last 30 days)
    thirty_days_ago = datetime.utcnow().date().replace(day=datetime.utcnow().date().day - 30)
    active_institutions = db.session.query(func.count(func.distinct(Assessment.institution_id))).filter(
        Assessment.updated_at >= thirty_days_ago
    ).scalar()
    
    return render_template('supervisor/index.html', 
                          title='Supervisor Dashboard',
                          institutions_count=institutions_count,
                          total_controls=total_controls,
                          active_periods=active_periods,
                          active_institutions=active_institutions)

@supervisor.route('/institutions')
@supervisor_required
def institutions():
    # Get all institutions
    institutions = Institution.query.order_by(Institution.name).all()
    
    return render_template('supervisor/institutions.html',
                          title='Institutions',
                          institutions=institutions)

@supervisor.route('/institution/<int:institution_id>')
@supervisor_required
def institution_detail(institution_id):
    # Get the institution
    institution = Institution.query.get_or_404(institution_id)
    
    # Get latest assessments for this institution
    assessments = Assessment.query.filter_by(
        institution_id=institution.id
    ).order_by(Assessment.updated_at.desc()).all()
    
    # Group assessments by control group for easier display
    grouped_assessments = {}
    for assessment in assessments:
        control = assessment.control
        if control.group not in grouped_assessments:
            grouped_assessments[control.group] = []
        
        grouped_assessments[control.group].append(assessment)
    
    # Get observation periods for this institution
    observation_periods = ObservationPeriod.query.filter_by(
        institution_id=institution.id
    ).order_by(ObservationPeriod.end_date.desc()).all()
    
    return render_template('supervisor/institution_detail.html',
                          title=f'Institution: {institution.name}',
                          institution=institution,
                          grouped_assessments=grouped_assessments,
                          observation_periods=observation_periods)

@supervisor.route('/controls')
@supervisor_required
def controls():
    # Get all control groups
    groups = ControlGroup.query.order_by(ControlGroup.name).all()
    
    # Get all controls grouped by control group
    grouped_controls = {}
    for group in groups:
        grouped_controls[group] = Control.query.filter_by(group_id=group.id).all()
    
    return render_template('supervisor/controls.html',
                          title='Controls Management',
                          grouped_controls=grouped_controls)

@supervisor.route('/control/<int:control_id>')
@supervisor_required
def control_detail(control_id):
    # Get the control
    control = Control.query.get_or_404(control_id)
    
    # Get institutions with assessments for this control
    assessments = Assessment.query.filter_by(
        control_id=control.id
    ).order_by(Assessment.maturity_level.desc()).all()
    
    return render_template('supervisor/control_detail.html',
                          title=f'Control: {control.control_id}',
                          control=control,
                          assessments=assessments)

@supervisor.route('/observation_periods')
@supervisor_required
def observation_periods():
    # Get all observation periods
    periods = ObservationPeriod.query.order_by(ObservationPeriod.end_date.desc()).all()
    
    return render_template('supervisor/observation_periods.html',
                          title='Observation Periods',
                          periods=periods)

@supervisor.route('/observation_period/<int:period_id>')
@supervisor_required
def observation_period_detail(period_id):
    # Get the period
    period = ObservationPeriod.query.get_or_404(period_id)
    
    # Get ratings
    ratings = ObservationRating.query.filter_by(
        observation_period_id=period.id
    ).all()
    
    # Group ratings by control group for easier display
    grouped_ratings = {}
    for rating in ratings:
        control = rating.control
        if control.group not in grouped_ratings:
            grouped_ratings[control.group] = []
        
        grouped_ratings[control.group].append(rating)
    
    return render_template('supervisor/observation_period_detail.html',
                          title=f'Observation: {period.title}',
                          period=period,
                          grouped_ratings=grouped_ratings)

@supervisor.route('/observation_period/create', methods=['GET', 'POST'])
@supervisor_required
def create_observation_period():
    if request.method == 'POST':
        # Create new observation period
        period = ObservationPeriod(
            institution_id=request.form.get('institution_id'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
            title=request.form.get('title'),
            description=request.form.get('description'),
            status='Planned',
            is_visible_to_institution=False,  # Not visible by default
            created_by=current_user.id
        )
        
        db.session.add(period)
        db.session.commit()
        
        flash('Observation period created successfully.')
        return redirect(url_for('supervisor.observation_period_detail', period_id=period.id))
    
    # GET request - show form
    institutions = Institution.query.filter_by(is_active=True).order_by(Institution.name).all()
    
    return render_template('supervisor/create_observation_period.html',
                          title='Create Observation Period',
                          institutions=institutions)

@supervisor.route('/observation_rating/update/<int:rating_id>', methods=['POST'])
@supervisor_required
def update_observation_rating(rating_id):
    # Get the rating
    rating = ObservationRating.query.get_or_404(rating_id)
    
    # Update rating data
    rating.maturity_level = float(request.form.get('maturity_level', rating.maturity_level))
    rating.comment = request.form.get('comment', rating.comment)
    rating.required_action = request.form.get('required_action', rating.required_action)
    rating.is_visible_to_institution = 'is_visible' in request.form
    
    db.session.commit()
    
    flash('Observation rating updated successfully.')
    return redirect(url_for('supervisor.observation_period_detail', period_id=rating.observation_period_id))

@supervisor.route('/observation_period/toggle_visibility/<int:period_id>', methods=['POST'])
@supervisor_required
def toggle_period_visibility(period_id):
    # Get the period
    period = ObservationPeriod.query.get_or_404(period_id)
    
    # Toggle visibility
    period.is_visible_to_institution = not period.is_visible_to_institution
    
    db.session.commit()
    
    flash(f'Observation period is now {"visible" if period.is_visible_to_institution else "hidden"} to the institution.')
    return redirect(url_for('supervisor.observation_period_detail', period_id=period.id))

@supervisor.route('/observation_rating/create/<int:period_id>', methods=['POST'])
@supervisor_required
def create_observation_rating(period_id):
    # Get the period
    period = ObservationPeriod.query.get_or_404(period_id)
    
    # Create new rating
    rating = ObservationRating(
        observation_period_id=period.id,
        control_id=request.form.get('control_id'),
        maturity_level=float(request.form.get('maturity_level', 1.0)),
        comment=request.form.get('comment', ''),
        required_action=request.form.get('required_action', ''),
        is_visible_to_institution=False,  # Not visible by default
        created_by=current_user.id
    )
    
    db.session.add(rating)
    db.session.commit()
    
    flash('Observation rating created successfully.')
    return redirect(url_for('supervisor.observation_period_detail', period_id=period.id))

@supervisor.route('/control/create', methods=['GET', 'POST'])
@supervisor_required
def create_control():
    if request.method == 'POST':
        # Create new control
        control = Control(
            control_id=request.form.get('control_id'),
            name=request.form.get('name'),
            description=request.form.get('description'),
            objective=request.form.get('objective'),
            group_id=request.form.get('group_id'),
            control_type=request.form.get('control_type'),
            group_level=request.form.get('group_level'),
            status=request.form.get('status', 1),  # Default to active
            version=request.form.get('version', '1.0')
        )
        
        db.session.add(control)
        db.session.commit()
        
        flash('Control created successfully.')
        return redirect(url_for('supervisor.control_detail', control_id=control.id))
    
    # GET request - show form
    groups = ControlGroup.query.order_by(ControlGroup.name).all()
    
    return render_template('supervisor/create_control.html',
                          title='Create Control',
                          groups=groups)

@supervisor.route('/institution/create', methods=['GET', 'POST'])
@supervisor_required
def create_institution():
    if request.method == 'POST':
        # Create new institution
        institution = Institution(
            name=request.form.get('name'),
            short_name=request.form.get('short_name'),
            institution_type=request.form.get('institution_type'),
            group_level=request.form.get('group_level'),
            is_active=True,
            address=request.form.get('address'),
            country=request.form.get('country')
        )
        
        db.session.add(institution)
        db.session.commit()
        
        flash('Institution created successfully.')
        return redirect(url_for('supervisor.institution_detail', institution_id=institution.id))
    
    # GET request - show form
    return render_template('supervisor/create_institution.html',
                          title='Create Institution')

@supervisor.route('/reports')
@supervisor_required
def reports():
    return render_template('supervisor/reports.html',
                          title='Reports')

@supervisor.route('/report/maturity_by_institution')
@supervisor_required
def maturity_by_institution():
    # Get all institutions
    institutions = Institution.query.filter_by(is_active=True).order_by(Institution.name).all()
    
    # For each institution, calculate average maturity
    data = []
    for institution in institutions:
        avg_maturity = db.session.query(func.avg(Assessment.maturity_level)).filter(
            Assessment.institution_id == institution.id
        ).scalar() or 0
        
        data.append({
            'institution': institution,
            'average_maturity': round(avg_maturity, 2),
            'assessments_count': Assessment.query.filter_by(institution_id=institution.id).count()
        })
    
    # Sort by average maturity (descending)
    data.sort(key=lambda x: x['average_maturity'], reverse=True)
    
    return render_template('supervisor/report_maturity_by_institution.html',
                          title='Maturity by Institution',
                          data=data)

@supervisor.route('/report/controls_by_maturity')
@supervisor_required
def controls_by_maturity():
    # Get all controls
    controls = Control.query.all()
    
    # For each control, calculate average maturity across institutions
    data = []
    for control in controls:
        avg_maturity = db.session.query(func.avg(Assessment.maturity_level)).filter(
            Assessment.control_id == control.id
        ).scalar() or 0
        
        data.append({
            'control': control,
            'average_maturity': round(avg_maturity, 2),
            'assessments_count': Assessment.query.filter_by(control_id=control.id).count()
        })
    
    # Sort by average maturity (ascending)
    data.sort(key=lambda x: x['average_maturity'])
    
    return render_template('supervisor/report_controls_by_maturity.html',
                          title='Controls by Maturity',
                          data=data)