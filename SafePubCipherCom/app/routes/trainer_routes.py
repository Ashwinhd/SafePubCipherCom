"""
CipherVault Pro — Typing Trainer Routes
"""

import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.vault import TypingScore
from app.utils.forms import TypingResultForm

trainer_bp = Blueprint("trainer", __name__)

TYPING_TEXTS = {
    "easy": [
        "The quick brown fox jumps over the lazy dog.",
        "Pack my box with five dozen liquor jugs.",
        "How vexingly quick daft zebras jump.",
    ],
    "medium": [
        "Cryptography is the practice of securing communications from adversaries.",
        "Encryption transforms readable data into an unreadable format using algorithms.",
        "A strong passphrase is your first and most important line of defense.",
        "Steganography hides secret information inside ordinary-looking files.",
    ],
    "hard": [
        "AES-256 uses 14 rounds of substitution-permutation operations on 128-bit blocks with a 256-bit key schedule.",
        "PBKDF2 derives cryptographic keys from passphrases using iterated HMAC-SHA256 with a random salt to resist brute-force attacks.",
        "The Feistel network structure of Blowfish allows encryption and decryption to share the same code path, differing only in subkey order.",
        "Authenticated encryption with associated data (AEAD) provides both confidentiality and integrity in a single primitive, eliminating composition errors.",
    ],
}


@trainer_bp.route("/")
@login_required
def index():
    difficulty = request.args.get("difficulty", "medium")
    if difficulty not in TYPING_TEXTS:
        difficulty = "medium"

    text = random.choice(TYPING_TEXTS[difficulty])

    # Leaderboard top 10
    leaderboard = (
        TypingScore.query
        .join(TypingScore.user)
        .with_entities(
            TypingScore.user_id,
            TypingScore.wpm,
            TypingScore.accuracy,
            TypingScore.difficulty,
            TypingScore.created_at,
        )
        .filter_by(difficulty=difficulty)
        .order_by(TypingScore.wpm.desc())
        .limit(10)
        .all()
    )

    # Current user's personal best
    personal_best = (
        TypingScore.query
        .filter_by(user_id=current_user.id, difficulty=difficulty)
        .order_by(TypingScore.wpm.desc())
        .first()
    )

    form = TypingResultForm()
    return render_template(
        "trainer/index.html",
        title="Typing Trainer",
        typing_text=text,
        difficulty=difficulty,
        leaderboard=leaderboard,
        personal_best=personal_best,
        form=form,
        all_difficulties=list(TYPING_TEXTS.keys()),
    )


@trainer_bp.route("/save", methods=["POST"])
@login_required
def save_score():
    form = TypingResultForm()
    if form.validate_on_submit():
        score = TypingScore(
            user_id=current_user.id,
            wpm=round(form.wpm.data, 2),
            accuracy=round(form.accuracy.data, 2),
            difficulty=form.difficulty.data or "medium",
            duration_seconds=form.duration.data,
            text_snippet=form.text_snippet.data[:256] if form.text_snippet.data else None,
        )
        db.session.add(score)
        db.session.commit()
        return jsonify({"status": "ok", "wpm": score.wpm, "accuracy": score.accuracy})
    return jsonify({"status": "error", "errors": form.errors}), 400


@trainer_bp.route("/history")
@login_required
def history():
    scores = (
        TypingScore.query
        .filter_by(user_id=current_user.id)
        .order_by(TypingScore.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template("trainer/history.html", title="Typing History", scores=scores)
