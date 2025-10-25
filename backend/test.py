from app import app
from models import db, Bhakt

if __name__ == '__main__':
    with app.app_context():
        # create tables if they don't exist
        db.create_all()
        bhakts = Bhakt.query.all()
        print('Bhakts count:', len(bhakts))
        for b in bhakts:
            print(b.id, b.registration_number, b.name)

