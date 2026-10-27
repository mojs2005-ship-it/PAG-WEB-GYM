"""Application entrypoint.

Legacy behaviour: app.py was a single monolithic file with every
route, the db connection, and startup code mixed together.

New behaviour: an application-factory (`create_app`) builds and wires
the app from independent pieces (config, database, blueprints), which
is what makes the app configurable (dev/testing/production) and
testable (pytest can build a fresh isolated app per test).
"""

import os

from flask import Flask

import database
from blueprints.api import api_bp
from blueprints.exercises import exercises_bp
from blueprints.main import main_bp
from blueprints.sessions import sessions_bp
from blueprints.sets import sets_bp
from config import DEFAULT_CONFIG_NAME, config_by_name


def create_app(config_name=None, test_config=None):
    app = Flask(__name__)

    if test_config is None:
        config_name = config_name or DEFAULT_CONFIG_NAME
        app.config.from_object(config_by_name[config_name])
    else:
        app.config.from_object(config_by_name["testing"])
        app.config.update(test_config)

    database.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(exercises_bp)
    app.register_blueprint(sets_bp)
    app.register_blueprint(api_bp)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
