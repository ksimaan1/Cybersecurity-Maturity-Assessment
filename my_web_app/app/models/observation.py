from app import db
from datetime import datetime

class ObservationPeriod(db.Model):
    __tablename__ = 'observation_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(32), default='Planned')  # Planned, In Progress, Completed
    is_visible_to_institution = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    institution = db.relationship('Institution', back_populates='observation_periods')
    creator = db.relationship('User')
    observation_ratings = db.relationship('ObservationRating', back_populates='observation_period', lazy='dynamic')
    
    def __repr__(self):
        return f'<ObservationPeriod {self.id}: {self.title}>'

class ObservationRating(db.Model):
    __tablename__ = 'observation_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    observation_period_id = db.Column(db.Integer, db.ForeignKey('observation_periods.id'), nullable=False)
    control_id = db.Column(db.Integer, db.ForeignKey('controls.id'), nullable=False)
    maturity_level = db.Column(db.Float, default=1.0)  # Level 1-4 with 5% increments
    comment = db.Column(db.Text)
    required_action = db.Column(db.Text)
    is_visible_to_institution = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    observation_period = db.relationship('ObservationPeriod', back_populates='observation_ratings')
    control = db.relationship('Control', back_populates='observation_ratings')
    creator = db.relationship('User')
    
    @property
    def maturity_display(self):
        """Format maturity for display, e.g., '1.25' becomes 'Level 1 (25%)'"""
        base_level = int(self.maturity_level)
        percentage = int((self.maturity_level - base_level) * 100)
        return f"Level {base_level} ({percentage}%)"
    
    def __repr__(self):
        return f'<ObservationRating {self.id}: {self.maturity_level}>'