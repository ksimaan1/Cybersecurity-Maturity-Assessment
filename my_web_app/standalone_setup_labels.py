# standalone_setup_labels.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Create Flask app and configure it
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define Label model
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

def setup_labels():
    with app.app_context():
        # Create tables
        db.create_all()
        
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
            ]
            
            # Add a few fully translated labels (with different keys to avoid conflicts)
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
            
            print('Labels created successfully!')
        except Exception as e:
            print(f'Error setting up labels: {str(e)}')

if __name__ == '__main__':
    setup_labels()