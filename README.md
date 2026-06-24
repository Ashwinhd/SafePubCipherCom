# SafePubCipherCom - CipherVault Pro

A secure web application for encryption, decryption, steganography, and cryptographic operations with user authentication and audit logging.

## Features

- **User Authentication**: Secure registration, login, and password reset
- **Encryption/Decryption**: Support for AES-256, Blowfish, and 3DES algorithms
- **Steganography**: Hide secrets inside images (LSB technique)
- **Vault**: Securely store encrypted files per user
- **Self-Destruct Messages**: Create time-expiring or read-limited encrypted messages
- **Typing Trainer**: Practice cryptographic typing with difficulty levels
- **Analytics**: Track encryption operations and user activity
- **CSRF Protection**: All forms protected against CSRF attacks

## Tech Stack

- **Backend**: Python 3.8+ with Flask 3.0.0
- **Database**: SQLAlchemy with SQLite (dev) / MySQL (production)
- **Cryptography**: PyCryptodome for AES-256-EAX, Blowfish-EAX, 3DES-CBC+HMAC
- **Authentication**: Flask-Login with Bcrypt password hashing
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Security**: Flask-WTF (CSRF), Flask-Bcrypt, Flask-Mail

## Project Structure

```
SafePubCipherCom/
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── README.md                # Project documentation
├── config/
│   ├── __init__.py
│   └── config.py            # Configuration for dev/test/prod
└── app/
    ├── __init__.py          # Flask app factory
    ├── models/
    │   ├── user.py          # User model with relationships
    │   └── vault.py         # VaultFile, EncryptionLog, SelfDestructMessage, TypingScore
    ├── routes/
    │   ├── auth_routes.py   # Registration, login, profile, password reset
    │   ├── main_routes.py   # Dashboard and index
    │   ├── encrypt_routes.py# Text and file encryption/decryption
    │   ├── stego_routes.py  # Image steganography
    │   ├── vault_routes.py  # Vault file management
    │   ├── message_routes.py# Self-destruct messages
    │   ├── trainer_routes.py# Typing trainer
    │   └── analytics_routes.py # Activity analytics
    ├── utils/
    │   ├── crypto.py        # Encryption utilities (AES, Blowfish, 3DES)
    │   ├── stego.py         # Steganography utilities
    │   ├── forms.py         # WTForms form definitions
    │   └── helpers.py       # Helper functions
    ├── templates/           # Jinja2 HTML templates
    │   ├── base.html        # Base template with navigation
    │   ├── auth/            # Authentication templates
    │   ├── main/            # Dashboard templates
    │   ├── encrypt/         # Encryption templates
    │   ├── stego/           # Steganography templates
    │   ├── vault/           # Vault templates
    │   ├── messages/        # Message templates
    │   ├── trainer/         # Trainer templates
    │   ├── analytics/       # Analytics templates
    │   └── errors/          # Error page templates
    └── static/
        ├── main.css         # Main stylesheet
        ├── main.js          # Main JavaScript
        └── trainer.js       # Typing trainer JavaScript
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip or conda
- Virtual environment (recommended)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Ashwinhd/SafePubCipherCom.git
   cd SafePubCipherCom
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and set SECRET_KEY and other settings
   ```

5. Initialize database:
   ```bash
   python run.py
   # Database will be created automatically on first run
   ```

## Running the Application

### Development
```bash
python run.py
# Application will be available at http://127.0.0.1:5000
```

### Production (with Gunicorn)
```bash
FLASK_ENV=production gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Usage

### User Registration
1. Navigate to `http://127.0.0.1:5000/auth/register`
2. Create account with username, email, and password (min 8 chars)
3. Login with credentials

### Encryption
1. Go to Dashboard → Encrypt
2. Choose text or file encryption
3. Select algorithm (AES-256 recommended)
4. Provide passphrase and content
5. Optionally save to vault

### Steganography
1. Go to Dashboard → Steganography
2. Upload carrier image (PNG recommended)
3. Upload secret file or enter text
4. Provide passphrase for encryption
5. Download image with hidden content

### Vault
- Access at Dashboard → Vault
- View all encrypted files
- Search and download files
- View encryption audit logs

## API Endpoints

### Authentication
- `GET/POST /auth/register` - User registration
- `GET/POST /auth/login` - User login
- `GET /auth/logout` - User logout
- `GET/POST /auth/profile` - User profile
- `GET/POST /auth/forgot-password` - Password reset request
- `GET/POST /auth/reset-password/<token>` - Password reset

### Main
- `GET /` - Landing page (redirects to dashboard if logged in)
- `GET /dashboard` - User dashboard with stats

### Encryption
- `GET/POST /encrypt/text` - Encrypt text
- `GET/POST /encrypt/decrypt-text` - Decrypt text
- `GET/POST /encrypt/file` - Encrypt file
- `GET/POST /encrypt/decrypt-file` - Decrypt file

### Steganography
- `GET/POST /stego/hide` - Hide secret in image
- `GET/POST /stego/extract` - Extract secret from image

### Vault
- `GET /vault` - List vault files
- `GET /vault/download/<file_id>` - Download encrypted file
- `GET /vault/delete/<file_id>` - Delete file

### Messages
- `GET/POST /messages/create` - Create self-destruct message
- `GET /messages/<token>` - View message (requires passphrase)

### Trainer
- `GET /trainer` - Typing trainer interface
- `POST /trainer/submit-score` - Submit typing score

### Analytics
- `GET /analytics` - User activity analytics

## Security Considerations

1. **Passwords**: Hashed with Bcrypt (cost=12)
2. **Encryption**: PBKDF2 key derivation with 200,000 iterations (dev), 300,000 (prod)
3. **CSRF**: All forms protected with Flask-WTF tokens
4. **Sessions**: HTTPOnly, SameSite cookies, 8-hour timeout
5. **Database**: Foreign key constraints, cascade deletion
6. **Input Validation**: WTForms validators on all forms
7. **XSS Prevention**: Auto-escaping in Jinja2 templates
8. **File Upload**: Extension whitelisting, size limits (16 MB)

## Cryptographic Algorithms

### AES-256-EAX (Recommended)
- 256-bit key via PBKDF2-HMAC-SHA256
- EAX mode for authenticated encryption
- 16-byte nonce, 16-byte authentication tag
- Salt: 32 bytes, 200k iterations (dev) / 300k (prod)

### Blowfish-EAX
- 448-bit key via PBKDF2
- EAX mode for authenticated encryption
- Alternative to AES

### 3DES-CBC+HMAC
- 192-bit encryption key + 256-bit HMAC key
- CBC mode with PKCS#7 padding
- HMAC-SHA256 for message authentication
- Encrypt-then-MAC pattern (prevents padding oracle)

## Database Models

### User
- `username` (unique, indexed)
- `email` (unique, indexed)
- `password_hash` (Bcrypt)
- `full_name`, `avatar_color`, `bio`
- `is_active`, `is_admin`, `failed_logins`
- Timestamps: `created_at`, `updated_at`
- Relationships: vault_files, encrypt_logs, messages, typing_scores

### VaultFile
- `original_name`, `stored_name` (UUID-based)
- `file_size` (bytes), `file_type`
- `algorithm` (AES-256, Blowfish, 3DES)
- `is_steganographic` (boolean)
- `description`
- `user_id` (foreign key)
- Timestamp: `created_at`

### EncryptionLog
- `operation` (encrypt/decrypt/stego_hide/stego_extract)
- `algorithm`, `file_name`, `file_size`
- `success` (boolean), `error_message`
- `user_id` (foreign key)
- Timestamp: `created_at`

### SelfDestructMessage
- `token` (unique, indexed)
- `encrypted_content` (TEXT)
- `algorithm` (AES-256, Blowfish, 3DES)
- `max_reads` (0 = unlimited), `read_count`
- `expires_at`, `is_destroyed`
- `title`
- `user_id` (foreign key)
- Timestamps: `created_at`, `destroyed_at`

### TypingScore
- `wpm` (words per minute)
- `accuracy` (0.0 - 100.0)
- `difficulty` (easy/medium/hard)
- `duration_seconds`
- `text_snippet`
- `user_id` (foreign key)
- Timestamp: `created_at`

## Environment Variables

```ini
# Flask
FLASK_ENV=development|production|testing
FLASK_APP=run.py
SECRET_KEY=your-secret-key-minimum-32-chars

# Database
DEV_DATABASE_URL=sqlite:///ciphervault_dev.db
DATABASE_URL=sqlite:///ciphervault.db

# Mail (Optional - for password reset emails)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@ciphervault.local
```

## Troubleshooting

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.8+: `python --version`

### Database Errors
- Delete old database files to reset: `rm *.db`
- Database recreates automatically on startup

### Port Already in Use
- Change port in `run.py`: `app.run(host="127.0.0.1", port=5001)`

### Module Not Found
- Verify virtual environment is activated
- Reinstall dependencies: `pip install --upgrade -r requirements.txt`

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues and feature requests, please use the GitHub Issues page.

## Version History

### v1.0.0 (Current)
- ✅ User authentication with secure password reset
- ✅ AES-256-EAX, Blowfish-EAX, 3DES-CBC+HMAC encryption
- ✅ Image steganography with LSB technique
- ✅ Vault system with per-user encrypted file storage
- ✅ Audit logging for all encryption operations
- ✅ Self-destruct messages with time/read limits
- ✅ Typing trainer with difficulty levels
- ✅ Analytics dashboard with user statistics
- ✅ CSRF protection on all forms
- ✅ Responsive UI with HTML5/CSS3
