import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all origins for /api/* routes (adjust for production)

# Initialize SQLite database with demo users
def init_db():
    conn = sqlite3.connect('eqr.db')
    c = conn.cursor()
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, phone TEXT, organization TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS self_assessment_reports
                 (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS submission_reports
                 (id INTEGER PRIMARY KEY, user_id INTEGER, state TEXT, township TEXT, need_type TEXT, need_detail TEXT, 
                  damage_type TEXT, damage_name TEXT, latitude REAL, longitude REAL, inaccessibility_cause TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS training_events
                 (id INTEGER PRIMARY KEY, title TEXT, date TEXT, location TEXT)''')
    
    # Insert demo users
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ("member1", "pass123", "member"))
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ("org1", "orgpass", "organization"))
    
    # Insert demo training events
    c.execute("INSERT OR IGNORE INTO training_events (title, date, location) VALUES (?, ?, ?)", ("First Aid Basics", "2025-07-01", "Yangon"))
    c.execute("INSERT OR IGNORE INTO training_events (title, date, location) VALUES (?, ?, ?)", ("Disaster Preparedness", "2025-07-15", "Mandalay"))
    c.execute("INSERT OR IGNORE INTO training_events (title, date, location) VALUES (?, ?, ?)", ("Evacuation Drills", "2025-08-01", "Shan"))
    
    # Insert demo submission reports
    c.execute("INSERT OR IGNORE INTO submission_reports (user_id, state, township, need_type, need_detail, damage_type, damage_name, latitude, longitude, inaccessibility_cause, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
              (1, "Yangon", "Hlaing", "Food", "Food shortage", "Road", "Main Road", 16.8409, 96.1704, "Damage by Disaster", "2025-06-27 15:00:00"))
    c.execute("INSERT OR IGNORE INTO submission_reports (user_id, state, township, need_type, need_detail, damage_type, damage_name, latitude, longitude, inaccessibility_cause, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
              (1, "Mandalay", "Aungmyethazan", "Shelter", "Temporary shelters needed", "Building", "School", 21.9747, 96.0836, "Security", "2025-06-27 14:00:00"))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.form
    conn = sqlite3.connect('eqr.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, role, phone, organization) VALUES (?, ?, ?, ?, ?)",
              (data['username'], data['password'], data['role'], data.get('phone', ''), data.get('organization', '')))
    conn.commit()
    conn.close()
    return jsonify({"message": "User registered"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.form
    conn = sqlite3.connect('eqr.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ? AND role = ?", 
              (data['username'], data['password'], data['role']))
    user = c.fetchone()
    conn.close()
    if user:
        session['user_id'] = user[0]  # Store user ID in session
        session['role'] = user[3]    # Store role in session
        if user[3] == "member":
            return jsonify({"message": "Login successful", "user_id": user[0], "role": user[3]}), 200
        elif user[3] == "organization":
            return jsonify({"message": "Login successful", "user_id": user[0], "role": user[3]}), 200
    return jsonify({"message": "Invalid credentials or role"}), 401

@app.route('/dashboard')
def dashboard():
    if 'role' in session and session['role'] == "member":
        return redirect(url_for('member_dashboard'))
    elif 'role' in session and session['role'] == "organization":
        return redirect(url_for('organization_dashboard'))
    return redirect(url_for('home'))

@app.route('/member_dashboard')
def member_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    conn = sqlite3.connect('eqr.db')
    c = conn.cursor()
    c.execute("SELECT title, date, location FROM training_events")
    trainings = c.fetchall()
    conn.close()
    return render_template('member_dashboard.html', trainings=trainings)

@app.route('/api/submit_assessment', methods=['POST'])
def submit_assessment():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401
    data = request.form
    conn = sqlite3.connect('eqr.db')
    c = conn.cursor()
    c.execute("INSERT INTO self_assessment_reports (user_id, content, timestamp) VALUES (?, ?, ?)",
              (session['user_id'], data.get('hurt_status', ''), "2025-06-27 15:00:00"))
    conn.commit()
    conn.close()
    return jsonify({"message": "Assessment submitted"}), 201

@app.route('/api/submit_report', methods=['POST'])
def submit_report():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401
    data = request.form
    conn = sqlite3.connect('eqr.db')
    c = conn.cursor()
    c.execute("INSERT INTO submission_reports (user_id, state, township, need_type, need_detail, damage_type, damage_name, latitude, longitude, inaccessibility_cause, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (session['user_id'], 
               data.get('state', ''), 
               data.get('township', ''), 
               data.get('primary_need', ''), 
               data.get('secondary_need', ''), 
               data.get('damage_type', ''), 
               data.get('damage_name', ''), 
               float(data.get('latitude', 0.0)), 
               float(data.get('longitude', 0.0)), 
               data.get('inaccessibility_cause', ''), 
               "2025-06-27 15:00:00"))
    conn.commit()
    conn.close()
    return jsonify({"message": "Report submitted"}), 201

@app.route('/organization_dashboard')
def organization_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template('organization_dashboard.html')

@app.route('/api/reports')
def get_reports():
    conn = sqlite3.connect('eqr.db')
    c = conn.cursor()
    c.execute("SELECT need_type, need_detail, latitude, longitude FROM submission_reports")
    reports = [{"need_type": row[0], "need_detail": row[1], "latitude": row[2], "longitude": row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(reports)

if __name__ == '__main__':
    app.run(debug=True, port=5001)