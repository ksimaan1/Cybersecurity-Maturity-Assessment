from flask import render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.auth import auth
from app.models.user import User, Role
from app.models.language import Label
from datetime import datetime
from urllib.parse import urlparse
from flask_jwt_extended import create_access_token
from . import forms

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect to appropriate dashboard based on role
        if current_user.is_supervisor:
            return redirect(url_for('supervisor.index'))
        else:
            return redirect(url_for('bank.index'))
    
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        
        # Check if user is active
        if not user.is_active_employee:
            flash('This account is no longer active')
            return redirect(url_for('auth.login'))
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        
        # Set user language preference
        if user.language:
            session['language'] = user.language
        
        # Redirect to the requested page or default dashboard
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.is_supervisor:
                next_page = url_for('supervisor.index')
            else:
                next_page = url_for('bank.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/change_language/<language_code>')
def change_language(language_code):
    # Store the language preference in session
    session['language'] = language_code
    
    # If user is logged in, save preference to user profile
    if current_user.is_authenticated:
        current_user.language = language_code
        db.session.commit()
    
    # Redirect back to the referring page or home
    return redirect(request.referrer or url_for('main.index'))

# API Authentication routes
@auth.route('/api/login', methods=['POST'])
def api_login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    
    user = User.query.filter_by(username=username).first()
    if user is None or not user.verify_password(password):
        return jsonify({"msg": "Bad username or password"}), 401
    
    # Check if user is active
    if not user.is_active_employee:
        return jsonify({"msg": "Account is inactive"}), 401
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create the tokens
    access_token = create_access_token(
        identity={
            'user_id': user.id,
            'role': user.role,
            'institution_id': user.institution_id
        }
    )
    
    return jsonify(access_token=access_token), 200