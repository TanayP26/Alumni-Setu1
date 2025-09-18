# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 16:57:52 2025

@author: Admin
"""
# app.py

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from flask_migrate import Migrate
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
migrate = Migrate()

def create_app(config_name='development'):
    app = Flask(__name__)

    # Core config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_url = os.getenv('DATABASE_URL', 'sqlite:///alumni_management.db')
    if db_url.startswith('sqlite:///'):
        rel_path = db_url.replace('sqlite:///', '', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, rel_path)
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

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Create database tables if not exist
    with app.app_context():
        db.create_all()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.alumni import alumni_bp
    from routes.events import events_bp
    from routes.jobs import jobs_bp
    from routes.messages import messages_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(alumni_bp, url_prefix='/api/alumni')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

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

    @app.route('/mentorship/find-mentor')
    def find_mentor_page():
        return render_template('find_mentor.html')

    @app.route('/mentorship/become-mentor')
    def become_mentor_page():
        return render_template('become_mentor.html')

    @app.route('/mentorship/matches')
    def mentor_matches_page():
        return render_template('mentor_matches.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
