from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.views.bank import bank
from app.models.control import Control
from app.models.assessment import Assessment, ImprovementPlan, ProgressUpdate
from app.models.observation import ObservationPeriod, ObservationRating
from app.models.user import Role
from datetime import datetime, date
from sqlalchemy import func
import calendar
from functools import wraps  # Add this import

# Bank user access decorator - FIXED with wraps to preserve function name
def bank_required(f):
    @wraps(f)  # Add this decorator to preserve the original function name
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.is_supervisor:
            flash('Access denied. This area is for bank users only.')
            return redirect(url_for('supervisor.index'))
        return f(*args, **kwargs)
    return decorated_function

@bank.route('/')
@bank_required
def index():
    # Get institution details
    institution = current_user.institution
    
    # Get count of all controls visible to this institution
    total_controls = institution.visible_controls().count()
    
    # Get count of assessed controls
    assessed_controls = db.session.query(func.count(Assessment.id)).filter(
        Assessment.institution_id == institution.id
    ).scalar() or 0
    
    # Calculate completion percentage
    completion_percentage = int((assessed_controls / total_controls * 100) if total_controls > 0 else 0)
    
    # Get upcoming improvement activities
    today = date.today()
    upcoming_activities = ImprovementPlan.query.join(Assessment).filter(
        Assessment.institution_id == institution.id,
        ImprovementPlan.status.in_(['Planned', 'In Progress']),
        ImprovementPlan.target_date >= today
    ).order_by(ImprovementPlan.target_date).limit(5).all()
    
    # Get active observation periods
    observation_periods = ObservationPeriod.query.filter(
        ObservationPeriod.institution_id == institution.id,
        ObservationPeriod.is_visible_to_institution == True
    ).order_by(ObservationPeriod.end_date.desc()).limit(3).all()
    
    return render_template('bank/index.html', 
                          title='Dashboard',
                          institution=institution,
                          total_controls=total_controls,
                          assessed_controls=assessed_controls,
                          completion_percentage=completion_percentage,
                          upcoming_activities=upcoming_activities,
                          observation_periods=observation_periods)

@bank.route('/controls')
@bank_required
def controls():
    # Get all controls visible to this institution
    institution = current_user.institution
    controls = institution.visible_controls().all()
    
    # Get existing assessments for these controls
    assessments = {}
    assessment_records = Assessment.query.filter(
        Assessment.institution_id == institution.id
    ).all()
    
    for assessment in assessment_records:
        assessments[assessment.control_id] = assessment
    
    return render_template('bank/controls.html',
                          title='Controls',
                          controls=controls,
                          assessments=assessments)

@bank.route('/control/<int:control_id>')
@bank_required
def control_detail(control_id):
    # Get the control
    control = Control.query.get_or_404(control_id)
    
    # Check if the control is visible to this institution
    institution = current_user.institution
    if control not in institution.visible_controls():
        flash('You do not have access to this control.')
        return redirect(url_for('bank.controls'))
    
    # Get existing assessment
    assessment = Assessment.query.filter_by(
        institution_id=institution.id,
        control_id=control.id
    ).first()
    
    # Get improvement plans if assessment exists
    improvement_plans = []
    if assessment:
        improvement_plans = ImprovementPlan.query.filter_by(
            assessment_id=assessment.id
        ).order_by(ImprovementPlan.target_date).all()
    
    # Get supervisor ratings that are visible to the institution
    supervisor_ratings = ObservationRating.query.join(ObservationPeriod).filter(
        ObservationRating.control_id == control.id,
        ObservationPeriod.institution_id == institution.id,
        ObservationPeriod.is_visible_to_institution == True,
        ObservationRating.is_visible_to_institution == True
    ).order_by(ObservationPeriod.end_date.desc()).all()
    
    return render_template('bank/control_detail.html',
                          title=f'Control: {control.control_id}',
                          control=control,
                          assessment=assessment,
                          improvement_plans=improvement_plans,
                          supervisor_ratings=supervisor_ratings)

@bank.route('/assessment/update/<int:control_id>', methods=['POST'])
@bank_required
def update_assessment(control_id):
    # Get the control
    control = Control.query.get_or_404(control_id)
    
    # Check if the control is visible to this institution
    institution = current_user.institution
    if control not in institution.visible_controls():
        flash('You do not have access to this control.')
        return redirect(url_for('bank.controls'))
    
    # Get or create assessment
    assessment = Assessment.query.filter_by(
        institution_id=institution.id,
        control_id=control.id
    ).first()
    
    if not assessment:
        assessment = Assessment(
            institution_id=institution.id,
            control_id=control.id,
            user_id=current_user.id
        )
        db.session.add(assessment)
    
    # Update assessment data
    assessment.maturity_level = float(request.form.get('maturity_level', 1.0))
    assessment.comment = request.form.get('comment', '')
    assessment.user_id = current_user.id  # Update the last editor
    
    db.session.commit()
    flash('Assessment updated successfully.')
    
    return redirect(url_for('bank.control_detail', control_id=control.id))

@bank.route('/improvement_plan/add/<int:control_id>', methods=['POST'])
@bank_required
def add_improvement_plan(control_id):
    # Get the assessment
    assessment = Assessment.query.filter_by(
        institution_id=current_user.institution_id,
        control_id=control_id
    ).first_or_404()
    
    # Create new improvement plan
    plan = ImprovementPlan(
        assessment_id=assessment.id,
        activity=request.form.get('activity', ''),
        target_date=datetime.strptime(request.form.get('target_date'), '%Y-%m-%d').date(),
        status='Planned'
    )
    
    db.session.add(plan)
    db.session.commit()
    
    flash('Improvement plan added successfully.')
    return redirect(url_for('bank.control_detail', control_id=control_id))

@bank.route('/improvement_plan/update/<int:plan_id>', methods=['POST'])
@bank_required
def update_improvement_plan(plan_id):
    # Get the plan
    plan = ImprovementPlan.query.get_or_404(plan_id)
    
    # Ensure the plan belongs to this institution
    assessment = Assessment.query.get(plan.assessment_id)
    if assessment.institution_id != current_user.institution_id:
        flash('Access denied.')
        return redirect(url_for('bank.index'))
    
    # Update plan
    plan.activity = request.form.get('activity', plan.activity)
    plan.target_date = datetime.strptime(request.form.get('target_date', str(plan.target_date)), '%Y-%m-%d').date()
    plan.status = request.form.get('status', plan.status)
    plan.completion_percentage = int(request.form.get('completion_percentage', plan.completion_percentage))
    
    # Add progress update if completion percentage changed
    old_percentage = plan.completion_percentage
    new_percentage = int(request.form.get('completion_percentage', old_percentage))
    
    if new_percentage != old_percentage:
        update = ProgressUpdate(
            improvement_plan_id=plan.id,
            update_date=date.today(),
            completion_percentage=new_percentage,
            comment=request.form.get('update_comment', ''),
            created_by=current_user.id
        )
        db.session.add(update)
    
    db.session.commit()
    
    flash('Improvement plan updated successfully.')
    return redirect(url_for('bank.control_detail', control_id=assessment.control_id))

@bank.route('/observation_periods')
@bank_required
def observation_periods():
    # Get observation periods visible to this institution
    periods = ObservationPeriod.query.filter(
        ObservationPeriod.institution_id == current_user.institution_id,
        ObservationPeriod.is_visible_to_institution == True
    ).order_by(ObservationPeriod.end_date.desc()).all()
    
    return render_template('bank/observation_periods.html',
                          title='Observation Periods',
                          periods=periods)

@bank.route('/observation_period/<int:period_id>')
@bank_required
def observation_period_detail(period_id):
    # Get the period
    period = ObservationPeriod.query.get_or_404(period_id)
    
    # Ensure the period is for this institution and is visible
    if period.institution_id != current_user.institution_id or not period.is_visible_to_institution:
        flash('Access denied.')
        return redirect(url_for('bank.observation_periods'))
    
    # Get ratings
    ratings = ObservationRating.query.filter(
        ObservationRating.observation_period_id == period.id,
        ObservationRating.is_visible_to_institution == True
    ).all()
    
    # Group ratings by control group for easier display
    grouped_ratings = {}
    for rating in ratings:
        control = rating.control
        if control.group not in grouped_ratings:
            grouped_ratings[control.group] = []
        
        grouped_ratings[control.group].append(rating)
    
    return render_template('bank/observation_period_detail.html',
                          title=f'Observation: {period.title}',
                          period=period,
                          grouped_ratings=grouped_ratings)