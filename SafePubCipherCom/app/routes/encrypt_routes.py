"""
CipherVault Pro — Encryption / Decryption Routes
"""

import os
import base64
import io
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, send_file, current_app, session,
)
from flask_login import login_required, current_user
from app import db
from app.models.vault import VaultFile, EncryptionLog
from app.utils.crypto import encrypt_data, decrypt_data, encrypt_b64, decrypt_b64, ALGORITHMS
from app.utils.forms import EncryptTextForm, DecryptTextForm, EncryptFileForm, DecryptFileForm
from app.utils.helpers import save_bytes, save_upload, read_file, delete_file, human_size, utcnow

encrypt_bp = Blueprint("encrypt", __name__)


def _log(operation: str, algorithm: str = None, file_name: str = None,
         file_size: int = None, success: bool = True, error: str = None):
    log = EncryptionLog(
        user_id=current_user.id,
        operation=operation,
        algorithm=algorithm,
        file_name=file_name,
        file_size=file_size,
        success=success,
        error_message=error,
    )
    db.session.add(log)
    db.session.commit()


# ---------------------------------------------------------------------------
# Text encryption
# ---------------------------------------------------------------------------

@encrypt_bp.route("/text", methods=["GET", "POST"])
@login_required
def encrypt_text():
    form = EncryptTextForm()
    result_b64 = None

    if form.validate_on_submit():
        try:
            plaintext = form.plaintext.data.encode("utf-8")
            encrypted = encrypt_data(plaintext, form.passphrase.data, form.algorithm.data)
            result_b64 = base64.b64encode(encrypted).decode("ascii")
            _log("encrypt", form.algorithm.data, file_name="text_input", file_size=len(plaintext))

            if form.save_to_vault.data:
                stored, path = save_bytes(
                    encrypted,
                    current_app.config["VAULT_FOLDER"],
                    ext="enc",
                )
                vf = VaultFile(
                    user_id=current_user.id,
                    original_name="text_input.enc",
                    stored_name=stored,
                    file_size=len(encrypted),
                    file_type="text/plain",
                    algorithm=form.algorithm.data,
                    description=form.vault_description.data or None,
                )
                db.session.add(vf)
                db.session.commit()
                flash("Saved to Vault.", "success")

            flash("Text encrypted successfully.", "success")
        except Exception as exc:
            _log("encrypt", form.algorithm.data, success=False, error=str(exc))
            flash(f"Encryption failed: {exc}", "danger")

    return render_template(
        "encrypt/encrypt_text.html",
        form=form,
        result_b64=result_b64,
        title="Encrypt Text",
        algorithms=list(ALGORITHMS.keys()),
    )


@encrypt_bp.route("/text/decrypt", methods=["GET", "POST"])
@login_required
def decrypt_text():
    form = DecryptTextForm()
    result_text = None

    if form.validate_on_submit():
        try:
            raw = base64.b64decode(form.ciphertext_b64.data.strip())
            plaintext = decrypt_data(raw, form.passphrase.data, form.algorithm.data)
            result_text = plaintext.decode("utf-8", errors="replace")
            _log("decrypt", form.algorithm.data, file_name="text_input", file_size=len(raw))
            flash("Decrypted successfully.", "success")
        except Exception as exc:
            _log("decrypt", form.algorithm.data, success=False, error=str(exc))
            flash(f"Decryption failed: {exc}", "danger")

    return render_template(
        "encrypt/decrypt_text.html",
        form=form,
        result_text=result_text,
        title="Decrypt Text",
    )


# ---------------------------------------------------------------------------
# File encryption
# ---------------------------------------------------------------------------

@encrypt_bp.route("/file", methods=["GET", "POST"])
@login_required
def encrypt_file():
    form = EncryptFileForm()

    if form.validate_on_submit():
        try:
            file_data = form.file.data.read()
            original_name = form.file.data.filename
            encrypted = encrypt_data(file_data, form.passphrase.data, form.algorithm.data)

            _log("encrypt", form.algorithm.data, file_name=original_name, file_size=len(file_data))

            if form.save_to_vault.data:
                stored, path = save_bytes(
                    encrypted, current_app.config["VAULT_FOLDER"], ext="enc"
                )
                vf = VaultFile(
                    user_id=current_user.id,
                    original_name=original_name + ".enc",
                    stored_name=stored,
                    file_size=len(encrypted),
                    file_type="application/octet-stream",
                    algorithm=form.algorithm.data,
                    description=form.vault_description.data or None,
                )
                db.session.add(vf)
                db.session.commit()
                flash("Encrypted and saved to Vault.", "success")
                return redirect(url_for("vault.index"))

            # Otherwise send as download
            return send_file(
                io.BytesIO(encrypted),
                as_attachment=True,
                download_name=original_name + ".enc",
                mimetype="application/octet-stream",
            )
        except Exception as exc:
            _log("encrypt", form.algorithm.data, success=False, error=str(exc))
            flash(f"Encryption failed: {exc}", "danger")

    return render_template(
        "encrypt/encrypt_file.html",
        form=form,
        title="Encrypt File",
    )


@encrypt_bp.route("/file/decrypt", methods=["GET", "POST"])
@login_required
def decrypt_file():
    form = DecryptFileForm()

    if form.validate_on_submit():
        try:
            enc_data = form.file.data.read()
            original_name = form.file.data.filename.removesuffix(".enc")
            plaintext = decrypt_data(enc_data, form.passphrase.data, form.algorithm.data)
            _log("decrypt", form.algorithm.data, file_name=original_name, file_size=len(enc_data))
            flash("File decrypted successfully.", "success")
            return send_file(
                io.BytesIO(plaintext),
                as_attachment=True,
                download_name=original_name or "decrypted_file",
                mimetype="application/octet-stream",
            )
        except Exception as exc:
            _log("decrypt", form.algorithm.data, success=False, error=str(exc))
            flash(f"Decryption failed: {exc}", "danger")

    return render_template(
        "encrypt/decrypt_file.html",
        form=form,
        title="Decrypt File",
    )
