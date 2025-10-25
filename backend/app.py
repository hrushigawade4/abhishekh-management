from flask import Flask, request, jsonify, render_template, redirect,  url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta,timezone
import os
from models import db, Bhakt, SacredDate, Subscriber # Import models from models.py
import csv
from io import StringIO
from flask import make_response
import sqlite3
from datetime import date
import webbrowser
from threading import Timer
from waitress import serve
import sys
import smtplib
import webbrowser
from email.message import EmailMessage
import calendar
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file, flash
from models import User  # Import User model
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from models import User,db, Bhakt, SacredDate, Subscriber
from flask_migrate import Migrate



ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
# from models import SacredDate
# ...existing code...
FIXED_ABHISHEKH_TYPES = ["Guruvar", "Pournima", "Pradosh", "Nityaseva", "Annadan"]
# ...existing code...

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Admini123'  # Change this to a secure secret key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'abhishek_management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db.init_app(app)
migrate = Migrate(app, db)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # try to find existing user
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))

        # Optionally create initial admin if using known initial password
        if username == 'admin' and password == os.environ.get('INITIAL_ADMIN_PASSWORD', 'Admini123'):
            user = User(username=username)
            user.set_password(password)   # <-- set hashed password
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))

        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- FIX FOR before_first_request ---
# Replace @app.before_first_request with @app.before_request
# db.create_all() is idempotent, so running it before each request won't cause issues
# after tables are created. For a truly one-time setup before serving,
# you could use Flask signals (e.g., before_serving) but this is a simpler fix.
@app.before_request
def create_tables():
    db.create_all()

# --- New Routes for Frontend Rendering ---
@app.route('/')
@login_required
def index():
    """Renders the main index.html page."""
    return render_template('index.html',year=datetime.now().year)

@app.route('/pages/<page_name>')
def serve_page_partial(page_name):
    """
    Serves partial HTML pages dynamically.
    For example, /pages/register_bhakt will try to render templates/register_bhakt.html.
    """
    try:
        return render_template(f'{page_name}.html')
    except Exception as e:
        # Log the error for debugging
        print(f"Error loading page '{page_name}.html': {e}")
        return f"Error loading page: {e}", 404

# --- Existing Routes for Bhakt Management  & register new bhkta --->
@app.route('/bhakts', methods=['POST'])
def add_bhakt():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    # Check if mobile number already exists
    existing = Bhakt.query.filter_by(mobile_number=data['mobile_number']).first()
    if existing:
        return jsonify({'error': 'Mobile number already exists'}), 400

    try:
        # Ensure registration_number is stored as string
        registration_number = str(data['registration_number']).zfill(2)  # This will pad single digits with leading zeros
        abhishek_types = ','.join(data['abhishek_types']) if isinstance(data['abhishek_types'], list) else data['abhishek_types']

        new_bhakt = Bhakt(
            registration_number=data['registration_number'],  # Store as string with leading zeros
            name=data['name'],
            mobile_number=data['mobile_number'],
            address=data['address'],
            gotra=data.get('gotra', ''),
            email_address=data.get('email_address', ''),
            abhishek_types=abhishek_types,
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            validity_months=int(data.get('validity_months', 12)),
        )

        db.session.add(new_bhakt)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500




@app.route('/bhakts', methods=['GET'])
def get_bhakts():
    bhakts = Bhakt.query.all()
    output = []
    for bhakt in bhakts:
        output.append({
            'id': bhakt.id,
            'name': bhakt.name,
            'mobile_number': bhakt.mobile_number,
            'address': bhakt.address,
            'gotra': bhakt.gotra,
            'email_address': bhakt.email_address,
            'abhishek_types': bhakt.abhishek_types.split(',') if bhakt.abhishek_types else [],
            'start_date': bhakt.start_date.isoformat(),
            'validity_months': bhakt.validity_months,
            'expiration_date': bhakt.expiration_date.isoformat(),
            "registration_number": bhakt.registration_number,
            'is_active': bhakt.expiration_date >= datetime.utcnow().date()
        })
    return jsonify(output)

@app.route('/bhakts/<int:bhakt_id>', methods=['PUT'])
def update_bhakt(bhakt_id):
    bhakt = Bhakt.query.get_or_404(bhakt_id)
    data = request.json

    bhakt.name = data.get('name', bhakt.name)
    bhakt.mobile_number = data.get('mobile_number', bhakt.mobile_number)
    bhakt.address = data.get('address', bhakt.address)
    bhakt.gotra = data.get('gotra', bhakt.gotra)
    bhakt.email_address = data.get('email_address', bhakt.email_address)
    bhakt.abhishek_types = ','.join(data.get('abhishek_types', bhakt.abhishek_types.split(','))) if 'abhishek_types' in data else bhakt.abhishek_types

    if 'start_date' in data:
        bhakt.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if 'validity_months' in data:
        bhakt.validity_months = int(data['validity_months'])
    bhakt.calculate_expiration() # Recalculate expiration after update

    try:
        db.session.commit()
        return jsonify({'message': 'Bhakt updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/bhakts/<int:bhakt_id>', methods=['DELETE'])
def delete_bhakt(bhakt_id):
    bhakt = Bhakt.query.get_or_404(bhakt_id)
    try:
        db.session.delete(bhakt)
        db.session.commit()
        return jsonify({'message': 'Bhakt deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- Routes for Sacred Date Management ---
@app.route('/sacred_dates', methods=['POST'])
def add_sacred_date():
    data = request.json
    if not all(k in data for k in ['abhishek_type', 'date']):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        sacred_date = SacredDate(
            abhishek_type=data['abhishek_type'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date()
        )
        db.session.add(sacred_date)
        db.session.commit()
        return jsonify({'message': 'Sacred date added successfully', 'id': sacred_date.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/sacred_dates', methods=['GET'])
def get_sacred_dates():
    sacred_dates = SacredDate.query.all()
    output = []
    for sd in sacred_dates:
        output.append({
            'id': sd.id,
            'abhishek_type': sd.abhishek_type,
            'date': sd.date.isoformat()
        })
    return jsonify(output)

@app.route('/sacred_dates/<int:date_id>', methods=['PUT'])
def update_sacred_date(date_id):
    sacred_date = SacredDate.query.get_or_404(date_id)
    data = request.json
    sacred_date.abhishek_type = data.get('abhishek_type', sacred_date.abhishek_type)
    if 'date' in data:
        sacred_date.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    try:
        db.session.commit()
        return jsonify({'message': 'Sacred date updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/sacred_dates/<int:date_id>', methods=['DELETE'])
def delete_sacred_date(date_id):
    sacred_date = SacredDate.query.get_or_404(date_id)
    try:
        db.session.delete(sacred_date)
        db.session.commit()
        return jsonify({'message': 'Sacred date deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/export/monthly_schedule', methods=['GET'])
def export_monthly_schedule():
    from datetime import datetime
    today = datetime.utcnow().date()
    month = today.month
    year = today.year
    bhakts = Bhakt.query.filter(Bhakt.expiration_date >= today).all()
    sacred_dates = SacredDate.query.all()
    filtered_dates = [sd for sd in sacred_dates if sd.date.month == month and sd.date.year == year and sd.date >= today]

    # For each bhakt and abhishek type, find the nearest sacred date in this month
    nearest_dates = {}
    for bhakt in bhakts:
        bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",") if t.strip()]
        for abhishek_type in bhakt_types:
            # Find all sacred dates for this abhishek_type after or equal to today
            future_dates = [sd for sd in sacred_dates if sd.abhishek_type == abhishek_type and bhakt.expiration_date >= sd.date and sd.date >= today]
            if future_dates:
                # Pick only the single soonest one
                nearest = min(future_dates, key=lambda d: d.date)
                # Only include if the nearest date is in the selected month/year
                if nearest.date.month == month and nearest.date.year == year:
                    key = (bhakt.id, abhishek_type)
                    nearest_dates[key] = {
                        'Name': bhakt.name,
                        'Gotra': bhakt.gotra,
                        'Mobile': bhakt.mobile_number,
                        'Address': bhakt.address,
                        'Abhishek Type': abhishek_type,
                        'Date': nearest.date.strftime('%Y-%m-%d'),
                        'DateObj': nearest.date
                    }
    data_to_export = list(nearest_dates.values())
    for row in data_to_export:
        row.pop('DateObj', None)
    if not data_to_export:
        return jsonify({'message': 'No data to export'}), 404
    si = StringIO()
    cw = csv.DictWriter(si, fieldnames=data_to_export[0].keys())
    cw.writeheader()
    cw.writerows(data_to_export)
    output = si.getvalue()
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=monthly_abhishek_schedule.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/export/monthly_schedule_html', methods=['GET'])
def export_monthly_schedule_html():

    from datetime import datetime
    today = datetime.utcnow().date()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    abhishek_type = request.args.get('abhishek_type', '').strip()
    bhakts = Bhakt.query.filter(Bhakt.expiration_date >= today).all()
    sacred_dates = SacredDate.query.all()

    nearest_dates = {}
    output_columns = ['Name', 'Gotra', 'Abhishek Type']
    for bhakt in bhakts:
        bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",") if t.strip()]
        # If abhishek_type filter is set, only include matching types
        types_to_check = [abhishek_type] if abhishek_type else bhakt_types
        for ab_type in types_to_check:
            if ab_type not in bhakt_types:
                continue
            future_dates = [sd for sd in sacred_dates if sd.abhishek_type == ab_type and bhakt.expiration_date >= sd.date and sd.date >= today]
            if future_dates:
                nearest = min(future_dates, key=lambda d: d.date)
                if nearest.date.month == month and nearest.date.year == year:
                    key = (bhakt.id, ab_type)
                    nearest_dates[key] = {
                        
                        'Name': bhakt.name,
                        'Gotra': bhakt.gotra,
                        'Abhishek Type': ab_type,
                        
                    }
    data_to_export = list(nearest_dates.values())
    filtered_data = [
        {col: row[col] for col in output_columns}
        for row in data_to_export
    ]
    rendered = render_template('monthly_schedule_table.html', schedule=filtered_data)
    response = make_response(rendered)
    response.headers['Content-Disposition'] = f'attachment; filename={abhishek_type or "all"}_{month}_{year}_schedule.html'
    response.headers['Content-Type'] = 'text/html'
    return response

# @app.route("/bhakt_status")
# def view_bhakt_status():
#     bhakts = Bhakt.query.all()
#     return render_template("bhakt_status.html", bhakts=bhakts)

@app.route("/pages/bhakt_status")
def view_bhakt_status():
    bhakts = Bhakt.query.all()
    return render_template("bhakt_status.html", bhakts=bhakts, current_date=date.today())

from sqlalchemy import distinct

@app.route("/pages/combined_view")
def combined_view():
    bhakts = Bhakt.query.all()
    sacred_dates = SacredDate.query.order_by(SacredDate.date).all()
    result = []

    for sd in sacred_dates:
        for bhakt in bhakts:
            bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",") if t.strip()]
            if (
                sd.abhishek_type.strip() in bhakt_types and
                bhakt.expiration_date >= sd.date
            ):
                result.append({
                    "date": sd.date.strftime("%Y-%m-%d"),

                    "name": bhakt.name,
                    "gotra": bhakt.gotra,
                    "mobile": bhakt.mobile_number,
                    "registration_number": bhakt.registration_number,
                    "address": bhakt.address,
                    "type": sd.abhishek_type.strip()
                })

    abhishek_types = [row[0] for row in db.session.query(distinct(SacredDate.abhishek_type)).all()]

    return render_template("combined_view.html", abhishek_data=result, abhishek_types=abhishek_types)

@app.route("/api/combined_data")
def api_combined_data():
    bhakts = Bhakt.query.all()
    result = []

    for b in bhakts:
        result.append({
            "id": b.id,
            "registration_number": b.registration_number,  # <-- use the DB value as-is
            "name": b.name,
            "mobile_number": b.mobile_number,
            "address": b.address,
            "gotra": b.gotra,
            "email_address": b.email_address,
            "abhishek_types": b.abhishek_types,
            "start_date": b.start_date.strftime("%Y-%m-%d") if b.start_date else None,
            "expiration_date": b.expiration_date.strftime("%Y-%m-%d") if b.expiration_date else None,
            "validity_months": b.validity_months
        })
    
    return jsonify(result)


@app.route('/debug_sacred_dates')
def debug_sacred_dates():
    from models import SacredDate
    sacred_dates = SacredDate.query.all()
    return "<br>".join(f"{sd.date} - {sd.abhishek_type}" for sd in sacred_dates) or "No sacred dates found."

@app.route("/pages/sacred_dates")
def sacred_dates_view():
    sacred_dates = SacredDate.query.order_by(SacredDate.date).all()
    data = [{'date': sd.date.strftime('%Y-%m-%d'), 'occasion': sd.abhishek_type} for sd in sacred_dates]
    return render_template("sacred_dates.html", sacred_dates=data)

@app.route('/monthly_scheduler', methods=['POST'])
def monthly_scheduler():
    data = request.json
    month = int(data.get('month'))
    year = int(data.get('year'))
    from datetime import datetime
    today = datetime.utcnow().date()
    bhakts = Bhakt.query.filter(Bhakt.expiration_date >= today).all()
    sacred_dates = SacredDate.query.all()
    filtered_dates = [sd for sd in sacred_dates if sd.date.month == month and sd.date.year == year and sd.date >= today]

    result = []
    seen = set()
    for sd in filtered_dates:
        for bhakt in bhakts:
            bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",")]
            key = (bhakt.id, sd.abhishek_type, sd.date)
            if sd.abhishek_type in bhakt_types and bhakt.expiration_date >= sd.date and key not in seen:
                result.append({
                    "date": sd.date.strftime("%Y-%m-%d"),
                    "name": bhakt.name,
                    "gotra": bhakt.gotra,
                    "mobile": bhakt.mobile_number,
                    "address": bhakt.address,
                    "type": sd.abhishek_type
                })
                seen.add(key)
    return jsonify(result)

# @app.route('/abhishek_types')
# def get_abhishek_types():
#     conn = sqlite3.connect('abhishek_management.db')
#     cursor = conn.cursor()

#     cursor.execute("SELECT DISTINCT occasion FROM sacred_dates")
#     types = [row[0] for row in cursor.fetchall()]

#     conn.close()
#     return jsonify(types)

'''@app.route('/abhishek_types')
def get_abhishek_types():
    return jsonify(FIXED_ABHISHEKH_TYPES)
'''
#<!-- COMBINED FIXED AND DB TYPES -->
@app.route('/abhishek_types')
def get_abhishek_types():
    # Get distinct abhishek types from SacredDate table
    types = db.session.query(SacredDate.abhishek_type).distinct().all()
    db_types = {t[0] for t in types if t[0]}  # convert to set, skip None
    all_types = set(FIXED_ABHISHEKH_TYPES) | db_types  

    
    return jsonify(sorted(all_types))

#<!-- COMBINED FIXED AND DB TYPES END -->
@app.route('/edit_bhakt/<int:bhakt_id>', methods=['GET'])
def edit_bhakt_form(bhakt_id):
    bhakt = Bhakt.query.get_or_404(bhakt_id)
    return render_template('edit_bhakt.html', bhakt=bhakt)

#<--- REDIRECT VIEWS FOR FORM SUBMISSIONS -->
@app.route('/delete_bhakt/<int:bhakt_id>', methods=['GET'])
def delete_bhakt_redirect(bhakt_id):
    try:
        bhakt = Bhakt.query.get_or_404(bhakt_id)
        db.session.delete(bhakt)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
#<---------------------Update Bhakt form submission with redirect------------------------------------>
@app.route('/update_bhakt/<int:bhakt_id>', methods=['POST'])
def update_bhakt_form(bhakt_id):
    bhakt = Bhakt.query.get_or_404(bhakt_id)
    try:
        bhakt.name = request.form['name']
        bhakt.mobile_number = request.form['mobile_number']
        bhakt.address = request.form['address']
        bhakt.gotra = request.form.get('gotra')
        bhakt.abhishek_types = ','.join(request.form.getlist('abhishek_types[]'))
        bhakt.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        bhakt.validity_months = int(request.form['validity_months'])
        # Ensure expiration_date is recalculated
        bhakt.calculate_expiration()
        db.session.commit()
        next_url = request.form.get('next_url') or '/pages/bhakt_status'
        return redirect(next_url)
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
#<-------------------------Renew Bhakt Subscription------------------------------->
@app.route('/renew_bhakt/<int:bhakt_id>', methods=['POST'])
def renew_bhakt(bhakt_id):
    bhakt = Bhakt.query.get_or_404(bhakt_id)
    try:
        data = request.get_json(silent=True) or {}
        months = int(data.get('validity_months', 12))
        
        today = datetime.now(timezone.utc).date()  # ✅ Timezone-aware UTC, then date only
        
        # If subscription is still active, extend from expiration date, else start from today
        base_date = bhakt.expiration_date if bhakt.expiration_date and bhakt.expiration_date > today else today

        # Add months
        target_year = base_date.year
        target_month = base_date.month + months
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        max_day = calendar.monthrange(target_year, target_month)[1]
        target_day = min(base_date.day, max_day)

        bhakt.expiration_date = datetime(target_year, target_month, target_day).date()
        
        # Optional: update validity_months for record-keeping
        bhakt.validity_months = ((bhakt.expiration_date.year - bhakt.start_date.year) * 12 +
                                 (bhakt.expiration_date.month - bhakt.start_date.month))

        db.session.commit()
        return jsonify({'success': True, 'message': 'Bhakt renewed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    
#<---------------------------------View Monthly Schedule--------------------------------->
@app.route('/view/monthly_schedule', methods=['GET'])
def view_monthly_schedule():
    from datetime import datetime
    today = datetime.utcnow().date()
    month = today.month
    year = today.year
    bhakts = Bhakt.query.filter(Bhakt.expiration_date >= today).all()
    sacred_dates = SacredDate.query.all()
    filtered_dates = [sd for sd in sacred_dates if sd.date.month == month and sd.date.year == year and sd.date >= today]

    # Use the same filtered, tabular logic as the export
    output_columns = ['Date', 'Name', 'Gotra', 'Abhishek Type', 'Mobile', 'Address']
    nearest_dates = {}
    for bhakt in bhakts:
        bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",") if t.strip()]
        for abhishek_type in bhakt_types:
            # Find all sacred dates for this abhishek_type after or equal to today
            future_dates = [sd for sd in sacred_dates if sd.abhishek_type == abhishek_type and bhakt.expiration_date >= sd.date and sd.date >= today]
            if future_dates:
                # Pick only the single soonest one
                nearest = min(future_dates, key=lambda d: d.date)
                # Only include if the nearest date is in the selected month/year
                if nearest.date.month == month and nearest.date.year == year:
                    key = (bhakt.id, abhishek_type)
                    nearest_dates[key] = {
                        'Date': nearest.date.strftime('%Y-%m-%d'),
                        'Name': bhakt.name,
                        'Gotra': bhakt.gotra,
                        'Abhishek Type': abhishek_type,
                        'Mobile': bhakt.mobile_number,
                        'Address': bhakt.address
                    }
    data_to_display = list(nearest_dates.values())
    return render_template('monthly_schedule_table.html', schedule=data_to_display)
#<---------------------------------Export Bhakts as CSV--------------------------------->
@app.route('/export/bhakts', methods=['GET'])
def export_bhakts():
    bhakts = Bhakt.query.all()
    if not bhakts:
        return jsonify({'message': 'No bhakts to export'}), 404
    si = StringIO()
    fieldnames = ['Name', 'Mobile', 'Email', 'Gotra', 'Address', 'Abhishek Types', 'Start Date', 'Validity (Months)', 'Expiration Date']
    cw = csv.DictWriter(si, fieldnames=fieldnames)
    cw.writeheader()
    for b in bhakts:
        cw.writerow({
            'Name': b.name,
            'Mobile': b.mobile_number,
            'Email': b.email_address,
            'Gotra': b.gotra,
            'Address': b.address,
            'Abhishek Types': b.abhishek_types,
            'Start Date': b.start_date.strftime('%Y-%m-%d'),
            'Validity (Months)': b.validity_months,
            'Expiration Date': b.expiration_date.strftime('%Y-%m-%d')
        })
    output = si.getvalue()
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=bhakts.csv"
    response.headers["Content-type"] = "text/csv"
    return response


#<---------------------------------API to get Bhakts expired last month--------------------------------->
@app.route('/bhakts/expired_last_month', methods=['GET'])
def bhakts_expired_last_month():
    today = datetime.utcnow().date()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)

    expired_bhakts = Bhakt.query.filter(
        Bhakt.expiration_date >= first_day_last_month,
        Bhakt.expiration_date <= last_day_last_month
    ).all()

    output = []
    for bhakt in expired_bhakts:
        output.append({
            'id': bhakt.id,
            'name': bhakt.name,
            'mobile_number': bhakt.mobile_number,
            'address': bhakt.address,
            'gotra': bhakt.gotra,
            'email_address': bhakt.email_address,
            'abhishek_types': bhakt.abhishek_types.split(',') if bhakt.abhishek_types else [],
            'start_date': bhakt.start_date.isoformat(),
            'validity_months': bhakt.validity_months,
            'expiration_date': bhakt.expiration_date.isoformat(),
        })
    return jsonify(output)
#<---------------------------------Export Full Monthly Schedule as CSV--------------------------------->
@app.route('/export/monthly_schedule_full', methods=['GET'])
def export_monthly_schedule_full():
    # Get month and year from query params
    month = int(request.args.get('month', datetime.utcnow().month))
    year = int(request.args.get('year', datetime.utcnow().year))
    today = datetime.utcnow().date()
    bhakts = Bhakt.query.filter(Bhakt.expiration_date >= today).all()
    sacred_dates = SacredDate.query.all()
    filtered_dates = [sd for sd in sacred_dates if sd.date.month == month and sd.date.year == year]

    data_to_export = []
    seen = set()
    for sd in filtered_dates:
        for bhakt in bhakts:
            bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",")]
            key = (bhakt.id, sd.abhishek_type, sd.date)
            if sd.abhishek_type in bhakt_types and bhakt.expiration_date >= sd.date and key not in seen:
                data_to_export.append({     
                    'Abhishek Type': sd.abhishek_type,
                    'Name': bhakt.name,
                    'Gotra': bhakt.gotra,                    
                })
                seen.add(key)
    if not data_to_export:
        return jsonify({'message': 'No data to export'}), 404
    si = StringIO()
    cw = csv.DictWriter(si, fieldnames=data_to_export[0].keys())
    cw.writeheader()
    cw.writerows(data_to_export)
    output = si.getvalue()
    response = make_response(output)
    response.headers["Content-Disposition"] = f"attachment; filename=monthly_schedule_{month}_{year}.csv"
    response.headers["Content-type"] = "text/csv"
    return response
#<---------------------------------API to get Bhakts expiring in next 30 days--------------------------------->
@app.route('/bhakts/expiring_soon', methods=['GET'])
def bhakts_expiring_soon():
    today = datetime.utcnow().date()
    thirty_days_from_now = today + timedelta(days=30)
    expiring_bhakts = Bhakt.query.filter(
        Bhakt.expiration_date > today,
        Bhakt.expiration_date <= thirty_days_from_now
    ).all()

    output = []
    for bhakt in expiring_bhakts:
        output.append({
            'id': bhakt.id,
            'name': bhakt.name,
            'mobile_number': bhakt.mobile_number,
            'address': bhakt.address,
            'gotra': bhakt.gotra,
            'email_address': bhakt.email_address,
            'abhishek_types': bhakt.abhishek_types.split(',') if bhakt.abhishek_types else [],
            'start_date': bhakt.start_date.isoformat(),
            'validity_months': bhakt.validity_months,
            'expiration_date': bhakt.expiration_date.isoformat(),
        })
    return jsonify(output)
#<----------------------Label Code------------------------------------------------------------------->
def check_admin():
    password = request.args.get('admin_password') or request.form.get('admin_password') or request.headers.get('X-Admin-Password')
    if password != ADMIN_PASSWORD:
        abort(403, description="Admin access required.")

#<----------------------Database Backup and Restore------------------------------------------>
@app.route('/backup_db', methods=['GET'])
def backup_db():
    check_admin()
    db_path = os.path.join(basedir, 'abhishek_management.db')
    return send_file(db_path, as_attachment=True, download_name='abhishek_management_backup.db')


#<----------------------Database Backup and Restore End--------------------------------------->
@app.route('/restore_db', methods=['POST'])
def restore_db():
    check_admin()
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    db_path = os.path.join(basedir, 'abhishek_management.db')
    file.save(db_path)
    return jsonify({'message': 'Database restored successfully'})
#<----------------------Email DB Backup------------------------------------------>
@app.route('/send_db_backup', methods=['POST'])
def send_db_backup():
    check_admin()
    # Get recipient email from request
    recipient = request.json.get('email')
    if not recipient:
        return jsonify({'error': 'No email provided'}), 400

    db_path = os.path.join(basedir, 'abhishek_management.db')
    if not os.path.exists(db_path):
        return jsonify({'error': 'Database file not found'}), 404

    # Gmail SMTP config
    GMAIL_USER = os.environ.get('GMAIL_USER', 'yourgmail@gmail.com')
    GMAIL_PASS = os.environ.get('GMAIL_PASS', 'Pass@123')

    msg = EmailMessage()
    msg['Subject'] = 'Abhishek Management Database Backup'
    msg['From'] = GMAIL_USER
    msg['To'] = recipient
    msg.set_content('Attached is the latest database backup.')

    with open(db_path, 'rb') as f:
        db_data = f.read()
        msg.add_attachment(db_data, maintype='application', subtype='octet-stream', filename='abhishek_management.db')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        return jsonify({'message': 'Backup sent successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
#<----------------------Email DB Backup End------------------------------------------>
@app.route('/export/monthly_schedule_filtered', methods=['GET'])
def export_monthly_schedule_filtered():
    month = int(request.args.get('month', datetime.utcnow().month))
    year = int(request.args.get('year', datetime.utcnow().year))
    abhishek_type = request.args.get('abhishek_type', '').strip()
    today = datetime.utcnow().date()

    # Get all bhakts whose subscription is still active
    bhakts = Bhakt.query.filter(Bhakt.expiration_date >= today).all()

    data_to_export = []
    for bhakt in bhakts:
        bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",") if t.strip()]
        # Only include bhakt if abhishek_type matches (or if no filter is given)
        types_to_export = [abhishek_type] if abhishek_type else bhakt_types
        for ab_type in types_to_export:
            if ab_type in bhakt_types:
                # Check if bhakt is active in the selected month
                exp_month = bhakt.expiration_date.month
                exp_year = bhakt.expiration_date.year
                if (exp_year > year) or (exp_year == year and exp_month >= month):
                    data_to_export.append({
                        'Name': bhakt.name,
                        'Gotra': bhakt.gotra,
                        'Abhishek Type': ab_type,
                        
                    })

    if not data_to_export:
        return jsonify({'message': 'No data to export'}), 404

    # CSV export
    fieldnames = ['Name', 'Gotra', 'Abhishek Type']
    si = StringIO()
    cw = csv.DictWriter(si, fieldnames=fieldnames)
    cw.writeheader()
    cw.writerows(data_to_export)
    output = si.getvalue()
    
    response = make_response(output)
    response.headers["Content-Disposition"] = f"attachment; filename={abhishek_type or 'all'}_{month}_{year}_schedule.csv"
    response.headers["Content-type"] = "text/csv"
    return response
#<----------------------Label Code----------------------------------------------------------------------->

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current = (request.form.get('current_password') or '').strip()
    new = (request.form.get('new_password') or '').strip()
    confirm = (request.form.get('confirm_password') or '').strip()

    if not current or not new or not confirm:
        flash('All fields are required.', 'error')
        return redirect(url_for('index'))

    if new != confirm:
        flash('New password and confirmation do not match.', 'error')
        return redirect(url_for('index'))

    # Reload the user from DB to avoid stale session object
    user = User.query.get(int(current_user.get_id()))
    if not user or not user.check_password(current):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('index'))

    user.set_password(new)
    db.session.commit()

    flash('Password changed successfully. Please login again.', 'success')
    logout_user()
    return redirect(url_for('login'))

@app.route('/update_special_date', methods=['POST'])
@login_required
def update_special_date():
    data = request.get_json()
    subscriber_id = data.get('subscriber_id')
    selected_date = datetime.strptime(data.get('selected_date'), '%Y-%m-%d').date()

    # Check if date is already taken by another subscriber
    existing_subscriber = Subscriber.query.filter_by(special_date_selected=selected_date).first()
    if existing_subscriber and existing_subscriber.id != subscriber_id:
        return jsonify({'error': 'This date is already booked by another subscriber'}), 400

    subscriber = Subscriber.query.get(subscriber_id)
    if subscriber:
        subscriber.special_date = True
        subscriber.special_date_selected = selected_date
        db.session.commit()
        return jsonify({'message': 'Special date updated successfully'}), 200
    return jsonify({'error': 'Subscriber not found'}), 404

@app.route('/register', methods=['POST'])
@login_required
def register_subscriber():
    data = request.get_json()
    
    # Basic subscriber details
    name = data.get('name')
    mobile = data.get('mobile')
    address = data.get('address')
    wants_special_date = data.get('special_date', False)
    special_date_selected = None

    if wants_special_date:
        special_date = data.get('special_date_selected')
        if special_date:
            special_date_selected = datetime.strptime(special_date, '%Y-%m-%d').date()
            
            # Check if date is already taken
            existing = Subscriber.query.filter_by(special_date_selected=special_date_selected).first()
            if existing:
                return jsonify({
                    'error': 'This special date is already taken by another subscriber'
                }), 400

    new_subscriber = Subscriber(
        name=name,
        mobile=mobile,
        address=address,
        special_date=wants_special_date,
        special_date_selected=special_date_selected
    )

    try:
        db.session.add(new_subscriber)
        db.session.commit()
        return jsonify({'message': 'Subscriber registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
@app.route('/reset-password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('Invalid user.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('reset_password', username=username))

        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password reset successfully. Please login.')
        return redirect(url_for('login'))

    return render_template('reset_password.html', username=username)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()

        if not user:
            flash('No user found with that username.')
            return redirect(url_for('forgot_password'))

        # For now: simple approach — redirect to reset form
        return redirect(url_for('reset_password', username=username))

    return render_template('forgot_password.html')

def upgrade_data():
    with app.app_context():
        bhakts = Bhakt.query.all()
        for bhakt in bhakts:
            bhakt.registration_number = str(bhakt.registration_number).zfill(2)
        db.session.commit()

def open_browser():
    webbrowser.open("http://127.0.0.1:5000/")
if __name__ == '__main__':
    
    Timer(1, open_browser).start()
    # Use Waitress for production-like EXE
    serve(app, host='127.0.0.1', port=5000)
