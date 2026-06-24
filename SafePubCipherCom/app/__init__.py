"""
CipherVault Pro — Application Factory
Initialises Flask extensions and registers all blueprints.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from config.config import config_map

# ---------------------------------------------------------------------------
# Extension singletons (bound to app later via init_app)
# ---------------------------------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
migrate = Migrate()


def create_app(config_name: str = "default") -> Flask:
    """Create and configure the Flask application."""

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Load configuration
    app.config.from_object(config_map[config_name])

    # Ensure required directories exist
    for folder in [app.config["UPLOAD_FOLDER"], app.config["VAULT_FOLDER"]]:
        os.makedirs(folder, exist_ok=True)

    # Bind extensions
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access CipherVault Pro."
    login_manager.login_message_category = "warning"

    # User loader
    from app.models.user import User  # noqa: F401 — needed for relationship resolution

    @login_manager.user_loader
    def load_user(user_id: int):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.main_routes import main_bp
    from app.routes.encrypt_routes import encrypt_bp
    from app.routes.stego_routes import stego_bp
    from app.routes.vault_routes import vault_bp
    from app.routes.message_routes import message_bp
    from app.routes.trainer_routes import trainer_bp
    from app.routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(encrypt_bp, url_prefix="/encrypt")
    app.register_blueprint(stego_bp, url_prefix="/stego")
    app.register_blueprint(vault_bp, url_prefix="/vault")
    app.register_blueprint(message_bp, url_prefix="/messages")
    app.register_blueprint(trainer_bp, url_prefix="/trainer")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")

    # Register error handlers
    _register_error_handlers(app)

    # Create tables if they don't exist (dev convenience)
    with app.app_context():
        db.create_all()

    return app


def _register_error_handlers(app: Flask) -> None:
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500
