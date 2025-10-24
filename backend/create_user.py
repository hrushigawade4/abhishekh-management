from app import app, db
from models import User

def create_initial_user():
    with app.app_context():
        db.create_all()
        
        # Check if user already exists
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            print("Initial user created!")
        else:
            print("Admin user already exists!")

if __name__ == '__main__':
    create_initial_user()