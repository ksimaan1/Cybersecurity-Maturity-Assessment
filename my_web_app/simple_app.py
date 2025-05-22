from flask import Flask, render_template, redirect, url_for, session, request, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Import models after db initialization
try:
    from app.models import User, Label
except ImportError:
    # If app.models doesn't exist, define models here
    class User(db.Model):
        __tablename__ = 'user'
        
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(64), index=True, unique=True)
        email = db.Column(db.String(120), index=True, unique=True)
        password_hash = db.Column(db.String(128))
        first_name = db.Column(db.String(64))
        last_name = db.Column(db.String(64))
        role = db.Column(db.String(20))
        language = db.Column(db.String(10), default='en')
        
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

# Language management functions
def get_current_language():
    """Get the current user's language preference"""
    # First check if logged in user has a language preference
    user_id = session.get('user_id')
    if user_id:
        try:
            user = User.query.get(user_id)
            if user and hasattr(user, 'language') and user.language:
                return user.language
        except Exception as e:
            print(f"Error getting user language: {e}")
    
    # Fall back to session language if set
    if 'language' in session:
        return session['language']
    
    # Default to English
    return 'en'

def get_label(key, language=None):
    """Get label in the specified language"""
    if language is None:
        language = get_current_language()
    return Label.get_label(key, language)

# Routes
@app.route('/set_language/<language>')
def set_language(language):
    """Set the user's language preference"""
    valid_languages = ['en', 'ar', 'ru', 'zh', 'es', 'tg', 'fa', 'kk', 'az']
    
    if language not in valid_languages:
        language = 'en'
    
    # Store language preference in session
    session['language'] = language
    
    # If user is logged in, update their preference in the database
    user_id = session.get('user_id')
    if user_id:
        try:
            user = User.query.get(user_id)
            if user:
                user.language = language
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating user language: {e}")
    
    return redirect(request.referrer or url_for('index'))

@app.route('/get_user')
def get_user():
    """Get current logged in user"""
    user_id = session.get('user_id')
    if user_id:
        try:
            user = User.query.get(user_id)
            return user
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            # Set user's language preference in session
            if user.language:
                session['language'] = user.language
            return redirect(url_for('index'))
        else:
            flash(get_label('invalid_credentials'), 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    # Try both template locations
    try:
        return render_template('main/index.html', user=user)
    except:
        return render_template('index.html', user=user)

# Admin routes for label management
@app.route('/admin/labels')
def admin_labels():
    user = get_user()
    if not user or user.role != 'admin':
        flash(get_label('access_denied'), 'error')
        return redirect(url_for('index'))
    
    labels = Label.query.all()
    return render_template('admin/labels.html', labels=labels)

@app.route('/admin/labels/add', methods=['GET', 'POST'])
def admin_add_label():
    user = get_user()
    if not user or user.role != 'admin':
        flash(get_label('access_denied'), 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        key = request.form.get('key')
        
        # Check if label key already exists
        existing = Label.query.filter_by(key=key).first()
        if existing:
            flash(get_label('label_key_exists'), 'error')
            return render_template('admin/edit_label.html')
        
        # Create new label with translations
        label = Label(
            key=key,
            en=request.form.get('en'),
            ar=request.form.get('ar'),
            ru=request.form.get('ru'),
            zh=request.form.get('zh'),
            es=request.form.get('es'),
            tg=request.form.get('tg'),
            fa=request.form.get('fa'),
            kk=request.form.get('kk'),
            az=request.form.get('az')
        )
        
        db.session.add(label)
        db.session.commit()
        flash(get_label('label_added_successfully'), 'success')
        
        return redirect(url_for('admin_labels'))
    
    return render_template('admin/edit_label.html')

@app.route('/admin/labels/edit/<int:id>', methods=['GET', 'POST'])
def admin_edit_label(id):
    user = get_user()
    if not user or user.role != 'admin':
        flash(get_label('access_denied'), 'error')
        return redirect(url_for('index'))
    
    label = Label.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update label translations
        label.key = request.form.get('key')
        label.en = request.form.get('en')
        label.ar = request.form.get('ar')
        label.ru = request.form.get('ru')
        label.zh = request.form.get('zh')
        label.es = request.form.get('es')
        label.tg = request.form.get('tg')
        label.fa = request.form.get('fa')
        label.kk = request.form.get('kk')
        label.az = request.form.get('az')
        
        db.session.commit()
        flash(get_label('label_updated_successfully'), 'success')
        return redirect(url_for('admin_labels'))
    
    return render_template('admin/edit_label.html', label=label)

@app.route('/admin/labels/delete/<int:id>', methods=['POST'])
def admin_delete_label(id):
    user = get_user()
    if not user or user.role != 'admin':
        flash(get_label('access_denied'), 'error')
        return redirect(url_for('index'))
    
    label = Label.query.get_or_404(id)
    db.session.delete(label)
    db.session.commit()
    flash(get_label('label_deleted_successfully'), 'success')
    
    return redirect(url_for('admin_labels'))

# Make helper functions available to templates
@app.context_processor
def inject_utilities():
    return {
        'get_current_language': get_current_language,
        'get_label': get_label,
        'get_user': get_user
    }

# Database initialization
def init_database():
    """Create database tables and populate initial data"""
    with app.app_context():
        db.create_all()
        
        # Add language column to existing users if it doesn't exist
        try:
            inspector = inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('user')]
            if 'language' not in columns:
                db.session.execute(text("ALTER TABLE user ADD COLUMN language VARCHAR(10) DEFAULT 'en'"))
                db.session.commit()
                print("Added language column to user table")
        except Exception as e:
            print(f"Error adding language column: {e}")
        
        # Add initial labels if none exist
        if Label.query.count() == 0:
            initial_labels = [
                {'key': 'app_title', 'en': 'Cybersecurity Maturity Assessment', 'ar': 'تقييم نضج الأمن السيبراني'},
                {'key': 'login', 'en': 'Login', 'ar': 'تسجيل الدخول'},
                {'key': 'username', 'en': 'Username', 'ar': 'اسم المستخدم'},
                {'key': 'password', 'en': 'Password', 'ar': 'كلمة المرور'},
                {'key': 'submit', 'en': 'Submit', 'ar': 'إرسال'},
                {'key': 'cancel', 'en': 'Cancel', 'ar': 'إلغاء'},
                {'key': 'welcome', 'en': 'Welcome', 'ar': 'مرحباً'},
                {'key': 'logout', 'en': 'Logout', 'ar': 'تسجيل الخروج'},
                {'key': 'dashboard', 'en': 'Dashboard', 'ar': 'لوحة التحكم'},
                {'key': 'admin', 'en': 'Admin', 'ar': 'الإدارة'},
                {'key': 'manage_labels', 'en': 'Manage Labels', 'ar': 'إدارة التسميات'},
                {'key': 'add_new_label', 'en': 'Add New Label', 'ar': 'إضافة تسمية جديدة'},
                {'key': 'edit_label', 'en': 'Edit Label', 'ar': 'تعديل التسمية'},
                {'key': 'delete_label', 'en': 'Delete Label', 'ar': 'حذف التسمية'},
                {'key': 'save', 'en': 'Save', 'ar': 'حفظ'},
                {'key': 'back', 'en': 'Back', 'ar': 'رجوع'},
                {'key': 'key', 'en': 'Key', 'ar': 'المفتاح'},
                {'key': 'english', 'en': 'English', 'ar': 'الإنجليزية'},
                {'key': 'arabic', 'en': 'Arabic', 'ar': 'العربية'},
                {'key': 'russian', 'en': 'Russian', 'ar': 'الروسية'},
                {'key': 'chinese', 'en': 'Chinese', 'ar': 'الصينية'},
                {'key': 'spanish', 'en': 'Spanish', 'ar': 'الإسبانية'},
                {'key': 'tajik', 'en': 'Tajik', 'ar': 'التاجيكية'},
                {'key': 'farsi', 'en': 'Farsi', 'ar': 'الفارسية'},
                {'key': 'kazakh', 'en': 'Kazakh', 'ar': 'الكازاخية'},
                {'key': 'azerbaijani', 'en': 'Azerbaijani', 'ar': 'الأذربيجانية'},
                {'key': 'actions', 'en': 'Actions', 'ar': 'الإجراءات'},
                {'key': 'edit', 'en': 'Edit', 'ar': 'تعديل'},
                {'key': 'delete', 'en': 'Delete', 'ar': 'حذف'},
                {'key': 'confirm_delete', 'en': 'Are you sure you want to delete this label?', 'ar': 'هل أنت متأكد من حذف هذه التسمية؟'},
                {'key': 'access_denied', 'en': 'Access denied', 'ar': 'تم رفض الوصول'},
                {'key': 'invalid_credentials', 'en': 'Invalid username or password', 'ar': 'اسم المستخدم أو كلمة المرور غير صحيحة'},
                {'key': 'label_key_exists', 'en': 'Label key already exists', 'ar': 'مفتاح التسمية موجود بالفعل'},
                {'key': 'label_added_successfully', 'en': 'Label added successfully', 'ar': 'تم إضافة التسمية بنجاح'},
                {'key': 'label_updated_successfully', 'en': 'Label updated successfully', 'ar': 'تم تحديث التسمية بنجاح'},
                {'key': 'label_deleted_successfully', 'en': 'Label deleted successfully', 'ar': 'تم حذف التسمية بنجاح'},
            ]
            
            for label_data in initial_labels:
                label = Label(**label_data)
                db.session.add(label)
            
            db.session.commit()
            print("Added initial labels")

if __name__ == '__main__':
    # Initialize database when running the app
    init_database()
    app.run(debug=True)