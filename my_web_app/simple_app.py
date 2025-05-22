from flask import Flask, render_template, redirect, url_for, flash, request, session, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Create basic Flask app with explicit template folder
app = Flask(__name__, 
            template_folder=os.path.abspath('app/templates'),
            static_folder=os.path.abspath('app/static'))

# Configure app
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'dev-key-replace-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.Integer, default=1)  # 1=bank user, 2=supervisor
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_supervisor(self):
        return self.role >= 2
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# Create database tables
with app.app_context():
    db.create_all()

# Helper function to get user by ID for templates
@app.context_processor
def utility_processor():
    def get_user(user_id):
        return User.query.get(user_id)
    return dict(get_user=get_user)

# Routes
@app.route('/')
def index():
    return render_template('main/index.html', title='Cybersecurity Maturity Assessment')

@app.route('/about')
def about():
    return render_template('main/about.html', title='About')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            
            # Redirect based on role
            if user.is_supervisor:
                return redirect(url_for('supervisor_dashboard'))
            else:
                return redirect(url_for('bank_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    # Use a template in the main directory instead of auth directory
    return render_template('main/login.html', title='Login')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/bank/dashboard')
def bank_dashboard():
    if 'user_id' not in session:
        flash('Please log in first', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        flash('User not found. Please log in again.', 'danger')
        return redirect(url_for('login'))
    
    if user.is_supervisor:
        return redirect(url_for('supervisor_dashboard'))
    
    return render_template('bank/dashboard.html', title='Bank Dashboard', user=user)

@app.route('/supervisor/dashboard')
def supervisor_dashboard():
    if 'user_id' not in session:
        flash('Please log in first', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        flash('User not found. Please log in again.', 'danger')
        return redirect(url_for('login'))
    
    if not user.is_supervisor:
        flash('Access denied. This area is for supervisors only.', 'danger')
        return redirect(url_for('bank_dashboard'))
    
    return render_template('supervisor/dashboard.html', title='Supervisor Dashboard', user=user)

# Create a basic admin user for testing
@app.route('/setup')
def setup():
    try:
        if User.query.count() == 0:
            # Create admin user
            admin = User(username='admin', email='admin@example.com', first_name='Admin', last_name='User', role=2)
            admin.set_password('password')
            
            # Create bank user
            bank_user = User(username='bank', email='bank@example.com', first_name='Bank', last_name='User', role=1)
            bank_user.set_password('password')
            
            db.session.add(admin)
            db.session.add(bank_user)
            db.session.commit()
            
            return 'Users created successfully! <a href="/login">Login here</a>'
        
        return 'Setup already completed. <a href="/login">Login here</a>'
    except Exception as e:
        return f'Error during setup: {str(e)}'

# Helper function to check if templates exist
@app.route('/check-templates')
def check_templates():
    template_paths = [
        'base.html',
        'main/index.html',
        'main/about.html',
        'main/login.html',
        'bank/dashboard.html',
        'supervisor/dashboard.html'
    ]
    
    results = {}
    for path in template_paths:
        try:
            app.jinja_env.get_template(path)
            results[path] = "Found"
        except Exception as e:
            results[path] = f"Not found: {str(e)}"
    
    return str(results)

# Debug helper function to check template paths
@app.route('/debug-templates')
def debug_templates():
    import os
    template_dir = app.template_folder
    result = {
        'template_folder': template_dir,
        'exists': os.path.exists(template_dir),
        'files': {}
    }
    
    # Check direct paths
    paths_to_check = [
        os.path.join(template_dir, 'base.html'),
        os.path.join(template_dir, 'main', 'index.html'),
        os.path.join(template_dir, 'main', 'about.html'),
        os.path.join(template_dir, 'main', 'login.html'),
        os.path.join(template_dir, 'bank', 'dashboard.html'),
        os.path.join(template_dir, 'supervisor', 'dashboard.html')
    ]
    
    for path in paths_to_check:
        result['files'][path] = os.path.exists(path)
    
    # Directory listings
    for root, dirs, files in os.walk(template_dir):
        rel_path = os.path.relpath(root, template_dir)
        if rel_path == '.':
            rel_path = 'ROOT'
        result[f'dir:{rel_path}'] = files
    
    return str(result)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)