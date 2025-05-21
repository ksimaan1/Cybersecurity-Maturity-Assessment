from app import db
from datetime import datetime

class Label(db.Model):
    __tablename__ = 'labels'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), nullable=False, unique=True)
    section = db.Column(db.String(64))  # For grouping labels by functional area
    
    # Languages supported (10)
    en = db.Column(db.Text)  # English
    ar = db.Column(db.Text)  # Arabic
    ru = db.Column(db.Text)  # Russian
    zh = db.Column(db.Text)  # Chinese
    es = db.Column(db.Text)  # Spanish
    tg = db.Column(db.Text)  # Tajik
    fa = db.Column(db.Text)  # Farsi
    kk = db.Column(db.Text)  # Kazakh
    az = db.Column(db.Text)  # Azerbaijani
    fr = db.Column(db.Text)  # French (Additional option)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_text(self, language_code):
        """Get the label text for the specified language code"""
        if hasattr(self, language_code):
            text = getattr(self, language_code)
            if text:
                return text
        
        # Fall back to English if requested language is not available
        return self.en
    
    def __repr__(self):
        return f'<Label {self.key}>'