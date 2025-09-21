# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_socketio import SocketIO

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
migrate = Migrate()
socketio = SocketIO()
