from flask import jsonify, request, current_app
from app import db
from app.api import api
from app.models.user import User, Role
from app.models.institution import Institution
from app.models.control import Control, ControlGroup
from app.models.assessment import Assessment, ImprovementPlan
from app.models.observation import ObservationPeriod, ObservationRating
from app.models.language import Label
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from datetime import datetime, date
from sqlalchemy import func

# Helper function to check if user has supervisor role
def is_supervisor():
    user_identity = get_jwt_identity()
    return user_identity.get('role', 0) >= Role.SUPERVISOR

# Schemas for serialization and validation
class ControlSchema(Schema):
    id = fields.Int(dump_only=True)
    control_id = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str()
    objective = fields.Str()
    group_id = fields.Int(required=True)
    control_type = fields.Int()
    group_level = fields.Int(required=True)
    status = fields.Int()
    version = fields.Str()

class AssessmentSchema(Schema):
    id = fields.Int(dump_only=True)
    institution_id = fields.Int(required=True)
    control_id = fields.Int(required=True)
    maturity_level = fields.Float(required=True)
    comment = fields.Str()

class ImprovementPlanSchema(Schema):
    id = fields.Int(dump_only=True)
    assessment_id = fields.Int(required=True)
    activity = fields.Str(required=True)
    target_date = fields.Date(required=True)
    status = fields.Str()
    completion_percentage = fields.Int()

class ObservationPeriodSchema(Schema):
    id = fields.Int(dump_only=True)
    institution_id = fields.Int(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    title = fields.Str(required=True)
    description = fields.Str()
    status = fields.Str()
    is_visible_to_institution = fields.Bool()

class ObservationRatingSchema(Schema):
    id = fields.Int(dump_only=True)
    observation_period_id = fields.Int(required=True)
    control_id = fields.Int(required=True)
    maturity_level = fields.Float(required=True)
    comment = fields.Str()
    required_action = fields.Str()
    is_visible_to_institution = fields.Bool()

# Initialize schemas
control_schema = ControlSchema()
controls_schema = ControlSchema(many=True)
assessment_schema = AssessmentSchema()
assessments_schema = AssessmentSchema(many=True)
improvement_plan_schema = ImprovementPlanSchema()
improvement_plans_schema = ImprovementPlanSchema(many=True)
observation_period_schema = ObservationPeriodSchema()
observation_periods_schema = ObservationPeriodSchema(many=True)
observation_rating_schema = ObservationRatingSchema()
observation_ratings_schema = ObservationRatingSchema(many=True)

# API routes

# Controls
@api.route('/controls', methods=['GET'])
@jwt_required()
def get_controls():
    user_identity = get_jwt_identity()
    user_role = user_identity.get('role', 0)
    institution_id = user_identity.get('institution_id', 0)
    
    if user_role >= Role.SUPERVISOR:
        # Supervisors see all controls
        controls = Control.query.all()
    else:
        # Bank users see only controls based on their institution's group level
        institution = Institution.query.get(institution_id)
        if not institution:
            return jsonify({'message': 'Institution not found'}), 404
        
        controls = institution.visible_controls().all()
    
    return jsonify(controls_schema.dump(controls))

@api.route('/controls/<int:control_id>', methods=['GET'])
@jwt_required()
def get_control(control_id):
    user_identity = get_jwt_identity()
    user_role = user_identity.get('role', 0)
    institution_id = user_identity.get('institution_id', 0)
    
    control = Control.query.get_or_404(control_id)
    
    # If not supervisor, check if control is visible to this institution
    if user_role < Role.SUPERVISOR:
        institution = Institution.query.get(institution_id)
        if not institution:
            return jsonify({'message': 'Institution not found'}), 404
        
        if control not in institution.visible_controls():
            return jsonify({'message': 'Access denied'}), 403
    
    return jsonify(control_schema.dump(control))

@api.route('/controls', methods=['POST'])
@jwt_required()
def create_control():
    # Only supervisors can create controls
    if not is_supervisor():
        return jsonify({'message': 'Access denied'}), 403
    
    try:
        data = control_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    control = Control(
        control_id=data['control_id'],
        name=data['name'],
        description=data.get('description', ''),
        objective=data.get('objective', ''),
        group_id=data['group_id'],
        control_type=data.get('control_type', 1),
        group_level=data['group_level'],
        status=data.get('status', 1),
        version=data.get('version', '1.0')
    )
    
    db.session.add(control)
    db.session.commit()
    
    return jsonify(control_schema.dump(control)), 201

@api.route('/controls/<int:control_id>', methods=['PUT'])
@jwt_required()
def update_control(control_id):
    # Only supervisors can update controls
    if not is_supervisor():
        return jsonify({'message': 'Access denied'}), 403
    
    control = Control.query.get_or_404(control_id)
    
    try:
        data = control_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    # Update control fields
    for key, value in data.items():
        setattr(control, key, value)
    
    db.session.commit()
    
    return jsonify(control_schema.dump(control))

# Assessments
@api.route('/institutions/<int:institution_id>/assessments', methods=['GET'])
@jwt_required()
def get_institution_assessments(institution_id):
    user_identity = get_jwt_identity()
    user_role = user_identity.get('role', 0)
    user_institution_id = user_identity.get('institution_id', 0)
    
    # If not supervisor, check if accessing own institution
    if user_role < Role.SUPERVISOR and user_institution_id != institution_id:
        return jsonify({'message': 'Access denied'}), 403
    
    assessments = Assessment.query.filter_by(institution_id=institution_id).all()
    
    return jsonify(assessments_schema.dump(assessments))

@api.route('/assessments', methods=['POST'])
@jwt_required()
def create_assessment():
    user_identity = get_jwt_identity()
    user_id = user_identity.get('user_id', 0)
    user_role = user_identity.get('role', 0)
    user_institution_id = user_identity.get('institution_id', 0)
    
    try:
        data = assessment_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    # Bank users can only create assessments for their own institution
    if user_role < Role.SUPERVISOR and data['institution_id'] != user_institution_id:
        return jsonify({'message': 'You can only create assessments for your own institution'}), 403
    
    # Check if control is accessible to this institution
    institution = Institution.query.get_or_404(data['institution_id'])
    control = Control.query.get_or_404(data['control_id'])
    
    if user_role < Role.SUPERVISOR and control not in institution.visible_controls():
        return jsonify({'message': 'This control is not applicable to your institution'}), 403
    
    # Check if assessment already exists
    existing = Assessment.query.filter_by(
        institution_id=data['institution_id'],
        control_id=data['control_id']
    ).first()
    
    if existing:
        # Update existing assessment
        existing.maturity_level = data['maturity_level']
        existing.comment = data.get('comment', existing.comment)
        existing.user_id = user_id
        db.session.commit()
        
        return jsonify(assessment_schema.dump(existing))
    
    # Create new assessment
    assessment = Assessment(
        institution_id=data['institution_id'],
        control_id=data['control_id'],
        maturity_level=data['maturity_level'],
        comment=data.get('comment', ''),
        user_id=user_id
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    return jsonify(assessment_schema.dump(assessment)), 201

# Improvement Plans
@api.route('/assessments/<int:assessment_id>/improvement_plans', methods=['GET'])
@jwt_required()
def get_improvement_plans(assessment_id):
    user_identity = get_jwt_identity()
    user_role = user_identity.get('role', 0)
    user_institution_id = user_identity.get('institution_id', 0)
    
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # If not supervisor, check if accessing own institution
    if user_role < Role.SUPERVISOR and assessment.institution_id != user_institution_id:
        return jsonify({'message': 'Access denied'}), 403
    
    plans = ImprovementPlan.query.filter_by(assessment_id=assessment_id).all()
    
    return jsonify(improvement_plans_schema.dump(plans))

@api.route('/improvement_plans', methods=['POST'])
@jwt_required()
def create_improvement_plan():
    user_identity = get_jwt_identity()
    user_id = user_identity.get('user_id', 0)
    user_role = user_identity.get('role', 0)
    user_institution_id = user_identity.get('institution_id', 0)
    
    try:
        data = improvement_plan_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    assessment = Assessment.query.get_or_404(data['assessment_id'])
    
    # Bank users can only create plans for their own institution
    if user_role < Role.SUPERVISOR and assessment.institution_id != user_institution_id:
        return jsonify({'message': 'You can only create plans for your own institution'}), 403
    
    plan = ImprovementPlan(
        assessment_id=data['assessment_id'],
        activity=data['activity'],
        target_date=data['target_date'],
        status=data.get('status', 'Planned'),
        completion_percentage=data.get('completion_percentage', 0)
    )
    
    db.session.add(plan)
    db.session.commit()
    
    return jsonify(improvement_plan_schema.dump(plan)), 201

# Observation Periods (Supervisor only)
@api.route('/observation_periods', methods=['GET'])
@jwt_required()
def get_observation_periods():
    user_identity = get_jwt_identity()
    user_role = user_identity.get('role', 0)
    user_institution_id = user_identity.get('institution_id', 0)
    
    if user_role >= Role.SUPERVISOR:
        # Supervisors see all periods
        periods = ObservationPeriod.query.all()
    else:
        # Bank users see only visible periods for their institution
        periods = ObservationPeriod.query.filter_by(
            institution_id=user_institution_id,
            is_visible_to_institution=True
        ).all()
    
    return jsonify(observation_periods_schema.dump(periods))

@api.route('/observation_periods', methods=['POST'])
@jwt_required()
def create_observation_period():
    # Only supervisors can create observation periods
    if not is_supervisor():
        return jsonify({'message': 'Access denied'}), 403
    
    user_identity = get_jwt_identity()
    user_id = user_identity.get('user_id', 0)
    
    try:
        data = observation_period_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    period = ObservationPeriod(
        institution_id=data['institution_id'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        title=data['title'],
        description=data.get('description', ''),
        status=data.get('status', 'Planned'),
        is_visible_to_institution=data.get('is_visible_to_institution', False),
        created_by=user_id
    )
    
    db.session.add(period)
    db.session.commit()
    
    return jsonify(observation_period_schema.dump(period)), 201

# Observation Ratings (Supervisor only)
@api.route('/observation_periods/<int:period_id>/ratings', methods=['GET'])
@jwt_required()
def get_observation_ratings(period_id):
    user_identity = get_jwt_identity()
    user_role = user_identity.get('role', 0)
    user_institution_id = user_identity.get('institution_id', 0)
    
    period = ObservationPeriod.query.get_or_404(period_id)
    
    if user_role >= Role.SUPERVISOR:
        # Supervisors see all ratings
        ratings = ObservationRating.query.filter_by(observation_period_id=period_id).all()
    else:
        # Bank users see only visible ratings and only if the period is for their institution
        if period.institution_id != user_institution_id:
            return jsonify({'message': 'Access denied'}), 403
        
        if not period.is_visible_to_institution:
            return jsonify({'message': 'This observation period is not visible to your institution'}), 403
        
        ratings = ObservationRating.query.filter_by(
            observation_period_id=period_id,
            is_visible_to_institution=True
        ).all()
    
    return jsonify(observation_ratings_schema.dump(ratings))

@api.route('/observation_ratings', methods=['POST'])
@jwt_required()
def create_observation_rating():
    # Only supervisors can create observation ratings
    if not is_supervisor():
        return jsonify({'message': 'Access denied'}), 403
    
    user_identity = get_jwt_identity()
    user_id = user_identity.get('user_id', 0)
    
    try:
        data = observation_rating_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    rating = ObservationRating(
        observation_period_id=data['observation_period_id'],
        control_id=data['control_id'],
        maturity_level=data['maturity_level'],
        comment=data.get('comment', ''),
        required_action=data.get('required_action', ''),
        is_visible_to_institution=data.get('is_visible_to_institution', False),
        created_by=user_id
    )
    
    db.session.add(rating)
    db.session.commit()
    
    return jsonify(observation_rating_schema.dump(rating)), 201

# Language labels
@api.route('/labels', methods=['GET'])
def get_labels():
    language = request.args.get('language', 'en')
    section = request.args.get('section')
    
    query = Label.query
    
    if section:
        query = query.filter_by(section=section)
    
    labels = query.all()
    
    result = {}
    for label in labels:
        result[label.key] = getattr(label, language, None) or label.en
    
    return jsonify(result)

@api.route('/languages', methods=['GET'])
def get_languages():
    languages = [
        {'code': 'en', 'name': 'English'},
        {'code': 'ar', 'name': 'Arabic'},
        {'code': 'ru', 'name': 'Russian'},
        {'code': 'zh', 'name': 'Chinese'},
        {'code': 'es', 'name': 'Spanish'},
        {'code': 'tg', 'name': 'Tajik'},
        {'code': 'fa', 'name': 'Farsi'},
        {'code': 'kk', 'name': 'Kazakh'},
        {'code': 'az', 'name': 'Azerbaijani'},
        {'code': 'fr', 'name': 'French'}
    ]
    
    return jsonify(languages)

# Statistics and dashboard data
@api.route('/stats/institution/<int:institution_id>', methods=['GET'])
@jwt_required()
def institution_stats(institution_id):
    user_identity = get_jwt_identity()
    user_role = user_identity.get('role', 0)
    user_institution_id = user_identity.get('institution_id', 0)
    
    # If not supervisor, check if accessing own institution
    if user_role < Role.SUPERVISOR and user_institution_id != institution_id:
        return jsonify({'message': 'Access denied'}), 403
    
    institution = Institution.query.get_or_404(institution_id)
    
    # Get count of all controls visible to this institution
    total_controls = institution.visible_controls().count()
    
    # Get count of assessed controls
    assessed_controls = db.session.query(func.count(Assessment.id)).filter(
        Assessment.institution_id == institution.id
    ).scalar() or 0
    
    # Calculate completion percentage
    completion_percentage = int((assessed_controls / total_controls * 100) if total_controls > 0 else 0)
    
    # Calculate average maturity
    avg_maturity = db.session.query(func.avg(Assessment.maturity_level)).filter(
        Assessment.institution_id == institution.id
    ).scalar() or 0
    
    # Get improvement plans by status
    plan_stats = {}
    statuses = ['Planned', 'In Progress', 'Completed', 'Canceled']
    
    for status in statuses:
        count = db.session.query(func.count(ImprovementPlan.id)).join(Assessment).filter(
            Assessment.institution_id == institution.id,
            ImprovementPlan.status == status
        ).scalar() or 0
        
        plan_stats[status] = count
    
    return jsonify({
        'institution_name': institution.name,
        'group_level': institution.group_level,
        'total_controls': total_controls,
        'assessed_controls': assessed_controls,
        'completion_percentage': completion_percentage,
        'average_maturity': round(avg_maturity, 2),
        'improvement_plans': plan_stats
    })

@api.route('/stats/system', methods=['GET'])
@jwt_required()
def system_stats():
    # Only supervisors can access system-wide stats
    if not is_supervisor():
        return jsonify({'message': 'Access denied'}), 403
    
    # Count of active institutions
    institutions_count = Institution.query.filter_by(is_active=True).count()
    
    # Count of controls by group level
    controls_by_level = {}
    for level in [1, 2, 3]:
        controls_by_level[f'group_{level}'] = Control.query.filter_by(group_level=level).count()
    
    # Count of active observation periods
    active_periods = ObservationPeriod.query.filter(
        ObservationPeriod.start_date <= date.today(),
        ObservationPeriod.end_date >= date.today()
    ).count()
    
    # Count of assessments in last 30 days
    thirty_days_ago = datetime.utcnow().date().replace(day=datetime.utcnow().date().day - 30)
    recent_assessments = Assessment.query.filter(
        Assessment.updated_at >= thirty_days_ago
    ).count()
    
    return jsonify({
        'institutions_count': institutions_count,
        'controls_count': sum(controls_by_level.values()),
        'controls_by_level': controls_by_level,
        'active_observation_periods': active_periods,
        'recent_assessments': recent_assessments
    })