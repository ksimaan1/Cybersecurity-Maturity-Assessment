from flask import render_template, redirect, url_for, flash, session, request
from flask_login import current_user, login_required
from app import db
from app.views.main import main
from app.models.language import Label

@main.route('/')
def index():
    # Redirect authenticated users to their appropriate dashboard
    if current_user.is_authenticated:
        if current_user.is_supervisor:
            return redirect(url_for('supervisor.index'))
        else:
            return redirect(url_for('bank.index'))
    
    # For unauthenticated users, show the welcome page
    return render_template('main/index.html', title='Welcome')

@main.route('/about')
def about():
    return render_template('main/about.html', title='About')

@main.route('/help')
def help():
    return render_template('main/help.html', title='Help & Documentation')

@main.context_processor
def inject_language():
    def get_label(key, default=None):
        """Get a label in the current language"""
        lang = session.get('language', 'en')
        label = Label.query.filter_by(key=key).first()
        
        if not label:
            return default or key
        
        text = getattr(label, lang, None)
        if not text:
            # Fall back to English if translation is missing
            text = label.en or default or key
            
        return text
    
    return {
        'current_language': session.get('language', 'en'),
        'get_label': get_label
    }

@main.route('/change_language', methods=['POST'])
def change_language():
    lang = request.form.get('language', 'en')
    if lang in ['en', 'ar', 'ru', 'zh', 'es', 'tg', 'fa', 'kk', 'az', 'fr']:
        session['language'] = lang
        
        # If user is logged in, save preference
        if current_user.is_authenticated:
            current_user.language = lang
            db.session.commit()
    
    # Redirect back to the previous page
    return redirect(request.referrer or url_for('main.index'))