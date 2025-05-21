from app import create_app, db
from flask_migrate import Migrate, init, migrate, upgrade

app = create_app('development')
migrate = Migrate(app, db)

with app.app_context():
    # Initialize migrations
    init()
    
    # Create initial migration
    migrate(message="Initial migration")
    
    # Apply migration
    upgrade()
    
    print("Database setup complete!")