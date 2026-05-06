import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Core ────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mycollegeproject2024smartbudgetflask'

    # ── Database ─────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'budget.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Google OAuth ─────────────────────────────────────
    # Replace these values with your own credentials or set environment variables.
    GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID') or 'YOUR_GOOGLE_CLIENT_ID'
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or 'YOUR_GOOGLE_CLIENT_SECRET'
