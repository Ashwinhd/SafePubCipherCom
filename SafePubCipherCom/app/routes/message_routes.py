"""
CipherVault Pro — Self-Destruct Message Routes
Messages encrypt content, set expiry / read limits, and auto-delete after access.
"""

import uuid
from datetime import timezone
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app,
)
from flask_login import login_required, current_user
from app import db
from app.models.vault import SelfDestructMessage
from app.utils.forms import CreateMessageForm, ReadMessageForm
from app.utils.crypto import encrypt_b64, decrypt_b64
from app.utils.helpers import utcnow, time_until
from datetime import timedelta

message_bp = Blueprint("messages", __name__)


@message_bp.route("/")
@login_required
def index():
    msgs = (
        SelfDestructMessage.query
        .filter_by(user_id=current_user.id)
        .order_by(SelfDestructMessage.created_at.desc())
        .all()
    )
    return render_template("messages/index.html", title="Self-Destruct Messages", messages=msgs, time_until=time_until)


@message_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = CreateMessageForm()
    share_url = None

    if form.validate_on_submit():
        try:
            # Encrypt content with user-supplied passphrase
            encrypted = encrypt_b64(
                form.content.data.encode("utf-8"),
                form.passphrase.data,
                form.algorithm.data,
            )

            expires_at = None
            if form.expires_hours.data and form.expires_hours.data > 0:
                expires_at = utcnow() + timedelta(hours=form.expires_hours.data)

            token = uuid.uuid4().hex + uuid.uuid4().hex  # 64-char token

            msg = SelfDestructMessage(
                user_id=current_user.id,
                token=token,
                encrypted_content=encrypted,
                algorithm=form.algorithm.data,
                title=form.title.data.strip() if form.title.data else None,
                max_reads=form.max_reads.data,
                expires_at=expires_at,
            )
            db.session.add(msg)
            db.session.commit()

            share_url = url_for("messages.read", token=token, _external=True)
            flash("Message created. Share the link below.", "success")
        except Exception as exc:
            flash(f"Failed to create message: {exc}", "danger")

    return render_template(
        "messages/create.html",
        title="Create Self-Destruct Message",
        form=form,
        share_url=share_url,
    )


@message_bp.route("/read/<token>", methods=["GET", "POST"])
def read(token: str):
    msg = SelfDestructMessage.query.filter_by(token=token).first_or_404()
    form = ReadMessageForm()
    content = None

    if not msg.is_available:
        reason = "destroyed" if msg.is_destroyed else ("expired" if msg.is_expired else "read limit reached")
        return render_template("messages/destroyed.html", title="Message Unavailable", reason=reason)

    if form.validate_on_submit():
        try:
            plaintext = decrypt_b64(msg.encrypted_content, form.passphrase.data, msg.algorithm)
            content = plaintext.decode("utf-8", errors="replace")

            # Increment reads and potentially destroy
            msg.read_count += 1
            if msg.max_reads > 0 and msg.read_count >= msg.max_reads:
                msg.is_destroyed = True
                msg.destroyed_at = utcnow()
            db.session.commit()
        except Exception as exc:
            flash(f"Decryption failed — wrong passphrase? ({exc})", "danger")

    return render_template(
        "messages/read.html",
        title=msg.title or "Secret Message",
        msg=msg,
        form=form,
        content=content,
        time_until=time_until,
    )


@message_bp.route("/delete/<int:msg_id>", methods=["POST"])
@login_required
def delete(msg_id: int):
    msg = SelfDestructMessage.query.filter_by(id=msg_id, user_id=current_user.id).first_or_404()
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted.", "success")
    return redirect(url_for("messages.index"))
