from flask import Flask, request, jsonify, render_template, redirect,  url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from models import db, Bhakt, SacredDate # Import models from models.py
import csv
from io import StringIO
from flask import make_response
import sqlite3
from datetime import date
import sys
import smtplib
from email.message import EmailMessage

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
# from models import SacredDate


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'abhishek_management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

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

# --- Existing Routes for Bhakt Management ---
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
        abhishek_types = ','.join(data['abhishek_types']) if isinstance(data['abhishek_types'], list) else data['abhishek_type']

        new_bhakt = Bhakt(
            name=data['name'],
            mobile_number=data['mobile_number'],
            address=data['address'],
            gotra=data.get('gotra', ''),
            email_address=data.get('email_address', ''),
            abhishek_types=abhishek_types,  # ✅ FIXED
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d'),
            validity_months=int(data.get('validity_months', 12))
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

    data_to_export = []
    seen = set()
    for sd in filtered_dates:
        for bhakt in bhakts:
            bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",")]
            key = (bhakt.id, sd.abhishek_type, sd.date)
            if sd.abhishek_type in bhakt_types and bhakt.expiration_date >= sd.date and key not in seen:
                data_to_export.append({
                    'Name': bhakt.name,
                    'Gotra': bhakt.gotra,
                    'Mobile': bhakt.mobile_number,
                    'Address': bhakt.address,
                    'Abhishek Type': sd.abhishek_type,
                    'Date': sd.date.strftime('%Y-%m-%d')
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
    response.headers["Content-Disposition"] = "attachment; filename=monthly_abhishek_schedule.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/export/monthly_schedule_html', methods=['GET'])
def export_monthly_schedule_html():
    from datetime import datetime
    today = datetime.utcnow().date()
    month = today.month
    year = today.year
    bhakts = Bhakt.query.filter(Bhakt.expiration_date >= today).all()
    sacred_dates = SacredDate.query.all()
    filtered_dates = [sd for sd in sacred_dates if sd.date.month == month and sd.date.year == year and sd.date >= today]

    data_to_export = []
    seen = set()
    for sd in filtered_dates:
        for bhakt in bhakts:
            bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",")]
            key = (bhakt.id, sd.abhishek_type, sd.date)
            if sd.abhishek_type in bhakt_types and bhakt.expiration_date >= sd.date and key not in seen:
                data_to_export.append({
                    'Name': bhakt.name,
                    'Gotra': bhakt.gotra,
                    'Mobile': bhakt.mobile_number,
                    'Address': bhakt.address,
                    'Abhishek_Type': sd.abhishek_type,
                    'Date': sd.date.strftime('%Y-%m-%d')
                })
                seen.add(key)
    rendered = render_template('monthly_schedule_table.html', schedule=data_to_export)
    response = make_response(rendered)
    response.headers['Content-Disposition'] = 'attachment; filename=monthly_abhishek_schedule.html'
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
                    "address": bhakt.address,
                    "type": sd.abhishek_type.strip()
                })

    abhishek_types = [row[0] for row in db.session.query(distinct(SacredDate.abhishek_type)).all()]

    return render_template("combined_view.html", abhishek_data=result, abhishek_types=abhishek_types)


@app.route("/api/combined_data")
def api_combined_data():
    bhakts = Bhakt.query.all()
    sacred_dates = SacredDate.query.all()
    result = []
    for sd in sacred_dates:
        for bhakt in bhakts:
            bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",") if t.strip()]
            if sd.abhishek_type.strip() in bhakt_types:
                result.append({
                    "date": sd.date.strftime("%Y-%m-%d"),
                    "name": bhakt.name,
                    "gotra": bhakt.gotra,
                    "mobile": bhakt.mobile_number,
                    "address": bhakt.address,
                    "type": sd.abhishek_type.strip()
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

@app.route('/abhishek_types')
def get_abhishek_types():
    types = db.session.query(SacredDate.abhishek_type).distinct().all()
    unique_types = sorted({t[0] for t in types})
    return jsonify(unique_types)


@app.route('/edit_bhakt/<int:bhakt_id>', methods=['GET'])
def edit_bhakt_form(bhakt_id):
    bhakt = Bhakt.query.get_or_404(bhakt_id)
    return render_template('edit_bhakt.html', bhakt=bhakt)

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

@app.route('/renew_bhakt/<int:bhakt_id>', methods=['POST'])
def renew_bhakt(bhakt_id):
    bhakt = Bhakt.query.get_or_404(bhakt_id)
    try:
        data = request.get_json(silent=True) or {}
        months = int(data.get('validity_months', 12))
        bhakt.start_date = datetime.utcnow().date()
        bhakt.validity_months = months
        bhakt.calculate_expiration()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

    except Exception as e:
        db.session.rollback()
        return f"Error renewing bhakt: {e}", 500


@app.route('/view/monthly_schedule', methods=['GET'])
def view_monthly_schedule():
    from datetime import datetime
    today = datetime.utcnow().date()
    month = today.month
    year = today.year
    bhakts = Bhakt.query.filter(Bhakt.expiration_date >= today).all()
    sacred_dates = SacredDate.query.all()
    filtered_dates = [sd for sd in sacred_dates if sd.date.month == month and sd.date.year == year and sd.date >= today]

    data_to_display = []
    seen = set()
    for sd in filtered_dates:
        for bhakt in bhakts:
            bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",")]
            key = (bhakt.id, sd.abhishek_type, sd.date)
            if sd.abhishek_type in bhakt_types and bhakt.expiration_date >= sd.date and key not in seen:
                data_to_display.append({
                    'Name': bhakt.name,
                    'Gotra': bhakt.gotra,
                    'Mobile': bhakt.mobile_number,
                    'Address': bhakt.address,
                    'Abhishek_Type': sd.abhishek_type,
                    'Date': sd.date.strftime('%Y-%m-%d')
                })
                seen.add(key)
    return render_template('monthly_schedule_table.html', schedule=data_to_display)

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
                    'Date': sd.date.strftime('%Y-%m-%d'),
                    'Day': sd.date.strftime('%A'),
                    'Abhishek Type': sd.abhishek_type,
                    'Name': bhakt.name,
                    'Gotra': bhakt.gotra,
                    'Mobile': bhakt.mobile_number,
                    'Email': bhakt.email_address,
                    'Address': bhakt.address,
                    'Validity (Months)': bhakt.validity_months,
                    'Expiration Date': bhakt.expiration_date.strftime('%Y-%m-%d')
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

def check_admin():
    password = request.args.get('admin_password') or request.form.get('admin_password') or request.headers.get('X-Admin-Password')
    if password != ADMIN_PASSWORD:
        abort(403, description="Admin access required.")

@app.route('/backup_db', methods=['GET'])
def backup_db():
    check_admin()
    db_path = os.path.join(basedir, 'abhishek_management.db')
    return send_file(db_path, as_attachment=True, download_name='abhishek_management_backup.db')

@app.route('/restore_db', methods=['POST'])
def restore_db():
    check_admin()
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    db_path = os.path.join(basedir, 'abhishek_management.db')
    file.save(db_path)
    return jsonify({'message': 'Database restored successfully'})

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

if __name__ == '__main__':
    # This runs Flask in development mode.
    # For production, we'll use a production-ready WSGI server like Waitress.
    app.run(debug=True, host='127.0.0.1', port=5000)