#!./venv/bin/python3
import os
import cv2
from flask import Flask, render_template, Response, redirect, url_for, session, flash, request, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from dumbel_curl_script import PoseDetector
from flask_cors import CORS
import io
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit
import base64
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfgen import canvas
import csv
import time
from chatbot_handler import chatbot_bp

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.secret_key = os.getenv("SECRET_KEY", "__privatekey__")
app.config['STATIC_URL_PATH'] = '/static'
app.config['STATIC_FOLDER'] = 'static'
app.config['UPLOAD_FOLDER'] = os.path.join(app.config['STATIC_FOLDER'], 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins="*")
pose_detector = PoseDetector()

# Register blueprints
app.register_blueprint(chatbot_bp)

# Create the uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    profile_picture = db.Column(db.String(100), nullable=True)

    def __init__(self, name, email, password, age, height, weight, profile_picture=None):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)  # Hash the password
        self.age = age
        self.height = height
        self.weight = weight
        self.profile_picture = profile_picture

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    date = db.Column(db.DateTime, default=datetime.now())

    user = db.relationship('User', back_populates='workouts')

    def __init__(self, user_id, date, exercise, sets, reps, weight=None):
        self.user_id = user_id
        self.date = date if date else datetime.now()
        self.exercise = exercise
        self.sets = sets
        self.reps = reps
        self.weight = weight

    def to_dict(self):
        return {
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'exercise': self.exercise,
            'sets': self.sets,
            'reps': self.reps,
            'weight': self.weight
        }

User.workouts = db.relationship('Workout', order_by=Workout.id, back_populates='user')

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    tracking_points = db.Column(db.String(200), nullable=False)  # JSON string of body points to track

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'instructions': self.instructions,
            'tracking_points': self.tracking_points
        }

# Global camera object
camera = None

@app.context_processor
def inject_template_vars():
    # Get current endpoint
    endpoint = request.endpoint if request else None
    
    # Hide chatbot and nav on authentication pages
    hide_chatbot = endpoint in ['index', 'login', 'register']
    hide_nav = hide_chatbot
    
    return {
        'hide_chatbot': hide_chatbot,
        'hide_nav': hide_nav
    }

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        values['v'] = int(time.time())
    return url_for(endpoint, **values)

@app.route('/workouts', methods=['GET', 'POST'])
def workouts():
    if 'user_id' in session:
        user_id = session['user_id']

        if request.method == 'POST':
            exercise = request.form['exercise']
            sets = request.form['sets']
            reps = request.form['reps']
            weight = request.form['weight'] if request.form['weight'] else None

            new_workout = Workout(user_id=user_id, date=datetime.now(), exercise=exercise, sets=sets, reps=reps, weight=weight)
            db.session.add(new_workout)
            db.session.commit()

            flash('Workout logged successfully')
            return redirect(url_for('workouts'))

        user = User.query.filter_by(id=user_id).first()
        workout_objects = Workout.query.filter_by(user_id=user_id).all()
        workouts = [workout.to_dict() for workout in workout_objects]
        return render_template('workouts.html', user=user, workouts=workouts)
    else:
        return redirect(url_for('index'))

@app.route('/download_workouts', methods=['GET'])
def download_workouts():
    if 'user_id' in session:
        user_id = session['user_id']
        workouts = Workout.query.filter_by(user_id=user_id).all()

        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()

        # Create the PDF object, using the buffer as its "file."
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Table data
        data = [["Date", "Exercise", "Sets", "Reps", "Weight"]]
        for workout in workouts:
            data.append([
                workout.date.strftime('%Y-%m-%d %H:%M:%S'),
                workout.exercise,
                workout.sets,
                workout.reps,
                workout.weight if workout.weight is not None else "N/A"
            ])

        # Create the table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        # Build the PDF
        doc.build(elements)

        # Return the PDF as a response
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f'workouts_{user_id}.pdf', mimetype='application/pdf')
    else:
        return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    if user:
        print("Stored hashed password:", user.password)  # Debug print
        print("Provided password:", password)  # Debug print
        if check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!')
            return redirect(url_for('info'))
        else:
            print("Password mismatch")
    else:
        print("User not found")
    
    flash('Invalid email or password')
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    age = request.form['age']
    height = request.form['height']
    weight = request.form['weight']
    if User.query.filter_by(email=email).first():
        flash('Email already registered')
        return redirect(url_for('index'))

    new_user = User(name=name, email=email, password=password, age=age, height=height, weight=weight)  # Password will be hashed in User model
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/info')
def info():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('info.html', user=user)
    else:
        return redirect(url_for('index'))

@app.route('/guest_info')
def guest_info():
    return render_template('info.html', user=None)

@app.route('/profile')
def profile():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('profile.html', user=user)
    else:
        return redirect(url_for('index'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        user.name = request.form['name']
        user.email = request.form['email']
        user.age = request.form['age']
        user.height = request.form['height']
        user.weight = request.form['weight']

        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                user.profile_picture = filename

        db.session.commit()
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('index'))

@app.route('/diet')
def diet():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('diet.html', user=user)
    else:
        return redirect(url_for('index'))

@app.route('/update_diet', methods=['POST'])
def update_diet():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        user.weight = request.form['weight']
        db.session.commit()
        return redirect(url_for('diet'))
    else:
        return redirect(url_for('index'))

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    global camera
    print('Client disconnected')
    if camera is not None:
        camera.release()
        camera = None

@socketio.on('start-stream')
def start_stream():
    global camera
    try:
        if camera is None:
            camera = cv2.VideoCapture(0)
        
        while True:
            success, frame = camera.read()
            if not success:
                print("Failed to grab frame")
                break
            
            # Process frame with pose detection
            frame = pose_detector.process_frame(frame)  # Changed from findPose to process_frame
            
            # Convert frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = base64.b64encode(buffer).decode('utf-8')
            
            # Emit frame to client
            emit('video-frame', {'frame': frame_bytes})
            socketio.sleep(0.1)  # Add small delay to prevent overwhelming the connection
            
    except Exception as e:
        print(f"Error in video stream: {str(e)}")
        print(f"Error details:", e.__class__.__name__)
        import traceback
        traceback.print_exc()
    finally:
        if camera is not None:
            camera.release()
            camera = None

@app.route('/exercise')
def exercise():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    exercises = Exercise.query.all()
    return render_template('exercise.html', exercises=exercises)

@app.route('/api/exercises')
def get_exercises():
    exercises = Exercise.query.all()
    return jsonify([exercise.to_dict() for exercise in exercises])

@app.route('/generate_pdf')
def generate_pdf():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        bmi = round(user.weight / ((user.height / 100) ** 2), 2)

        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()

        # Create the PDF object, using the buffer as its "file."
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Draw the user data on the PDF
        pdf.drawString(100, height - 100, f"Name: {user.name}")
        pdf.drawString(100, height - 120, f"Email: {user.email}")
        pdf.drawString(100, height - 140, f"Age: {user.age}")
        pdf.drawString(100, height - 160, f"Height: {user.height} cm")
        pdf.drawString(100, height - 180, f"Weight: {user.weight} kg")
        pdf.drawString(100, height - 200, f"BMI: {bmi}")

        # Determine BMI status
        if bmi < 19:
            bmi_status = "Underweight"
            diet_suggestions = [
                "Eat more frequently. Have 5-6 small meals throughout the day.",
                "Include nutrient-rich foods in your diet, such as whole grains, lean proteins, and healthy fats.",
                "Drink high-calorie smoothies and shakes.",
                "Snack on nuts, seeds, and dried fruits.",
                "Stay hydrated and avoid skipping meals."
            ]
        elif bmi >= 19 and bmi <= 25:
            bmi_status = "Normal"
            diet_suggestions = [
                "Maintain a balanced diet with a variety of foods from all food groups.",
                "Eat plenty of fruits and vegetables.",
                "Include lean proteins, whole grains, and healthy fats in your meals.",
                "Stay hydrated by drinking plenty of water.",
                "Avoid sugary drinks and excessive junk food."
            ]
        else:
            bmi_status = "Overweight"
            diet_suggestions = [
                "Eat more fruits and vegetables.",
                "Choose whole grains over refined grains.",
                "Include lean proteins, such as chicken, fish, beans, and legumes.",
                "Avoid sugary drinks and opt for water or herbal teas.",
                "Reduce your intake of high-calorie, low-nutrient foods.",
                "Practice portion control and avoid eating late at night."
            ]

        pdf.drawString(100, height - 220, f"BMI Status: {bmi_status}")
        pdf.drawString(100, height - 240, "Diet Suggestions:")

        y = height - 260
        for suggestion in diet_suggestions:
            pdf.drawString(120, y, f"- {suggestion}")
            y -= 20

        # Close the PDF object cleanly
        pdf.showPage()
        pdf.save()

        # Get the value of the BytesIO buffer and write it to the response
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='diet_plan.pdf', mimetype='application/pdf')
    else:
        return redirect(url_for('index'))

@app.route('/nearest_gym')
def nearest_gym():
    api_key = ''
    return render_template('nearest_gym.html', api_key=api_key)

def init_exercises():
    # Check if exercises already exist
    if Exercise.query.count() > 0:
        return

    exercises = [
        {
            'name': 'Dumbbell Curl',
            'description': 'A classic bicep exercise that targets the muscles in your upper arm.',
            'instructions': '''1. Stand with feet shoulder-width apart
2. Hold dumbbells at your sides with palms facing forward
3. Keep your upper arms stationary and elbows close to your torso
4. Curl the weights up towards your shoulders
5. Slowly lower the weights back to starting position
6. Keep your core engaged throughout the movement''',
            'tracking_points': '["left_shoulder", "left_elbow", "left_wrist", "right_shoulder", "right_elbow", "right_wrist"]'
        },
        {
            'name': 'Pull-up',
            'description': 'A compound exercise that primarily targets your back and biceps muscles.',
            'instructions': '''1. Grip the pull-up bar with hands slightly wider than shoulder-width
2. Hang with arms fully extended (dead hang)
3. Pull yourself up until your chin is over the bar
4. Keep your core engaged and legs still
5. Lower yourself back down with control
6. Repeat while maintaining proper form''',
            'tracking_points': '["left_shoulder", "left_elbow", "left_wrist", "right_shoulder", "right_elbow", "right_wrist", "left_hip", "right_hip"]'
        },
        {
            'name': 'Push-up',
            'description': 'A fundamental bodyweight exercise that works your chest, shoulders, and triceps.',
            'instructions': '''1. Start in a plank position with hands slightly wider than shoulders
2. Keep your body in a straight line from head to heels
3. Lower your body until your chest nearly touches the ground
4. Keep your elbows at a 45-degree angle to your body
5. Push back up to the starting position
6. Maintain core engagement throughout''',
            'tracking_points': '["left_shoulder", "left_elbow", "left_wrist", "right_shoulder", "right_elbow", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee"]'
        }
    ]

    for exercise_data in exercises:
        exercise = Exercise(**exercise_data)
        db.session.add(exercise)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_exercises()  # Initialize exercises
    socketio.run(app, host='0.0.0.0', port=10000, debug=True, allow_unsafe_werkzeug=True)
