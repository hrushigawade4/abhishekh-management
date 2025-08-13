from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import calendar

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
        # Calculate expiration when creating the object
        self.calculate_expiration()

    def calculate_expiration(self):
        """Calculate expiration date based on start_date and validity_months"""
        if not self.start_date or not self.validity_months:
            return
        
        # Start from the current start_date
        current_date = self.start_date
        target_year = current_date.year
        target_month = current_date.month
        
        # Add the validity months
        target_month += self.validity_months
        
        # Handle year overflow
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        # Handle day overflow (e.g., Jan 31 + 1 month should be Feb 28/29)
        max_day_in_target_month = calendar.monthrange(target_year, target_month)[1]
        target_day = min(current_date.day, max_day_in_target_month)
        
        self.expiration_date = datetime(target_year, target_month, target_day).date()

class SacredDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    abhishek_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('abhishek_type', 'date', name='uix_type_date'),
    )

    def __repr__(self):
        return f"<SacredDate {self.abhishek_type} - {self.date}>"