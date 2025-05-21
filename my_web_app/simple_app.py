from flask import Flask, render_template, redirect, url_for, flash, request, session, g, Response
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
    language = db.Column(db.String(2), default='en')  # Default language preference
    
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

# Language/Label model
class Label(db.Model):
    __tablename__ = 'labels'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    section = db.Column(db.String(50))
    
    # Language columns
    en = db.Column(db.Text)  # English
    ar = db.Column(db.Text)  # Arabic
    ru = db.Column(db.Text)  # Russian
    zh = db.Column(db.Text)  # Chinese
    es = db.Column(db.Text)  # Spanish
    tg = db.Column(db.Text)  # Tajik
    fa = db.Column(db.Text)  # Farsi
    kk = db.Column(db.Text)  # Kazakh
    az = db.Column(db.Text)  # Azerbaijani (Azeri)
    fr = db.Column(db.Text)  # French

# Create database tables
with app.app_context():
    db.create_all()

# Helper function to get user by ID for templates
@app.context_processor
def utility_processor():
    def get_user(user_id):
        return User.query.get(user_id)
    return dict(get_user=get_user)

# Helper function to get labels in the current language
@app.context_processor
def inject_labels():
    def get_label(key, default=None):
        # Get current language from session or use default
        lang = session.get('language', 'en')
        
        # Find the label by key
        label = Label.query.filter_by(key=key).first()
        
        if not label:
            return default or key
        
        # Get the translation for the current language
        translation = getattr(label, lang, None)
        
        # Fall back to English if translation is missing
        if not translation and lang != 'en':
            translation = label.en
        
        # Fall back to key if no translation is available
        return translation or default or key
    
    # Get all supported languages
    languages = [
        {'code': 'en', 'name': 'English'},
        {'code': 'ar', 'name': 'العربية'},  # Arabic
        {'code': 'ru', 'name': 'Русский'},  # Russian
        {'code': 'zh', 'name': '中文'},      # Chinese
        {'code': 'es', 'name': 'Español'},  # Spanish
        {'code': 'tg', 'name': 'Тоҷикӣ'},   # Tajik
        {'code': 'fa', 'name': 'فارسی'},    # Farsi
        {'code': 'kk', 'name': 'Қазақша'},  # Kazakh
        {'code': 'az', 'name': 'Azərbaycan'}, # Azerbaijani
        {'code': 'fr', 'name': 'Français'}  # French
    ]
    
    return {
        'get_label': get_label,
        'languages': languages,
        'current_language': session.get('language', 'en')
    }

# Routes
@app.route('/')
def index():
    # Get the app_title directly from the database instead of using get_label
    app_title_label = Label.query.filter_by(key='app_title').first()
    title = app_title_label.en if app_title_label else 'Cybersecurity Maturity Assessment'
    
    return render_template('main/index.html', title=title)

@app.route('/about')
def about():
    # Get the about title directly from the database
    about_label = Label.query.filter_by(key='about').first()
    title = about_label.en if about_label else 'About'
    
    return render_template('main/about.html', title=title)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            
            # Set user's preferred language
            if user.language:
                session['language'] = user.language
            
            # Get login success message
            login_success_label = Label.query.filter_by(key='login_success').first()
            success_msg = login_success_label.en if login_success_label else 'Login successful!'
            
            flash(success_msg, 'success')
            
            # Redirect based on role
            if user.is_supervisor:
                return redirect(url_for('supervisor_dashboard'))
            else:
                return redirect(url_for('bank_dashboard'))
        else:
            # Get login failed message
            login_failed_label = Label.query.filter_by(key='login_failed').first()
            failed_msg = login_failed_label.en if login_failed_label else 'Invalid username or password'
            
            flash(failed_msg, 'danger')
    
    # Get login title
    login_label = Label.query.filter_by(key='login').first()
    title = login_label.en if login_label else 'Login'
    
    # Use a template in the main directory instead of auth directory
    return render_template('main/login.html', title=title)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    
    # Get logout success message
    logout_success_label = Label.query.filter_by(key='logout_success').first()
    logout_msg = logout_success_label.en if logout_success_label else 'You have been logged out'
    
    flash(logout_msg, 'info')
    return redirect(url_for('index'))

@app.route('/change-language/<language_code>')
def change_language(language_code):
    # Validate language code
    valid_languages = ['en', 'ar', 'ru', 'zh', 'es', 'tg', 'fa', 'kk', 'az', 'fr']
    
    if language_code in valid_languages:
        session['language'] = language_code
        
        # If user is logged in, save preference to profile
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                user.language = language_code
                db.session.commit()
    
    # Redirect back to the referring page
    return redirect(request.referrer or url_for('index'))

@app.route('/bank/dashboard')
def bank_dashboard():
    if 'user_id' not in session:
        # Get login required message
        login_required_label = Label.query.filter_by(key='login_required').first()
        login_msg = login_required_label.en if login_required_label else 'Please log in first'
        
        flash(login_msg, 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        
        # Get user not found message
        user_not_found_label = Label.query.filter_by(key='user_not_found').first()
        user_msg = user_not_found_label.en if user_not_found_label else 'User not found. Please log in again.'
        
        flash(user_msg, 'danger')
        return redirect(url_for('login'))
    
    if user.is_supervisor:
        return redirect(url_for('supervisor_dashboard'))
    
    # Get bank dashboard title
    bank_dashboard_label = Label.query.filter_by(key='bank_dashboard').first()
    title = bank_dashboard_label.en if bank_dashboard_label else 'Bank Dashboard'
    
    return render_template('bank/dashboard.html', title=title, user=user)

@app.route('/supervisor/dashboard')
def supervisor_dashboard():
    if 'user_id' not in session:
        # Get login required message
        login_required_label = Label.query.filter_by(key='login_required').first()
        login_msg = login_required_label.en if login_required_label else 'Please log in first'
        
        flash(login_msg, 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        
        # Get user not found message
        user_not_found_label = Label.query.filter_by(key='user_not_found').first()
        user_msg = user_not_found_label.en if user_not_found_label else 'User not found. Please log in again.'
        
        flash(user_msg, 'danger')
        return redirect(url_for('login'))
    
    if not user.is_supervisor:
        # Get access denied message
        access_denied_label = Label.query.filter_by(key='access_denied').first()
        access_msg = access_denied_label.en if access_denied_label else 'Access denied. This area is for supervisors only.'
        
        flash(access_msg, 'danger')
        return redirect(url_for('bank_dashboard'))
    
    # Get supervisor dashboard title
    supervisor_dashboard_label = Label.query.filter_by(key='supervisor_dashboard').first()
    title = supervisor_dashboard_label.en if supervisor_dashboard_label else 'Supervisor Dashboard'
    
    return render_template('supervisor/dashboard.html', title=title, user=user)

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

# Setup labels route
@app.route('/setup-labels')
def setup_labels():
    try:
        # Clear existing labels to avoid duplicates
        Label.query.delete()
        db.session.commit()
        
        # Helper function to create labels
        def create_label(key, section, en, es=""):
            return Label(
                key=key,
                section=section,
                en=en,
                es=es if es else f"[ES] {en}",  # Spanish (use provided or placeholder)
                ar=f"[AR] {en}",  # Arabic placeholder
                ru=f"[RU] {en}",  # Russian placeholder
                tg=f"[TG] {en}",  # Tajik placeholder
                zh=f"[ZH] {en}",  # Chinese placeholder
                fa=f"[FA] {en}",  # Farsi placeholder
                kk=f"[KK] {en}",  # Kazakh placeholder
                az=f"[AZ] {en}",  # Azerbaijani placeholder
                fr=f"[FR] {en}"   # French placeholder
            )
        
        # Create comprehensive label set
        labels = [
            # Common/General UI labels
            create_label('app_title', 'common', 'Cybersecurity Maturity Assessment', 'Evaluación de Madurez en Ciberseguridad'),
            create_label('home', 'common', 'Home', 'Inicio'),
            create_label('about', 'common', 'About', 'Acerca de'),
            create_label('login', 'common', 'Login', 'Iniciar sesión'),
            create_label('logout', 'common', 'Logout', 'Cerrar sesión'),
            create_label('account', 'common', 'Account', 'Cuenta'),
            create_label('profile', 'common', 'Profile', 'Perfil'),
            create_label('language', 'common', 'Language', 'Idioma'),
            create_label('welcome_user', 'common', 'Welcome', 'Bienvenido'),
            create_label('dashboard', 'common', 'Dashboard', 'Panel de control'),
            create_label('submit', 'common', 'Submit', 'Enviar'),
            create_label('cancel', 'common', 'Cancel', 'Cancelar'),
            create_label('save', 'common', 'Save', 'Guardar'),
            create_label('edit', 'common', 'Edit', 'Editar'),
            create_label('delete', 'common', 'Delete', 'Eliminar'),
            create_label('back', 'common', 'Back', 'Atrás'),
            create_label('next', 'common', 'Next', 'Siguiente'),
            create_label('yes', 'common', 'Yes', 'Sí'),
            create_label('no', 'common', 'No', 'No'),
            create_label('required', 'common', 'Required', 'Requerido'),
            create_label('optional', 'common', 'Optional', 'Opcional'),
            create_label('actions', 'common', 'Actions', 'Acciones'),
            create_label('view', 'common', 'View', 'Ver'),
            create_label('add', 'common', 'Add', 'Añadir'),
            create_label('search', 'common', 'Search', 'Buscar'),
            create_label('filter', 'common', 'Filter', 'Filtrar'),
            create_label('please_wait', 'common', 'Please wait...', 'Por favor espere...'),
            create_label('loading', 'common', 'Loading', 'Cargando'),
            create_label('success', 'common', 'Success', 'Éxito'),
            create_label('error', 'common', 'Error', 'Error'),
            create_label('warning', 'common', 'Warning', 'Advertencia'),
            create_label('info', 'common', 'Information', 'Información'),
            create_label('copyright', 'common', '©2025 Cybersecurity Maturity Assessment', '©2025 Evaluación de Madurez en Ciberseguridad'),
            
            # Auth/Login related messages
            create_label('username', 'auth', 'Username', 'Nombre de usuario'),
            create_label('password', 'auth', 'Password', 'Contraseña'),
            create_label('remember_me', 'auth', 'Remember me', 'Recordarme'),
            create_label('login_success', 'auth', 'Login successful!', '¡Inicio de sesión exitoso!'),
            create_label('login_failed', 'auth', 'Invalid username or password', 'Usuario o contraseña inválidos'),
            create_label('logout_success', 'auth', 'You have been logged out', 'Ha cerrado sesión'),
            create_label('login_required', 'auth', 'Please log in first', 'Por favor inicie sesión primero'),
            create_label('user_not_found', 'auth', 'User not found. Please log in again.', 'Usuario no encontrado. Por favor inicie sesión nuevamente.'),
            create_label('access_denied', 'auth', 'Access denied. This area is for supervisors only.', 'Acceso denegado. Esta área es solo para supervisores.'),
            
            # Homepage
            create_label('welcome_msg', 'homepage', 'Welcome to the Cybersecurity Controls Framework application.', 'Bienvenido a la aplicación del Marco de Controles de Ciberseguridad.'),
            create_label('app_description', 'homepage', 'This platform helps financial institutions evaluate and monitor cybersecurity maturity using a structured, control-based framework.', 'Esta plataforma ayuda a las instituciones financieras a evaluar y monitorear la madurez en ciberseguridad utilizando un marco estructurado basado en controles.'),
            create_label('learn_more', 'homepage', 'Learn more', 'Más información'),
            
            # About page
            create_label('about_app', 'about', 'About the Application', 'Acerca de la Aplicación'),
            create_label('about_desc', 'about', 'This application is designed for central bank supervisors and authorized personnel from private financial institutions to evaluate and monitor cybersecurity maturity across institutions using a structured, control-based framework.', 'Esta aplicación está diseñada para supervisores de bancos centrales y personal autorizado de instituciones financieras privadas para evaluar y monitorear la madurez en ciberseguridad en todas las instituciones utilizando un marco estructurado basado en controles.'),
            create_label('key_features', 'about', 'Key Features', 'Características Principales'),
            create_label('feature_1', 'about', 'Customizable library of cybersecurity controls', 'Biblioteca personalizable de controles de ciberseguridad'),
            create_label('feature_2', 'about', 'Group-based control visibility for different institution sizes', 'Visibilidad de controles basada en grupos para diferentes tamaños de instituciones'),
            create_label('feature_3', 'about', 'Self-assessment capabilities for bank users', 'Capacidades de autoevaluación para usuarios bancarios'),
            create_label('feature_4', 'about', 'Supervisor evaluation and observation periods', 'Períodos de evaluación y observación del supervisor'),
            create_label('feature_5', 'about', 'Multilingual support across 10 languages', 'Soporte multilingüe en 10 idiomas'),
            create_label('feature_6', 'about', 'Comprehensive reporting tools', 'Herramientas de informes completas'),
            
            # Supervisor dashboard
            create_label('supervisor_dashboard', 'supervisor', 'Supervisor Dashboard', 'Panel de Supervisor'),
            create_label('supervisor_dashboard_desc', 'supervisor', 'This is your supervisor dashboard for cybersecurity maturity assessment.', 'Este es su panel de supervisor para la evaluación de madurez en ciberseguridad.'),
            create_label('institutions', 'supervisor', 'Institutions', 'Instituciones'),
            create_label('manage_institutions', 'supervisor', 'Manage financial institutions.', 'Gestionar instituciones financieras.'),
            create_label('view_institutions', 'supervisor', 'View Institutions', 'Ver Instituciones'),
            create_label('controls', 'supervisor', 'Controls', 'Controles'),
            create_label('manage_controls', 'supervisor', 'Manage control framework.', 'Gestionar marco de controles.'),
            create_label('view_controls', 'supervisor', 'View Controls', 'Ver Controles'),
            create_label('observations', 'supervisor', 'Observations', 'Observaciones'),
            create_label('manage_observations', 'supervisor', 'Manage observation periods.', 'Gestionar períodos de observación.'),
            create_label('view_observations', 'supervisor', 'View Observations', 'Ver Observaciones'),
            create_label('reports', 'supervisor', 'Reports', 'Informes'),
            create_label('generate_reports', 'supervisor', 'Generate assessment reports.', 'Generar informes de evaluación.'),
            create_label('view_reports', 'supervisor', 'View Reports', 'Ver Informes'),
            
            # Bank dashboard
            create_label('bank_dashboard', 'bank', 'Bank Dashboard', 'Panel de Banco'),
            create_label('bank_dashboard_desc', 'bank', 'This is your cybersecurity maturity assessment dashboard.', 'Este es su panel de evaluación de madurez en ciberseguridad.'),
            create_label('view_assess_controls', 'bank', 'View and assess cybersecurity controls.', 'Ver y evaluar controles de ciberseguridad.'),
            create_label('improvement_plans', 'bank', 'Improvement Plans', 'Planes de Mejora'),
            create_label('manage_plans', 'bank', 'Track your improvement activities.', 'Seguimiento de actividades de mejora.'),
            create_label('view_plans', 'bank', 'View Plans', 'Ver Planes'),
            create_label('supervisor_evaluations', 'bank', 'Supervisor evaluations and feedback.', 'Evaluaciones y retroalimentación del supervisor.'),
            
            # Controls management
            create_label('control_id', 'controls', 'Control ID', 'ID de Control'),
            create_label('control_name', 'controls', 'Control Name', 'Nombre del Control'),
            create_label('control_description', 'controls', 'Description', 'Descripción'),
            create_label('control_objective', 'controls', 'Objective', 'Objetivo'),
            create_label('control_group', 'controls', 'Control Group', 'Grupo de Control'),
            create_label('control_type', 'controls', 'Control Type', 'Tipo de Control'),
            create_label('applicability_group', 'controls', 'Applicability Group', 'Grupo de Aplicabilidad'),
            create_label('control_status', 'controls', 'Status', 'Estado'),
            create_label('control_version', 'controls', 'Version', 'Versión'),
            create_label('add_control', 'controls', 'Add Control', 'Añadir Control'),
            create_label('edit_control', 'controls', 'Edit Control', 'Editar Control'),
            create_label('delete_control', 'controls', 'Delete Control', 'Eliminar Control'),
            
            # Assessment related
            create_label('maturity_level', 'assessment', 'Maturity Level', 'Nivel de Madurez'),
            create_label('assessment_comment', 'assessment', 'Comment', 'Comentario'),
            create_label('save_assessment', 'assessment', 'Save Assessment', 'Guardar Evaluación'),
            create_label('assessment_date', 'assessment', 'Assessment Date', 'Fecha de Evaluación'),
            create_label('last_updated', 'assessment', 'Last Updated', 'Última Actualización'),
            create_label('assessed_by', 'assessment', 'Assessed By', 'Evaluado Por'),
            create_label('level_1', 'assessment', 'Level 1', 'Nivel 1'),
            create_label('level_2', 'assessment', 'Level 2', 'Nivel 2'),
            create_label('level_3', 'assessment', 'Level 3', 'Nivel 3'),
            create_label('level_4', 'assessment', 'Level 4', 'Nivel 4'),
            
            # Improvement plan
            create_label('improvement_activity', 'improvement', 'Activity', 'Actividad'),
            create_label('target_date', 'improvement', 'Target Date', 'Fecha Objetivo'),
            create_label('completion_percentage', 'improvement', 'Completion %', '% de Finalización'),
            create_label('plan_status', 'improvement', 'Status', 'Estado'),
            create_label('add_plan', 'improvement', 'Add Plan', 'Añadir Plan'),
            create_label('update_plan', 'improvement', 'Update Plan', 'Actualizar Plan'),
            create_label('status_planned', 'improvement', 'Planned', 'Planificado'),
            create_label('status_in_progress', 'improvement', 'In Progress', 'En Progreso'),
            create_label('status_completed', 'improvement', 'Completed', 'Completado'),
            create_label('status_canceled', 'improvement', 'Canceled', 'Cancelado'),
            
            # Observation period
            create_label('observation_period', 'observation', 'Observation Period', 'Período de Observación'),
            create_label('start_date', 'observation', 'Start Date', 'Fecha de Inicio'),
            create_label('end_date', 'observation', 'End Date', 'Fecha de Fin'),
            create_label('observation_title', 'observation', 'Title', 'Título'),
            create_label('observation_description', 'observation', 'Description', 'Descripción'),
            create_label('observation_status', 'observation', 'Status', 'Estado'),
            create_label('visibility_to_institution', 'observation', 'Visible to Institution', 'Visible para la Institución'),
            create_label('required_action', 'observation', 'Required Action', 'Acción Requerida'),
            create_label('created_by', 'observation', 'Created By', 'Creado Por'),
            create_label('creation_date', 'observation', 'Creation Date', 'Fecha de Creación'),
            
            # Institution management
            create_label('institution_name', 'institution', 'Institution Name', 'Nombre de la Institución'),
            create_label('short_name', 'institution', 'Short Name', 'Nombre Corto'),
            create_label('institution_type', 'institution', 'Institution Type', 'Tipo de Institución'),
            create_label('group_level', 'institution', 'Group Level', 'Nivel de Grupo'),
            create_label('active', 'institution', 'Active', 'Activo'),
            create_label('address', 'institution', 'Address', 'Dirección'),
            create_label('country', 'institution', 'Country', 'País'),
            create_label('add_institution', 'institution', 'Add Institution', 'Añadir Institución'),
            create_label('edit_institution', 'institution', 'Edit Institution', 'Editar Institución'),
            create_label('delete_institution', 'institution', 'Delete Institution', 'Eliminar Institución'),
            
            # Reports
            create_label('report_title', 'reports', 'Report Title', 'Título del Informe'),
            create_label('report_date', 'reports', 'Report Date', 'Fecha del Informe'),
            create_label('report_type', 'reports', 'Report Type', 'Tipo de Informe'),
            create_label('generate_report', 'reports', 'Generate Report', 'Generar Informe'),
            create_label('download_report', 'reports', 'Download Report', 'Descargar Informe'),
            create_label('print_report', 'reports', 'Print Report', 'Imprimir Informe'),
            create_label('report_period', 'reports', 'Report Period', 'Período del Informe'),
            create_label('from_date', 'reports', 'From Date', 'Desde Fecha'),
            create_label('to_date', 'reports', 'To Date', 'Hasta Fecha'),
            
            # User profile
            create_label('personal_info', 'profile', 'Personal Information', 'Información Personal'),
            create_label('first_name', 'profile', 'First Name', 'Nombre'),
            create_label('last_name', 'profile', 'Last Name', 'Apellido'),
            create_label('email', 'profile', 'Email', 'Correo Electrónico'),
            create_label('department', 'profile', 'Department', 'Departamento'),
            create_label('institution', 'profile', 'Institution', 'Institución'),
            create_label('role', 'profile', 'Role', 'Rol'),
            create_label('preferred_language', 'profile', 'Preferred Language', 'Idioma Preferido'),
            create_label('change_password', 'profile', 'Change Password', 'Cambiar Contraseña'),
            create_label('current_password', 'profile', 'Current Password', 'Contraseña Actual'),
            create_label('new_password', 'profile', 'New Password', 'Nueva Contraseña'),
            create_label('confirm_password', 'profile', 'Confirm Password', 'Confirmar Contraseña'),
            create_label('save_changes', 'profile', 'Save Changes', 'Guardar Cambios'),
            
            # Error messages
            create_label('error_404', 'errors', 'Page Not Found', 'Página No Encontrada'),
            create_label('error_500', 'errors', 'Server Error', 'Error del Servidor'),
            create_label('error_403', 'errors', 'Access Forbidden', 'Acceso Prohibido'),
            create_label('error_generic', 'errors', 'An error occurred', 'Ha ocurrido un error'),
            create_label('return_home', 'errors', 'Return to Home', 'Volver al Inicio'),
            
            # Label Management
            create_label('label_management', 'admin', 'Label Management', 'Gestión de Etiquetas'),
            create_label('label_key', 'admin', 'Label Key', 'Clave de Etiqueta'),
            create_label('label_section', 'admin', 'Section', 'Sección'),
            create_label('label_en', 'admin', 'English', 'Inglés'),
            create_label('label_es', 'admin', 'Spanish', 'Español'),
            create_label('label_ar', 'admin', 'Arabic', 'Árabe'),
            create_label('label_ru', 'admin', 'Russian', 'Ruso'),
            create_label('label_zh', 'admin', 'Chinese', 'Chino'),
            create_label('label_tg', 'admin', 'Tajik', 'Tayiko'),
            create_label('label_fa', 'admin', 'Farsi', 'Farsi'),
            create_label('label_kk', 'admin', 'Kazakh', 'Kazajo'),
            create_label('label_az', 'admin', 'Azerbaijani', 'Azerbaiyano'),
            create_label('label_fr', 'admin', 'French', 'Francés'),
            create_label('edit_translations', 'admin', 'Edit Translations', 'Editar Traducciones'),
            create_label('add_new_label', 'admin', 'Add New Label', 'Añadir Nueva Etiqueta'),
            create_label('import_labels', 'admin', 'Import Labels', 'Importar Etiquetas'),
            create_label('export_labels', 'admin', 'Export Labels', 'Exportar Etiquetas'),
            create_label('confirm_delete', 'admin', 'Confirm Delete', 'Confirmar Eliminación'),
            create_label('delete_confirm_text', 'admin', 'Are you sure you want to delete this label?', '¿Está seguro de que desea eliminar esta etiqueta?'),
            create_label('filter_labels', 'admin', 'Filter Labels', 'Filtrar Etiquetas'),
            create_label('search_key_text', 'admin', 'Search Key or Text', 'Buscar Clave o Texto'),
            create_label('all_sections', 'admin', 'All Sections', 'Todas las Secciones'),
        ]
        
        # Add a few labels with complete translations for all languages
        enhanced_labels = [
            Label(
                key='language_selector', 
                section='common', 
                en='Select Language', 
                es='Seleccionar Idioma',
                ar='اختر اللغة',
                ru='Выбрать язык',
                tg='Забони интихоб кунед',
                zh='选择语言',
                fa='انتخاب زبان',
                kk='Тілді таңдаңыз',
                az='Dil seçin',
                fr='Choisir la langue'
            ),
            Label(
                key='dashboard_welcome', 
                section='common', 
                en='Welcome to your dashboard', 
                es='Bienvenido a su panel',
                ar='مرحبًا بك في لوحة التحكم الخاصة بك',
                ru='Добро пожаловать в вашу панель',
                tg='Хуш омадед ба лавҳаи шумо',
                zh='欢迎来到您的仪表板',
                fa='به داشبورد خود خوش آمدید',
                kk='Тақтаңызға қош келдіңіз',
                az='İdarəetmə panelinizə xoş gəldiniz',
                fr='Bienvenue sur votre tableau de bord'
            )
        ]
        
        # Add all labels to the database
        db.session.add_all(labels)
        db.session.add_all(enhanced_labels)
        db.session.commit()
        
        return 'Labels created successfully! <a href="/">Go to homepage</a>'
    except Exception as e:
        return f'Error setting up labels: {str(e)}'

# Label Management Routes
@app.route('/admin/labels')
def admin_labels():
    # Get query parameters for filtering
    selected_section = request.args.get('section', '')
    search_term = request.args.get('search', '')
    
    # Start with all labels
    query = Label.query
    
    # Apply filters
    if selected_section:
        query = query.filter_by(section=selected_section)
    
    if search_term:
        search = f"%{search_term}%"
        query = query.filter(
            db.or_(
                Label.key.like(search),
                Label.en.like(search),
                Label.es.like(search)
            )
        )
    
    # Get all unique sections for the dropdown
    sections = db.session.query(Label.section).distinct().order_by(Label.section).all()
    sections = [section[0] for section in sections if section[0]]
    
    # Execute query with filters and order
    labels = query.order_by(Label.section, Label.key).all()
    
    return render_template(
        'admin/labels.html', 
        labels=labels, 
        sections=sections,
        selected_section=selected_section,
        search_term=search_term
    )

@app.route('/admin/labels/edit/<int:label_id>', methods=['GET', 'POST'])
def edit_label(label_id):
    if label_id:
        label = Label.query.get_or_404(label_id)
    else:
        # New label
        label = Label()
    
    if request.method == 'POST':
        # Update label fields
        if not label_id:  # Only update key for new labels
            label.key = request.form.get('key')
        
        label.section = request.form.get('section')
        label.en = request.form.get('en')
        label.es = request.form.get('es')
        label.ar = request.form.get('ar')
        label.ru = request.form.get('ru')
        label.zh = request.form.get('zh')
        label.tg = request.form.get('tg')
        label.fa = request.form.get('fa')
        label.kk = request.form.get('kk')
        label.az = request.form.get('az')
        label.fr = request.form.get('fr')
        
        # Save changes
        if not label_id:
            db.session.add(label)
        
        db.session.commit()
        
        flash('Label saved successfully!', 'success')
        return redirect(url_for('admin_labels'))
    
    return render_template('admin/edit_label.html', label=label)

@app.route('/admin/labels/add', methods=['GET', 'POST'])
def add_label():
    # Create empty label for the form
    label = Label(key='', section='', en='', es='', ar='', ru='', zh='', tg='', fa='', kk='', az='', fr='')
    
    if request.method == 'POST':
        # Check if key already exists
        existing_label = Label.query.filter_by(key=request.form.get('key')).first()
        if existing_label:
            flash(f"A label with key '{request.form.get('key')}' already exists!", 'danger')
            return render_template('admin/edit_label.html', label=label)
        
        # Create new label
        label = Label(
            key=request.form.get('key'),
            section=request.form.get('section'),
            en=request.form.get('en'),
            es=request.form.get('es'),
            ar=request.form.get('ar'),
            ru=request.form.get('ru'),
            zh=request.form.get('zh'),
            tg=request.form.get('tg'),
            fa=request.form.get('fa'),
            kk=request.form.get('kk'),
            az=request.form.get('az'),
            fr=request.form.get('fr')
        )
        
        db.session.add(label)
        db.session.commit()
        
        flash('Label added successfully!', 'success')
        return redirect(url_for('admin_labels'))
    
    return render_template('admin/edit_label.html', label=label)

@app.route('/admin/labels/delete/<int:label_id>')
def delete_label(label_id):
    label = Label.query.get_or_404(label_id)
    
    db.session.delete(label)
    db.session.commit()
    
    flash(f"Label '{label.key}' deleted successfully!", 'success')
    return redirect(url_for('admin_labels'))

@app.route('/admin/labels/export')
def export_labels():
    from io import StringIO
    import csv
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['key', 'section', 'en', 'es', 'ar', 'ru', 'zh', 'tg', 'fa', 'kk', 'az', 'fr'])
    
    # Write data
    labels = Label.query.order_by(Label.section, Label.key).all()
    for label in labels:
        writer.writerow([
            label.key, 
            label.section, 
            label.en, 
            label.es,
            label.ar,
            label.ru,
            label.zh,
            label.tg,
            label.fa,
            label.kk,
            label.az,
            label.fr
        ])
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=labels.csv"}
    )

@app.route('/admin/labels/import', methods=['GET', 'POST'])
def import_labels():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file:
            import csv
            from io import StringIO
            
            # Read CSV file
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.reader(stream)
            
            # Skip header row
            next(csv_input)
            
            # Process data
            update_existing = request.form.get('update_existing', '') == '1'
            updated = 0
            created = 0
            skipped = 0
            
            for row in csv_input:
                if len(row) < 12:  # Make sure row has enough columns
                    continue
                
                key, section, en, es, ar, ru, zh, tg, fa, kk, az, fr = row
                
                # Look for existing label
                label = Label.query.filter_by(key=key).first()
                
                if label and update_existing:
                    # Update existing label
                    label.section = section
                    label.en = en
                    label.es = es
                    label.ar = ar
                    label.ru = ru
                    label.zh = zh
                    label.tg = tg
                    label.fa = fa
                    label.kk = kk
                    label.az = az
                    label.fr = fr
                    updated += 1
                elif not label:
                    # Create new label
                    label = Label(
                        key=key,
                        section=section,
                        en=en,
                        es=es,
                        ar=ar,
                        ru=ru,
                        zh=zh,
                        tg=tg,
                        fa=fa,
                        kk=kk,
                        az=az,
                        fr=fr
                    )
                    db.session.add(label)
                    created += 1
                else:
                    # Skip existing labels if not updating
                    skipped += 1
            
            db.session.commit()
            flash(f'Import completed: {updated} labels updated, {created} labels created, {skipped} labels skipped', 'success')
            return redirect(url_for('admin_labels'))
    
    return render_template('admin/import_labels.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)