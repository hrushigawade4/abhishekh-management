from app import app
from models import Bhakt, SacredDate

with app.app_context():
    bhakts = Bhakt.query.all()
    sacred_dates = SacredDate.query.all()

    print("Bhakts:")
    for b in bhakts:
        print(b.registration_number, b.name, b.abhishek_types)

    print("\nSacred Dates:")
    for sd in sacred_dates:
        print(sd.abhishek_type, sd.date)
