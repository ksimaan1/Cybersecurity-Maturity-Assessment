# app/models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.String(20))
    language = db.Column(db.String(10), default='en')  # NEW FIELD ADDED
    
    def __repr__(self):
        return f'<User {self.username}>'

class Label(db.Model):
    __tablename__ = 'label'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    en = db.Column(db.Text)  # English
    ar = db.Column(db.Text)  # Arabic
    ru = db.Column(db.Text)  # Russian
    zh = db.Column(db.Text)  # Chinese
    es = db.Column(db.Text)  # Spanish
    tg = db.Column(db.Text)  # Tajik
    fa = db.Column(db.Text)  # Farsi/Persian
    kk = db.Column(db.Text)  # Kazakh
    az = db.Column(db.Text)  # Azerbaijani
    
    @classmethod
    def get_label(cls, key, language='en'):
        """Get label in the specified language"""
        try:
            label = cls.query.filter_by(key=key).first()
            if label and hasattr(label, language) and getattr(label, language):
                return getattr(label, language)
            # Fallback to English if no translation available
            elif label and label.en:
                return label.en
        except:
            pass
        # Return the key as last resort
        return key
    
    def __repr__(self):
        return f'<Label {self.key}>'