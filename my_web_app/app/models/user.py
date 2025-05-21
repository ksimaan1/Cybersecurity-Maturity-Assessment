from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# User roles
class Role:
    BANK_USER = 1
    SUPERVISOR = 2
    ADMIN = 3

# Employment status
class EmploymentStatus:
    ACTIVE = 1
    ON_LEAVE = 2
    TERMINATED = 3

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    department = db.Column(db.String(128))
    role = db.Column(db.Integer, default=Role.BANK_USER)  # Default to bank user
    employment_status = db.Column(db.Integer, default=EmploymentStatus.ACTIVE)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    institution = db.relationship('Institution', back_populates='users')
    assessments = db.relationship('Assessment', back_populates='user', lazy='dynamic')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_supervisor(self):
        return self.role >= Role.SUPERVISOR
    
    @property
    def is_admin(self):
        return self.role == Role.ADMIN
    
    @property
    def is_active_employee(self):
        return self.employment_status == EmploymentStatus.ACTIVE
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))