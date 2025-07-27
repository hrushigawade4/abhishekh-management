from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class Bhakt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False)
    gotra = db.Column(db.String(100))
    email_address = db.Column(db.String(100))
    abhishek_types = db.Column(db.String(255)) # Store as comma-separated string: "Pournima,Guruvar"
    start_date = db.Column(db.Date, default=datetime.utcnow().date())
    validity_months = db.Column(db.Integer, default=12)
    expiration_date = db.Column(db.Date) # Calculated automatically

    def __init__(self, name, mobile_number, address, gotra=None, email_address=None,
                 abhishek_types=None, start_date=None, validity_months=12):
        self.name = name
        self.mobile_number = mobile_number
        self.address = address
        self.gotra = gotra
        self.email_address = email_address
        self.abhishek_types = abhishek_types if abhishek_types else ""
        self.start_date = start_date if start_date else datetime.utcnow().date()
        self.validity_months = validity_months
        self.expiration_date = self.start_date + timedelta(days=validity_months * 30) # Approximate

    def calculate_expiration(self):
        # More accurate expiration calculation considering month end
        import calendar
        year = self.start_date.year + (self.start_date.month + self.validity_months - 1) // 12
        month = (self.start_date.month + self.validity_months - 1) % 12 + 1
        day = min(self.start_date.day, calendar.monthrange(year, month)[1])
        self.expiration_date = datetime(year, month, day).date()


class SacredDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    abhishek_type = db.Column(db.String(50), nullable=False) # e.g., Pournima, Guruvar, Pradosh, Custom
    date = db.Column(db.Date, nullable=False, unique=True) # Ensure no duplicate dates for same type

    def __repr__(self):
        return f"<SacredDate {self.abhishek_type} - {self.date}>"