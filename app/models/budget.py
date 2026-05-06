from app import db
from datetime import datetime


class Budget(db.Model):
    __tablename__ = 'budgets'

    id         = db.Column(db.Integer, primary_key=True)
    amount     = db.Column(db.Float, nullable=False)
    month      = db.Column(db.Integer, nullable=False)
    year       = db.Column(db.Integer, nullable=False)
    currency   = db.Column(db.String(10), nullable=False, default='INR')
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Budget {self.amount} {self.currency} {self.month}/{self.year}>'
