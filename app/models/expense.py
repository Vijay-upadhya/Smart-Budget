from app import db
from datetime import datetime


class Expense(db.Model):
    __tablename__ = 'expenses'

    id         = db.Column(db.Integer, primary_key=True)
    category   = db.Column(db.String(100), nullable=False)
    amount     = db.Column(db.Float, nullable=False)
    currency   = db.Column(db.String(10), nullable=False, default='INR')
    date       = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    note       = db.Column(db.String(255), nullable=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':       self.id,
            'category': self.category,
            'amount':   self.amount,
            'currency': self.currency,
            'date':     self.date.strftime('%Y-%m-%d'),
            'note':     self.note or '',
        }

    def __repr__(self):
        return f'<Expense {self.category} {self.amount} {self.currency}>'
