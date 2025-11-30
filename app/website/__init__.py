from flask import Flask, Blueprint, render_template, request, session, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jesusislord'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
mail = Mail()

def create_app():
    print(__name__)
    
    # Set app configuration data
    # app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    db.init_app(app)
    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    mail.init_app(app)

    from ..website.views import mainbp
    from ..website.auth import authbp
    app.register_blueprint(mainbp)
    app.register_blueprint(authbp)

    login_manager = LoginManager()
    login_manager.login_view = 'authentication.login'
    login_manager.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialise bootstrap
    bootstrap = Bootstrap(app)

    from .models import Events

    with app.app_context():
        db.create_all()

    # @app.before_first_request
    # def create_tables():
        # db.create_all()

    return app

