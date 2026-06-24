"""
CipherVault Pro — Analytics Routes
Provides data for charts and usage dashboards.
"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from app.models.vault import EncryptionLog, TypingScore
from app import db

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/")
@login_required
def index():
    uid = current_user.id

    # Algorithm usage distribution
    algo_data = (
        db.session.query(EncryptionLog.algorithm, func.count(EncryptionLog.id))
        .filter_by(user_id=uid)
        .filter(EncryptionLog.algorithm.isnot(None))
        .group_by(EncryptionLog.algorithm)
        .all()
    )
    algo_labels = [r[0] for r in algo_data]
    algo_counts = [r[1] for r in algo_data]

    # Operation breakdown
    op_data = (
        db.session.query(EncryptionLog.operation, func.count(EncryptionLog.id))
        .filter_by(user_id=uid)
        .group_by(EncryptionLog.operation)
        .all()
    )
    op_labels = [r[0] for r in op_data]
    op_counts = [r[1] for r in op_data]

    # Last 7 days activity (daily encrypt count)
    from datetime import timedelta
    from app.utils.helpers import utcnow
    now = utcnow()
    daily_labels = []
    daily_counts = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%b %d")
        count = (
            EncryptionLog.query
            .filter_by(user_id=uid)
            .filter(func.date(EncryptionLog.created_at) == day.date())
            .count()
        )
        daily_labels.append(day_str)
        daily_counts.append(count)

    # Typing WPM over time (last 20 sessions)
    typing_sessions = (
        TypingScore.query
        .filter_by(user_id=uid)
        .order_by(TypingScore.created_at.asc())
        .limit(20)
        .all()
    )
    typing_labels = [s.created_at.strftime("%b %d %H:%M") for s in typing_sessions]
    typing_wpm = [round(s.wpm, 1) for s in typing_sessions]
    typing_acc = [round(s.accuracy, 1) for s in typing_sessions]

    # Success vs failure
    success_count = EncryptionLog.query.filter_by(user_id=uid, success=True).count()
    fail_count = EncryptionLog.query.filter_by(user_id=uid, success=False).count()

    return render_template(
        "analytics/index.html",
        title="Analytics",
        algo_labels=algo_labels,
        algo_counts=algo_counts,
        op_labels=op_labels,
        op_counts=op_counts,
        daily_labels=daily_labels,
        daily_counts=daily_counts,
        typing_labels=typing_labels,
        typing_wpm=typing_wpm,
        typing_acc=typing_acc,
        success_count=success_count,
        fail_count=fail_count,
    )


@analytics_bp.route("/api/activity")
@login_required
def api_activity():
    """JSON endpoint for live chart refresh."""
    uid = current_user.id
    from app.utils.helpers import utcnow
    from datetime import timedelta
    now = utcnow()
    result = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        count = (
            EncryptionLog.query
            .filter_by(user_id=uid)
            .filter(func.date(EncryptionLog.created_at) == day.date())
            .count()
        )
        result.append({"date": day.strftime("%b %d"), "count": count})
    return jsonify(result)
