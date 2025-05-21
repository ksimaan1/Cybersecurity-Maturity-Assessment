import os
from app import create_app, db
from flask_migrate import Migrate

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    from app.models.user import User
    from app.models.institution import Institution
    from app.models.control import Control, ControlGroup
    from app.models.assessment import Assessment, MaturityRating
    from app.models.observation import ObservationPeriod, ObservationRating
    from app.models.language import Label
    
    return {
        'db': db, 
        'User': User, 
        'Institution': Institution,
        'Control': Control,
        'ControlGroup': ControlGroup,
        'Assessment': Assessment,
        'MaturityRating': MaturityRating,
        'ObservationPeriod': ObservationPeriod,
        'ObservationRating': ObservationRating,
        'Label': Label
    }

if __name__ == '__main__':
    app.run(debug=True)