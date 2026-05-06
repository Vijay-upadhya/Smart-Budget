import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance folder exists for SQLite
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)

    # Register Google OAuth provider
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.main_routes import main_bp
    from app.routes.history_routes import history_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(history_bp)

    # Create DB tables
    with app.app_context():
        db.create_all()

    return app
