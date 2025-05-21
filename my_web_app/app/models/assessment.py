from app import db
from datetime import datetime

class Assessment(db.Model):
    __tablename__ = 'assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    control_id = db.Column(db.Integer, db.ForeignKey('controls.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    maturity_level = db.Column(db.Float, default=1.0)  # Level 1-4 with 5% increments
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    institution = db.relationship('Institution', back_populates='assessments')
    control = db.relationship('Control', back_populates='assessments')
    user = db.relationship('User', back_populates='assessments')
    improvement_plans = db.relationship('ImprovementPlan', back_populates='assessment', lazy='dynamic')
    
    @property
    def maturity_display(self):
        """Format maturity for display, e.g., '1.25' becomes 'Level 1 (25%)'"""
        base_level = int(self.maturity_level)
        percentage = int((self.maturity_level - base_level) * 100)
        return f"Level {base_level} ({percentage}%)"
    
    def __repr__(self):
        return f'<Assessment {self.id}: {self.maturity_level}>'

class ImprovementPlan(db.Model):
    __tablename__ = 'improvement_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    activity = db.Column(db.Text, nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), default='Planned')  # Planned, In Progress, Completed, Canceled
    completion_percentage = db.Column(db.Integer, default=0)  # 0-100
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assessment = db.relationship('Assessment', back_populates='improvement_plans')
    progress_updates = db.relationship('ProgressUpdate', back_populates='improvement_plan', lazy='dynamic')
    
    @property
    def is_overdue(self):
        return self.target_date < datetime.now().date() and self.status != 'Completed'
    
    def __repr__(self):
        return f'<ImprovementPlan {self.id}: {self.status}>'

class ProgressUpdate(db.Model):
    __tablename__ = 'progress_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    improvement_plan_id = db.Column(db.Integer, db.ForeignKey('improvement_plans.id'), nullable=False)
    update_date = db.Column(db.Date, nullable=False)
    completion_percentage = db.Column(db.Integer, nullable=False)  # 0-100
    comment = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    improvement_plan = db.relationship('ImprovementPlan', back_populates='progress_updates')
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<ProgressUpdate {self.id}: {self.completion_percentage}%>'

class MaturityRating(db.Model):
    """Defines the meaning of each maturity level"""
    __tablename__ = 'maturity_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer, nullable=False)  # 1-4
    name = db.Column(db.String(64), nullable=False)  # e.g., "Initial", "Managed", "Defined", "Optimized"
    description = db.Column(db.Text)
    criteria = db.Column(db.Text)
    
    def __repr__(self):
        return f'<MaturityRating {self.level}: {self.name}>'