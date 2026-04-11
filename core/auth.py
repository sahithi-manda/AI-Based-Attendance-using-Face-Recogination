import json
import os
import hashlib
import binascii

AUTH_FILE = 'auth.json'

def _hash_password(password: str) -> str:
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def _verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64].encode('ascii')
    stored_hash = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_hash

def init_admin():
    """Initializes the admin user with default password 'admin' if no auth config exists."""
    if not os.path.exists(AUTH_FILE):
        data = {
            "users": {
                "admin": _hash_password("admin")
            }
        }
        with open(AUTH_FILE, 'w') as f:
            json.dump(data, f, indent=4)

def verify_login(username, password):
    """Verifies the username and password against the auth config."""
    if not os.path.exists(AUTH_FILE):
        init_admin()
        
    try:
        with open(AUTH_FILE, 'r') as f:
            data = json.load(f)
            
        users = data.get("users", {})
        if username in users:
            return _verify_password(users[username], password)
    except Exception as e:
        print(f"Auth error: {e}")
        return False
        
    return False

def update_password(username, new_password):
    """Updates the password for a given user."""
    if not os.path.exists(AUTH_FILE):
        return False, "Auth file missing."
        
    try:
        with open(AUTH_FILE, 'r') as f:
            data = json.load(f)
            
        users = data.get("users", {})
        if username in users:
            users[username] = _hash_password(new_password)
            with open(AUTH_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            return True, "Password updated successfully."
        else:
            return False, "User not found."
    except Exception as e:
        return False, str(e)
