"""
CipherVault Pro — Steganography Routes
Hide encrypted data inside images and extract it back.
"""

import io
import base64
from flask import (
    Blueprint, render_template, flash, send_file, current_app,
)
from flask_login import login_required, current_user
from app import db
from app.models.vault import EncryptionLog, VaultFile
from app.utils.stego import lsb_embed, lsb_extract, image_capacity_info
from app.utils.crypto import encrypt_data, decrypt_data
from app.utils.forms import StegoHideForm, StegoExtractForm
from app.utils.helpers import save_bytes, utcnow

stego_bp = Blueprint("stego", __name__)


def _log(op, algo=None, fname=None, fsize=None, success=True, error=None):
    log = EncryptionLog(
        user_id=current_user.id,
        operation=op,
        algorithm=algo,
        file_name=fname,
        file_size=fsize,
        success=success,
        error_message=error,
    )
    db.session.add(log)
    db.session.commit()


@stego_bp.route("/hide", methods=["GET", "POST"])
@login_required
def hide():
    form = StegoHideForm()
    capacity_info = None

    if form.validate_on_submit():
        try:
            image_bytes = form.image.data.read()
            img_name = form.image.data.filename
            cap = image_capacity_info(image_bytes)
            capacity_info = cap

            # Gather secret payload
            if form.secret_file.data and form.secret_file.data.filename:
                secret_bytes = form.secret_file.data.read()
            elif form.secret_text.data:
                secret_bytes = form.secret_text.data.encode("utf-8")
            else:
                flash("Please provide secret text or a secret file.", "warning")
                return render_template("stego/hide.html", form=form, title="Hide Secret", capacity_info=capacity_info)

            # Encrypt the secret
            encrypted = encrypt_data(secret_bytes, form.passphrase.data, form.algorithm.data)

            if len(encrypted) > cap["lsb_capacity_bytes"]:
                flash(
                    f"Secret too large: {len(encrypted)} bytes encrypted, "
                    f"image capacity is {cap['lsb_capacity_bytes']} bytes. "
                    "Use a larger image or shorter message.",
                    "danger",
                )
                return render_template("stego/hide.html", form=form, title="Hide Secret", capacity_info=capacity_info)

            # Embed
            stego_bytes = lsb_embed(image_bytes, encrypted)
            _log("stego_hide", form.algorithm.data, fname=img_name, fsize=len(image_bytes))

            return send_file(
                io.BytesIO(stego_bytes),
                as_attachment=True,
                download_name="stego_" + img_name.rsplit(".", 1)[0] + ".png",
                mimetype="image/png",
            )
        except Exception as exc:
            _log("stego_hide", form.algorithm.data, success=False, error=str(exc))
            flash(f"Steganography failed: {exc}", "danger")

    return render_template("stego/hide.html", form=form, title="Hide Secret", capacity_info=capacity_info)


@stego_bp.route("/extract", methods=["GET", "POST"])
@login_required
def extract():
    form = StegoExtractForm()
    result_text = None
    result_b64 = None

    if form.validate_on_submit():
        try:
            image_bytes = form.image.data.read()

            # Extract LSB payload (encrypted bytes)
            encrypted = lsb_extract(image_bytes)

            # Decrypt
            plaintext = decrypt_data(encrypted, form.passphrase.data, form.algorithm.data)
            _log("stego_extract", form.algorithm.data, fname=form.image.data.filename, fsize=len(image_bytes))

            # Try to display as text; fall back to base64
            try:
                result_text = plaintext.decode("utf-8")
            except UnicodeDecodeError:
                result_b64 = base64.b64encode(plaintext).decode("ascii")
                result_text = None

            flash("Secret extracted and decrypted successfully.", "success")
        except Exception as exc:
            _log("stego_extract", form.algorithm.data, success=False, error=str(exc))
            flash(f"Extraction failed: {exc}", "danger")

    return render_template(
        "stego/extract.html",
        form=form,
        title="Extract Secret",
        result_text=result_text,
        result_b64=result_b64,
    )


@stego_bp.route("/capacity", methods=["POST"])
@login_required
def capacity():
    """AJAX endpoint — returns image capacity JSON."""
    from flask import request, jsonify
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "No image provided"}), 400
    try:
        info = image_capacity_info(file.read())
        return jsonify(info)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
