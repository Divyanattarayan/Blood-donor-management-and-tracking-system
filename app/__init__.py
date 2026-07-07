from flask import Flask
from app.config import config


def create_app(config_name='default'):
    app = Flask(__name__, static_folder='../static')
    app.config.from_object(config[config_name])

    # ── Register Blueprints ──────────────────────────────────
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.donors.routes import donors_bp
    from app.donations.routes import donations_bp
    from app.requests.routes import requests_bp
    from app.reports.routes import reports_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(donors_bp,    url_prefix='/donors')
    app.register_blueprint(donations_bp, url_prefix='/donations')
    app.register_blueprint(requests_bp,  url_prefix='/requests')
    app.register_blueprint(reports_bp,   url_prefix='/reports')
    app.register_blueprint(admin_bp,     url_prefix='/admin')

    # ── Root redirect ────────────────────────────────────────
    from flask import render_template
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
