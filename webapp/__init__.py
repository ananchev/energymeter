from flask import Flask, current_app

def create_app():
    app = Flask(__name__)

    # non-auth blueprint
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app