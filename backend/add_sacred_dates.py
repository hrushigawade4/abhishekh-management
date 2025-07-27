from datetime import date
from models import db, SacredDate
from app import app

with app.app_context():
    dates_to_add = [
        SacredDate(date=date(2025, 8, 1), abhishek_type='Pournima'),
        SacredDate(date=date(2025, 8, 7), abhishek_type='Guruvar'),
        SacredDate(date=date(2025, 8, 10), abhishek_type='Pradosh'),
    ]
    db.session.bulk_save_objects(dates_to_add)
    db.session.commit()
    print("✅ Sacred dates added.")
