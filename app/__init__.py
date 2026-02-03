from flask import Flask

from .db import init_db
from .routes import bp


def create_app(testing: bool = False) -> Flask:
    """
    Application factory.
    Creates and configures the Flask app.
    """
    app = Flask(__name__)

    # Config
    app.config["TESTING"] = testing

    # Initialize database (safe to call multiple times)
    init_db()

    # Register routes
    app.register_blueprint(bp)

    return app
