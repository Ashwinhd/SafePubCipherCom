"""
CipherVault Pro — WTForms definitions.
All forms include CSRF protection via Flask-WTF.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField, PasswordField, TextAreaField, SelectField,
    IntegerField, BooleanField, HiddenField, FloatField, SubmitField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, NumberRange,
    Optional, ValidationError, Regexp,
)
from app.models.user import User


# ---------------------------------------------------------------------------
# Auth forms
# ---------------------------------------------------------------------------

class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=64),
            Regexp(r"^[A-Za-z0-9_]+$", message="Letters, numbers, and underscores only."),
        ],
    )
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField("Full Name", validators=[Optional(), Length(max=128)])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Stay logged in")
    submit = SubmitField("Log In")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Reset Password")


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[Optional(), Length(max=128)])
    bio = StringField("Bio", validators=[Optional(), Length(max=256)])
    current_password = PasswordField("Current Password", validators=[Optional()])
    new_password = PasswordField("New Password", validators=[Optional(), Length(min=8)])
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[Optional(), EqualTo("new_password")],
    )
    submit = SubmitField("Save Changes")


# ---------------------------------------------------------------------------
# Encryption forms
# ---------------------------------------------------------------------------

ALGORITHM_CHOICES = [
    ("AES-256", "AES-256 (recommended)"),
    ("Blowfish", "Blowfish"),
    ("3DES", "Triple DES (3DES)"),
]


class EncryptTextForm(FlaskForm):
    plaintext = TextAreaField(
        "Plain Text",
        validators=[DataRequired(), Length(max=65536)],
    )
    passphrase = PasswordField("Passphrase", validators=[DataRequired(), Length(min=6)])
    algorithm = SelectField("Algorithm", choices=ALGORITHM_CHOICES, default="AES-256")
    save_to_vault = BooleanField("Save encrypted output to Vault")
    vault_description = StringField("Vault Note", validators=[Optional(), Length(max=512)])
    submit = SubmitField("Encrypt")


class DecryptTextForm(FlaskForm):
    ciphertext_b64 = TextAreaField(
        "Encrypted Content (Base64)",
        validators=[DataRequired()],
    )
    passphrase = PasswordField("Passphrase", validators=[DataRequired()])
    algorithm = SelectField("Algorithm", choices=ALGORITHM_CHOICES, default="AES-256")
    submit = SubmitField("Decrypt")


class EncryptFileForm(FlaskForm):
    file = FileField(
        "File to Encrypt",
        validators=[FileRequired()],
    )
    passphrase = PasswordField("Passphrase", validators=[DataRequired(), Length(min=6)])
    algorithm = SelectField("Algorithm", choices=ALGORITHM_CHOICES, default="AES-256")
    save_to_vault = BooleanField("Save to Vault after encrypting")
    vault_description = StringField("Vault Note", validators=[Optional(), Length(max=512)])
    submit = SubmitField("Encrypt File")


class DecryptFileForm(FlaskForm):
    file = FileField("Encrypted File (.enc)", validators=[FileRequired()])
    passphrase = PasswordField("Passphrase", validators=[DataRequired()])
    algorithm = SelectField("Algorithm", choices=ALGORITHM_CHOICES, default="AES-256")
    submit = SubmitField("Decrypt File")


# ---------------------------------------------------------------------------
# Steganography forms
# ---------------------------------------------------------------------------

class StegoHideForm(FlaskForm):
    image = FileField(
        "Carrier Image (PNG recommended)",
        validators=[FileRequired(), FileAllowed(["png", "jpg", "jpeg", "bmp"], "Images only.")],
    )
    secret_text = TextAreaField(
        "Secret Text",
        validators=[Optional(), Length(max=32768)],
    )
    secret_file = FileField("Or upload a secret file", validators=[Optional()])
    passphrase = PasswordField("Passphrase (for encryption)", validators=[DataRequired(), Length(min=6)])
    algorithm = SelectField("Encryption Algorithm", choices=ALGORITHM_CHOICES, default="AES-256")
    submit = SubmitField("Hide Secret in Image")


class StegoExtractForm(FlaskForm):
    image = FileField(
        "Image with hidden content",
        validators=[FileRequired(), FileAllowed(["png", "jpg", "jpeg", "bmp"], "Images only.")],
    )
    passphrase = PasswordField("Passphrase", validators=[DataRequired()])
    algorithm = SelectField("Algorithm used", choices=ALGORITHM_CHOICES, default="AES-256")
    submit = SubmitField("Extract Secret")


# ---------------------------------------------------------------------------
# Vault forms
# ---------------------------------------------------------------------------

class VaultSearchForm(FlaskForm):
    query = StringField("Search", validators=[Optional(), Length(max=128)])
    submit = SubmitField("Search")


# ---------------------------------------------------------------------------
# Self-destruct message forms
# ---------------------------------------------------------------------------

class CreateMessageForm(FlaskForm):
    title = StringField("Message Title", validators=[Optional(), Length(max=128)])
    content = TextAreaField("Message Content", validators=[DataRequired(), Length(max=65536)])
    passphrase = PasswordField("Passphrase (to encrypt)", validators=[DataRequired(), Length(min=6)])
    algorithm = SelectField("Algorithm", choices=ALGORITHM_CHOICES, default="AES-256")
    max_reads = IntegerField(
        "Max reads (0 = unlimited)",
        validators=[NumberRange(min=0, max=100)],
        default=1,
    )
    expires_hours = IntegerField(
        "Expires after (hours, 0 = never)",
        validators=[NumberRange(min=0, max=168)],
        default=24,
    )
    submit = SubmitField("Create Message")


class ReadMessageForm(FlaskForm):
    passphrase = PasswordField("Passphrase", validators=[DataRequired()])
    submit = SubmitField("Unlock Message")


# ---------------------------------------------------------------------------
# Typing trainer form
# ---------------------------------------------------------------------------

class TypingResultForm(FlaskForm):
    wpm = FloatField("WPM", validators=[DataRequired(), NumberRange(min=0, max=300)])
    accuracy = FloatField("Accuracy", validators=[DataRequired(), NumberRange(min=0, max=100)])
    difficulty = HiddenField("Difficulty")
    duration = IntegerField("Duration", validators=[DataRequired()])
    text_snippet = HiddenField("Text")
    submit = SubmitField("Save Score")
