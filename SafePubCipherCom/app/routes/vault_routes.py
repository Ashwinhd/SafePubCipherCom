"""
CipherVault Pro — Vault Routes
Secure per-user file storage.
"""

import os
import io
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, send_file, current_app, abort,
)
from flask_login import login_required, current_user
from app import db
from app.models.vault import VaultFile
from app.utils.forms import VaultSearchForm
from app.utils.helpers import delete_file, read_file

vault_bp = Blueprint("vault", __name__)


@vault_bp.route("/")
@login_required
def index():
    form = VaultSearchForm(request.args, meta={"csrf": False})
    query = VaultFile.query.filter_by(user_id=current_user.id)

    if form.query.data:
        q = f"%{form.query.data}%"
        query = query.filter(
            VaultFile.original_name.ilike(q) | VaultFile.description.ilike(q)
        )

    page = request.args.get("page", 1, type=int)
    files = query.order_by(VaultFile.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )

    return render_template(
        "vault/index.html",
        title="My Vault",
        files=files,
        form=form,
    )


@vault_bp.route("/download/<int:file_id>")
@login_required
def download(file_id: int):
    vf = VaultFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    path = os.path.join(current_app.config["VAULT_FOLDER"], vf.stored_name)
    if not os.path.exists(path):
        flash("File not found on server.", "danger")
        return redirect(url_for("vault.index"))
    data = read_file(path)
    return send_file(
        io.BytesIO(data),
        as_attachment=True,
        download_name=vf.original_name,
        mimetype="application/octet-stream",
    )


@vault_bp.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete(file_id: int):
    vf = VaultFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    path = os.path.join(current_app.config["VAULT_FOLDER"], vf.stored_name)
    delete_file(path)
    db.session.delete(vf)
    db.session.commit()
    flash(f"'{vf.original_name}' deleted from vault.", "success")
    return redirect(url_for("vault.index"))


@vault_bp.route("/detail/<int:file_id>")
@login_required
def detail(file_id: int):
    vf = VaultFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    return render_template("vault/detail.html", title="File Details", vf=vf)
