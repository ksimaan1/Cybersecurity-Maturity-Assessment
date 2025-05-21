from app import db
from datetime import datetime

class ControlType:
    PHYSICAL = 1
    HUMAN = 2
    TECHNICAL = 3
    ADMINISTRATIVE = 4
    PROCEDURAL = 5

class ControlStatus:
    ACTIVE = 1
    DEPRECATED = 2
    DRAFT = 3

class ControlGroup(db.Model):
    __tablename__ = 'control_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    standard = db.Column(db.String(64))  # e.g., ISO27002, NIST CSF, CIS
    version = db.Column(db.String(32))   # e.g., v1.0, 2022
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    controls = db.relationship('Control', back_populates='group', lazy='dynamic')
    
    def __repr__(self):
        return f'<ControlGroup {self.name}>'

class Control(db.Model):
    __tablename__ = 'controls'
    
    id = db.Column(db.Integer, primary_key=True)
    control_id = db.Column(db.String(32), nullable=False, index=True)  # E.g., "ISO-5.1.3"
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    objective = db.Column(db.Text)
    group_id = db.Column(db.Integer, db.ForeignKey('control_groups.id'))
    control_type = db.Column(db.Integer, default=ControlType.TECHNICAL)
    group_level = db.Column(db.Integer, nullable=False)  # 1, 2, or 3 (applicability)
    status = db.Column(db.Integer, default=ControlStatus.ACTIVE)
    version = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = db.relationship('ControlGroup', back_populates='controls')
    assessments = db.relationship('Assessment', back_populates='control', lazy='dynamic')
    observation_ratings = db.relationship('ObservationRating', back_populates='control', lazy='dynamic')
    
    def __repr__(self):
        return f'<Control {self.control_id}: {self.name}>'
    
    @property
    def control_type_name(self):
        types = {
            ControlType.PHYSICAL: "Physical",
            ControlType.HUMAN: "Human",
            ControlType.TECHNICAL: "Technical",
            ControlType.ADMINISTRATIVE: "Administrative",
            ControlType.PROCEDURAL: "Procedural"
        }
        return types.get(self.control_type, "Unknown")