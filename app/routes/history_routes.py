from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services.budget_service import get_expenses_grouped_by_date

history_bp = Blueprint('history', __name__)


@history_bp.route('/history')
@login_required
def history():
    grouped = get_expenses_grouped_by_date(current_user.id)
    return render_template('history.html', grouped_expenses=grouped)
