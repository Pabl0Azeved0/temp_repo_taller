import os
from flask import Flask
from src.models import db
from src.routes import bp


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        database_url = os.environ.get("DATABASE_URL", "sqlite:///minivenmo.db")
        app.config.from_mapping(
            SQLALCHEMY_DATABASE_URI=database_url, SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
    else:
        app.config.from_mapping(test_config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(bp, url_prefix="/api")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
