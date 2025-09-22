# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 16:57:52 2025
@author: Admin
"""
import os
from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta

# Import the already instantiated extensions
from extensions import db, jwt, mail, migrate, socketio

load_dotenv()

# Import blueprints
from routes.auth import auth_bp
from routes.alumni import alumni_bp
from routes.events import events_bp
from routes.jobs import jobs_bp
from routes.admin import admin_bp
from routes.messaging import messaging_bp


def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    from flask import send_file

    @app.route('/download-db')
    def download_db():
        return send_file('alumni_management.db', as_attachment=True)


    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    db_url = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "alumni_management.db")}')
    if db_url.startswith('sqlite:///'):
        rel = db_url.replace('sqlite:///', '', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, rel)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')

    # Initialize extensions with the app instance
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Create tables within app context
    with app.app_context():
        db.create_all()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(alumni_bp, url_prefix='/api/alumni')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(messaging_bp, url_prefix='/api/messaging')

    @app.route('/debug/users')
def debug_users():
    users = User.query.all()
    user_list = [u.to_dict(include_sensitive=True) for u in users]
    return jsonify(user_list)

    # Frontend routes
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/jobs')
    def jobs_page():
        return render_template('jobs.html')

    @app.route('/alumni')
    def alumni_page():
        return render_template('alumni.html')

    @app.route('/messaging')
    def messaging_page():
        return render_template('messaging.html')

    @app.route('/events')
    def events_page():
        return render_template('events.html')

    @app.route('/profile')
    def profile_page():
        return render_template('profile.html')

    # Mentorship routes
    @app.route('/mentorship')
    def mentorship_page():
        return render_template('mentorship.html')

    @app.route('/mentorship/find')
    def find_mentor_page():
        return render_template('find_mentor.html')

    @app.route('/mentorship/become')
    def become_mentor_page():
        return render_template('become_mentor.html')

    @app.route('/mentorship/matches')
    def mentor_matches():
        return render_template('mentor_matches.html')

    return app


if __name__ == "__main__":
    # Run with socketio to enable real-time functionality
    socketio.run(create_app(), host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))



