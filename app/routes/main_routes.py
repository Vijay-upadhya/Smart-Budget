import csv
import io
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense
from app.models.budget import Budget
from app.services.budget_service import (
    get_current_budget,
    get_total_expenses,
    get_category_breakdown,
    get_monthly_expenses,
    get_comparison_data,
)

main_bp = Blueprint('main', __name__)

CATEGORIES = [
    'Food & Dining', 'Transport', 'Shopping', 'Entertainment',
    'Health & Medical', 'Utilities', 'Education', 'Travel',
    'Rent & Housing', 'Subscriptions', 'Personal Care', 'Other',
]

CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'JPY', 'AED']


def safe_eval(expr):
    """Safely evaluate a simple arithmetic expression like 200+300*2."""
    try:
        expr = str(expr).strip()
        if not all(c in '0123456789 +-*/.() ' for c in expr):
            return None
        result = eval(expr, {"__builtins__": {}}, {})
        return float(result)
    except Exception:
        return None


# ─── Dashboard ────────────────────────────────────────────────────────────────

@main_bp.route('/dashboard')
@login_required
def dashboard():
    now = datetime.utcnow()
    budget         = get_current_budget(current_user.id)
    total_expenses = get_total_expenses(current_user.id)
    budget_amount  = budget.amount if budget else 0.0
    remaining      = budget_amount - total_expenses
    pct_used       = min((total_expenses / budget_amount * 100), 100) if budget_amount > 0 else 0

    category_data  = get_category_breakdown(current_user.id)
    monthly_data   = get_monthly_expenses(current_user.id)

    recent_expenses = (
        Expense.query
        .filter_by(user_id=current_user.id)
        .order_by(Expense.date.desc(), Expense.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        'dashboard.html',
        budget         = budget,
        budget_amount  = budget_amount,
        total_expenses = total_expenses,
        remaining      = remaining,
        pct_used       = pct_used,
        category_data  = category_data,
        monthly_data   = monthly_data,
        recent_expenses= recent_expenses,
        categories     = CATEGORIES,
        currencies     = CURRENCIES,
        today          = date.today().isoformat(),
        current_month  = now.strftime('%B %Y'),
    )


# ─── Add Expense ──────────────────────────────────────────────────────────────

@main_bp.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    category  = request.form.get('category', '').strip()
    amount_str= request.form.get('amount', '').strip()
    currency  = request.form.get('currency', 'INR').strip()
    date_str  = request.form.get('date', '').strip()
    note      = request.form.get('note', '').strip()

    if not category or not amount_str or not date_str:
        flash('Category, amount, and date are required.', 'error')
        return redirect(url_for('main.dashboard'))

    amount = safe_eval(amount_str)
    if amount is None or amount <= 0:
        flash('Invalid amount. Enter a number or expression like 200+50.', 'error')
        return redirect(url_for('main.dashboard'))

    try:
        expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date.', 'error')
        return redirect(url_for('main.dashboard'))

    db.session.add(Expense(
        category = category,
        amount   = round(amount, 2),
        currency = currency,
        date     = expense_date,
        note     = note or None,
        user_id  = current_user.id,
    ))
    db.session.commit()
    flash(f'Expense of {currency} {amount:.2f} added! ✅', 'success')
    return redirect(url_for('main.dashboard'))


# ─── Delete Expense ───────────────────────────────────────────────────────────

@main_bp.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(request.referrer or url_for('main.dashboard'))


# ─── Set / Update Budget ──────────────────────────────────────────────────────

@main_bp.route('/set_budget', methods=['POST'])
@login_required
def set_budget():
    amount_str = request.form.get('budget_amount', '').strip()
    currency   = request.form.get('budget_currency', 'INR').strip()

    amount = safe_eval(amount_str)
    if amount is None or amount <= 0:
        flash('Invalid budget amount.', 'error')
        return redirect(url_for('main.dashboard'))

    now    = datetime.utcnow()
    budget = Budget.query.filter_by(
        user_id=current_user.id, month=now.month, year=now.year
    ).first()

    if budget:
        budget.amount   = round(amount, 2)
        budget.currency = currency
        flash('Budget updated! ✅', 'success')
    else:
        db.session.add(Budget(
            amount  = round(amount, 2),
            currency= currency,
            month   = now.month,
            year    = now.year,
            user_id = current_user.id,
        ))
        flash('Budget set! ✅', 'success')

    db.session.commit()
    return redirect(url_for('main.dashboard'))


# ─── Comparison ───────────────────────────────────────────────────────────────

@main_bp.route('/comparison')
@login_required
def comparison():
    data = get_comparison_data(current_user.id)
    return render_template('comparison.html', comparison=data)


# ─── Export CSV ───────────────────────────────────────────────────────────────

@main_bp.route('/export')
@login_required
def export():
    expenses = (
        Expense.query
        .filter_by(user_id=current_user.id)
        .order_by(Expense.date.desc())
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#', 'Category', 'Amount', 'Currency', 'Date', 'Note'])
    for e in expenses:
        writer.writerow([e.id, e.category, e.amount, e.currency,
                         e.date.strftime('%Y-%m-%d'), e.note or ''])
    output.seek(0)
    fname = f"smart_budget_{current_user.username}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={fname}'},
    )
