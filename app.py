import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, login_required, logout_user, LoginManager, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from game_manager import GameManager
from sqlalchemy import case


app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5000"])

# Configure the application
def configure_app(app):
    load_dotenv()
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # secrets.token_hex(16)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'game.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def initialize_database():
    with app.app_context():
        db.create_all()

def initialize_game_manager():
    return GameManager("C:\\dev\\coin_collector_project\\game\\coin_collector.py")

configure_app(app)
db = SQLAlchemy(app)
game_manager = initialize_game_manager()

# Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirects not authenticated users to the login page

# ORM models
class User(UserMixin, db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    result = db.Column(db.String(20), nullable=False)
    coins = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    play_time = db.Column(db.Integer)

    user = db.relationship('User', backref=db.backref('results', lazy=True))

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route("/")
@login_required
def index():
    game_active = game_manager.is_game_active   # Check if the game is active
    return render_template("index.html", user=current_user, game_active=game_active)

@app.route("/leaderboard")
@login_required
def global_leaderboard():
    # Global leaderboar: top 20 result among all the users
    results = Result.query.join(User).order_by(
        case({"won": 1, "lost": 2, "quit": 3}, value=Result.result), # first order by result
        case(
            (Result.result == 'won', Result.play_time), # for wins order by play time
            else_=-Result.coins # for defeat/quit order by descending coins
        ).asc(),
        Result.play_time.asc() # ascending play time if the rest is the same
    ).limit(20).all()
    
    return render_template('global_leaderboard.html', results=results)

@app.route("/my_stats")
@login_required
def user_leaderboard():
    user_results = Result.query.filter_by(user_id=current_user.id).order_by(
        case({"won": 1, "lost": 2, "quit": 3}, value=Result.result),
        case(
            (Result.result == 'won', Result.play_time),
            else_=-Result.coins
        ).asc(),
        Result.play_time.asc()
    ).limit(20).all()
    
    total_wins = Result.query.filter_by(user_id=current_user.id, result='won').count()
    total_coins = db.session.query(db.func.sum(Result.coins)).filter_by(user_id=current_user.id).scalar()
    
    return render_template('user_leaderboard.html', 
                         results=user_results,
                         total_wins=total_wins,
                         total_coins=total_coins)

@app.route("/submit_result", methods=["POST"])
def submit_result():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data received"}), 400

        result_value = data.get("result")
        coins = data.get("coins")
        play_time = data.get("play_time")

        if any(x is None for x in (result_value, coins, play_time)):
            return jsonify({"message": "Invalid data."}), 400

        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            return jsonify({"message": "User not authenticated"}), 401

        time = datetime.now(timezone.utc)
        new_result = Result(user_id=user_id, result=result_value, coins=coins, time=time, play_time=play_time)
        db.session.add(new_result)

        db.session.commit()
        return jsonify({'message': 'Result submitted successfully!'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("login.html", toastr_message="Username and password are required", toastr_type="error")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template("login.html", toastr_message="Invalid username or password", toastr_type="error")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validations
        if not all([username, password, confirmation]):
            return render_template("register.html", 
                                toastr_message="Fill all the fields",
                                toastr_type="error")

        if password != confirmation:
            return render_template("register.html",
                                toastr_message="Passwords do not match",
                                toastr_type="error")

        if User.query.filter_by(username=username).first():
            return render_template("register.html",
                                toastr_message="Username already exists",
                                toastr_type="error")

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))  # Redirect alla home
        except Exception as e:
            db.session.rollback()
            return render_template("register.html",
                                toastr_message=f"Errore: {str(e)}",
                                toastr_type="error")

    return render_template("register.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/start_game", methods=["GET", "POST"])
@login_required
def start_game():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    game_active = game_manager.is_game_active  # Check if the game is active
    if game_active:
        game_manager.cleanup() # close game
        success = True
        message = "Game closed successfully."
    else:
        session_cookie = request.cookies.get('session')
        success, message = game_manager.start_game(session_cookie)

    # Update game_active status
    game_active = game_manager.is_game_active
    return render_template('index.html', user=current_user, game_active=game_active, toastr_message=message, toastr_type='success' if success else 'error')

@app.route("/check_game_status")
@login_required
def check_game_status():
    return jsonify({"game_active": game_manager.is_game_active})

@app.route("/close_game", methods=["POST"])
@login_required
def close_game():
    game_manager.cleanup()
    return redirect(url_for('index'))
    
initialize_database()
