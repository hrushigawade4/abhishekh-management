from app import app, db
from models import Bhakt

def migrate_data():
    with app.app_context():
        # Get your existing data (if you have it backed up)
        # Add it back with registration numbers
        bhakts_data = [
            # Your backed up data here
            # Example:
            # {'name': 'John', 'mobile_number': '1234567890', ...}
        ]
        
        for i, data in enumerate(bhakts_data, 1):
            bhakt = Bhakt(
                registration_number=str(i).zfill(2),
                **data
            )
            db.session.add(bhakt)
        
        db.session.commit()

if __name__ == '__main__':
    migrate_data()