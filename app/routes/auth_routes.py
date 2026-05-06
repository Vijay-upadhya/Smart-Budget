import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, oauth
from app.models.user import User

auth_bp = Blueprint('auth', __name__)


# ─── Index redirect ───────────────────────────────────────────────────────────

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


# ─── Register ─────────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not email or not username or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
            return render_template('register.html')

        user = User(email=email, username=username, auth_method='local')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ─── Login ────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}! 👋', 'success')
            return redirect(next_page or url_for('main.dashboard'))

        flash('Invalid email or password. Please try again.', 'error')

    return render_template('login.html')


# ─── Logout ───────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ─── Google OAuth — Initiate ──────────────────────────────────────────────────

@auth_bp.route('/login/google')
def google_login():
    """Redirect the user to Google's OAuth consent screen."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


# ─── Google OAuth — Callback ──────────────────────────────────────────────────

@auth_bp.route('/login/google/callback')
def google_callback():
    """Handle the response from Google after the user grants permission."""
    try:
        token    = oauth.google.authorize_access_token()
        userinfo = token.get('userinfo') or oauth.google.userinfo()
    except Exception as e:
        flash('Google sign-in failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

    email     = userinfo.get('email', '').lower()
    name      = userinfo.get('name') or email.split('@')[0]
    google_id = userinfo.get('sub')
    avatar    = userinfo.get('picture')

    if not email:
        flash('Could not retrieve email from Google. Please try again.', 'error')
        return redirect(url_for('auth.login'))

    # Check by google_id first, then by email
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()

    if user:
        # Update Google metadata if this was a local account logging in via Google
        if not user.google_id:
            user.google_id   = google_id
            user.avatar_url  = avatar
            user.auth_method = 'google'
            db.session.commit()
    else:
        # Brand new user via Google
        user = User(
            email       = email,
            username    = name,
            google_id   = google_id,
            avatar_url  = avatar,
            auth_method = 'google',
        )
        # Set a random unusable password so the account is valid
        user.set_password(os.urandom(24).hex())
        db.session.add(user)
        db.session.commit()

    login_user(user, remember=True)
    flash(f'Welcome, {user.username}! Signed in with Google. 🎉', 'success')
    return redirect(url_for('main.dashboard'))
