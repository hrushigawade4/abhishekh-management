from flask import Flask, request, jsonify, render_template
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
    return render_template('index.html')

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
    # (Implement logic to get monthly schedule data similar to /monthly_scheduler route)
    data_to_export = [] # This will be list of dictionaries for each row
    # Example:
    # data_to_export.append({'Name': 'Bhakt A', 'Gotra': 'G', 'Mobile': '123', 'Address': 'XYZ', 'Abhishek Type': 'Pournima', 'Date': '2025-08-01'})

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

    bhakts = Bhakt.query.all()
    sacred_dates = SacredDate.query.all()

    filtered_dates = [sd for sd in sacred_dates if sd.date.month == month and sd.date.year == year]

    result = []
    for sd in filtered_dates:
        for bhakt in bhakts:
            bhakt_types = [t.strip() for t in bhakt.abhishek_types.split(",")]
            if sd.abhishek_type in bhakt_types and bhakt.expiration_date >= sd.date:
                result.append({
                    "date": sd.date.strftime("%Y-%m-%d"),
                    "name": bhakt.name,
                    "gotra": bhakt.gotra,
                    "mobile": bhakt.mobile_number,
                    "address": bhakt.address,
                    "type": sd.abhishek_type
                })

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



if __name__ == '__main__':
    # This runs Flask in development mode.
    # For production, we'll use a production-ready WSGI server like Waitress.
    app.run(debug=True, host='127.0.0.1', port=5000)