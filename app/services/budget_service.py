from datetime import datetime
from collections import defaultdict
from app.models.expense import Expense
from app.models.budget import Budget


# ─── Budget helpers ───────────────────────────────────────────────────────────

def get_current_budget(user_id):
    """Return Budget for the current calendar month, or None."""
    now = datetime.utcnow()
    return Budget.query.filter_by(
        user_id=user_id,
        month=now.month,
        year=now.year
    ).first()


def get_total_expenses(user_id, month=None, year=None):
    """Sum all expense amounts for a user in the given month/year."""
    now = datetime.utcnow()
    month = month or now.month
    year  = year  or now.year

    total = 0.0
    for e in Expense.query.filter_by(user_id=user_id).all():
        if e.date.month == month and e.date.year == year:
            total += e.amount
    return total


# ─── Chart data ───────────────────────────────────────────────────────────────

def get_category_breakdown(user_id, month=None, year=None):
    """Return {category: total} dict for the pie/doughnut chart."""
    now = datetime.utcnow()
    month = month or now.month
    year  = year  or now.year

    breakdown = defaultdict(float)
    for e in Expense.query.filter_by(user_id=user_id).all():
        if e.date.month == month and e.date.year == year:
            breakdown[e.category] += e.amount
    return dict(breakdown)


def get_monthly_expenses(user_id, year=None):
    """Return list of 12 floats (Jan→Dec) for the bar chart."""
    year = year or datetime.utcnow().year
    monthly = [0.0] * 12
    for e in Expense.query.filter_by(user_id=user_id).all():
        if e.date.year == year:
            monthly[e.date.month - 1] += e.amount
    return monthly


# ─── Comparison ───────────────────────────────────────────────────────────────

def get_comparison_data(user_id):
    """Return dict with current vs previous month data for grouped bar chart."""
    now = datetime.utcnow()
    curr_month, curr_year = now.month, now.year

    if curr_month == 1:
        prev_month, prev_year = 12, curr_year - 1
    else:
        prev_month, prev_year = curr_month - 1, curr_year

    curr_bd = get_category_breakdown(user_id, curr_month, curr_year)
    prev_bd = get_category_breakdown(user_id, prev_month, prev_year)

    all_cats = sorted(set(list(curr_bd) + list(prev_bd)))
    month_names = ['Jan','Feb','Mar','Apr','May','Jun',
                   'Jul','Aug','Sep','Oct','Nov','Dec']

    return {
        'categories':     all_cats,
        'current':        [curr_bd.get(c, 0) for c in all_cats],
        'previous':       [prev_bd.get(c, 0) for c in all_cats],
        'current_label':  f"{month_names[curr_month - 1]} {curr_year}",
        'previous_label': f"{month_names[prev_month - 1]} {prev_year}",
        'current_total':  sum(curr_bd.values()),
        'previous_total': sum(prev_bd.values()),
    }


# ─── History ──────────────────────────────────────────────────────────────────

def get_expenses_grouped_by_date(user_id):
    """
    Return a list of dicts, one per day, sorted latest first.
    Each dict has: date, date_str, expenses, total, is_highest
    """
    all_expenses = (
        Expense.query
        .filter_by(user_id=user_id)
        .order_by(Expense.date.desc())
        .all()
    )

    grouped = defaultdict(list)
    for e in all_expenses:
        grouped[e.date].append(e)

    result = []
    for d in sorted(grouped.keys(), reverse=True):
        day_exps  = grouped[d]
        day_total = sum(e.amount for e in day_exps)
        result.append({
            'date':     d,
            'date_str': d.strftime('%A, %d %B %Y'),
            'expenses': day_exps,
            'total':    day_total,
        })

    # Mark the highest-spending day
    if result:
        max_total = max(g['total'] for g in result)
        for g in result:
            g['is_highest'] = (g['total'] == max_total and max_total > 0)

    return result
