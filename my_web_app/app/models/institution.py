from app import db
from datetime import datetime

class InstitutionType:
    COMMERCIAL_BANK = 1
    CREDIT_UNION = 2
    INVESTMENT_BANK = 3
    INSURANCE = 4
    PAYMENT_SYSTEM = 5
    OTHER = 6

class Institution(db.Model):
    __tablename__ = 'institutions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    short_name = db.Column(db.String(32), unique=True)
    institution_type = db.Column(db.Integer, default=InstitutionType.COMMERCIAL_BANK)
    group_level = db.Column(db.Integer, nullable=False)  # 1, 2, or 3
    is_active = db.Column(db.Boolean, default=True)
    address = db.Column(db.String(256))
    country = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', back_populates='institution', lazy='dynamic')
    assessments = db.relationship('Assessment', back_populates='institution', lazy='dynamic')
    observation_periods = db.relationship('ObservationPeriod', back_populates='institution', lazy='dynamic')
    
    def visible_controls(self):
        """Return all controls visible to this institution based on its group level"""
        from app.models.control import Control
        
        # Group 1 institutions see all controls (1, 2, 3)
        # Group 2 institutions see controls tagged 2 or 3
        # Group 3 institutions see only controls tagged 3
        if self.group_level == 1:
            return Control.query.filter(Control.group_level >= 1)
        elif self.group_level == 2:
            return Control.query.filter(Control.group_level >= 2)
        else:  # group_level == 3
            return Control.query.filter(Control.group_level == 3)
    
    def __repr__(self):
        return f'<Institution {self.short_name}>'