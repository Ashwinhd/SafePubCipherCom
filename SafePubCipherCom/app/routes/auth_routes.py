"""
CipherVault Pro — Authentication Routes
Handles register, login, logout, profile, and password reset.
"""

from datetime import datetime, timezone, timedelta
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models.user import User
from app.utils.forms import (
    RegistrationForm, LoginForm, ForgotPasswordForm,
    ResetPasswordForm, ProfileForm,
)
from app.utils.helpers import pick_avatar_colour, generate_token, utcnow

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        pw_hash = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            full_name=form.full_name.data.strip() if form.full_name.data else None,
            password_hash=pw_hash,
            avatar_color=pick_avatar_colour(form.username.data),
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form, title="Create Account")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash("Your account has been deactivated. Contact support.", "danger")
                return render_template("auth/login.html", form=form, title="Login")
            user.failed_logins = 0
            user.last_login = utcnow()
            db.session.commit()
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(next_page or url_for("main.dashboard"))
        else:
            if user:
                user.failed_logins = (user.failed_logins or 0) + 1
                db.session.commit()
            flash("Invalid username or password.", "danger")

    return render_template("auth/login.html", form=form, title="Log In")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Password change
        if form.current_password.data:
            if not bcrypt.check_password_hash(current_user.password_hash, form.current_password.data):
                flash("Current password is incorrect.", "danger")
                return render_template("auth/profile.html", form=form, title="Profile")
            if form.new_password.data:
                current_user.password_hash = bcrypt.generate_password_hash(
                    form.new_password.data
                ).decode("utf-8")
                flash("Password updated.", "success")

        current_user.full_name = form.full_name.data.strip() if form.full_name.data else None
        current_user.bio = form.bio.data.strip() if form.bio.data else None
        current_user.updated_at = utcnow()
        db.session.commit()
        flash("Profile saved.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", form=form, title="Profile")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            token = generate_token()
            user.reset_token = token
            user.reset_token_expires = utcnow() + timedelta(hours=1)
            db.session.commit()
            # In production send via email; here we flash for demo
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            flash(
                f"Reset link (demo — would be emailed): {reset_url}",
                "info",
            )
        else:
            flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form, title="Forgot Password")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    user = User.query.filter_by(reset_token=token).first_or_404()
    if user.reset_token_expires < utcnow():
        flash("Reset link has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        flash("Password reset! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form, title="Reset Password")
