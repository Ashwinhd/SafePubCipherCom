"""
CipherVault Pro — Main / Dashboard Routes
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models.vault import VaultFile, EncryptionLog, SelfDestructMessage, TypingScore

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/index.html", title="CipherVault Pro")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    uid = current_user.id

    # Aggregated stats
    total_enc = EncryptionLog.query.filter_by(user_id=uid, operation="encrypt").count()
    total_dec = EncryptionLog.query.filter_by(user_id=uid, operation="decrypt").count()
    vault_count = VaultFile.query.filter_by(user_id=uid).count()
    active_messages = SelfDestructMessage.query.filter_by(
        user_id=uid, is_destroyed=False
    ).count()

    # Most used algorithm
    algo_row = (
        EncryptionLog.query
        .filter_by(user_id=uid)
        .filter(EncryptionLog.algorithm.isnot(None))
        .with_entities(EncryptionLog.algorithm, func.count(EncryptionLog.id).label("cnt"))
        .group_by(EncryptionLog.algorithm)
        .order_by(func.count(EncryptionLog.id).desc())
        .first()
    )
    top_algo = algo_row.algorithm if algo_row else "—"

    # Best typing score
    best_score = (
        TypingScore.query
        .filter_by(user_id=uid)
        .order_by(TypingScore.wpm.desc())
        .first()
    )

    # Recent activity (last 5)
    recent = (
        EncryptionLog.query
        .filter_by(user_id=uid)
        .order_by(EncryptionLog.created_at.desc())
        .limit(5)
        .all()
    )

    # Recent vault files
    recent_files = (
        VaultFile.query
        .filter_by(user_id=uid)
        .order_by(VaultFile.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "main/dashboard.html",
        title="Dashboard",
        total_enc=total_enc,
        total_dec=total_dec,
        vault_count=vault_count,
        active_messages=active_messages,
        top_algo=top_algo,
        best_score=best_score,
        recent=recent,
        recent_files=recent_files,
    )
