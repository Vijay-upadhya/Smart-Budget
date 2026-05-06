from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    email        = db.Column(db.String(150), unique=True, nullable=False)
    username     = db.Column(db.String(100), nullable=False)
    password_hash= db.Column(db.String(256), nullable=True)   # nullable for OAuth users
    google_id    = db.Column(db.String(128), unique=True, nullable=True)
    avatar_url   = db.Column(db.String(512), nullable=True)   # Google profile picture
    auth_method  = db.Column(db.String(20), default='local')  # 'local' | 'google'

    expenses = db.relationship('Expense', backref='owner', lazy=True, cascade='all, delete-orphan')
    budgets  = db.relationship('Budget',  backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_google_user(self):
        return self.auth_method == 'google'

    def __repr__(self):
        return f'<User {self.email}>'
