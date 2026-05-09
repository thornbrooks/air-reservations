import os
import requests
from firebase_admin import auth as firebase_auth
from firebase_admin import firestore as fs
from flask import session

FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY', '')

class AuthService:

    @staticmethod
    def login(email, password):
        if not FIREBASE_WEB_API_KEY:
            return {'error': 'Server configuration error: missing FIREBASE_WEB_API_KEY'}
        try:
            resp = requests.post(
                f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}',
                json={'email': email, 'password': password, 'returnSecureToken': True},
                timeout=10,
            )
            data = resp.json()
            if 'error' in data:
                msg = data['error'].get('message', 'Login failed')
                if msg in ('EMAIL_NOT_FOUND', 'INVALID_PASSWORD', 'INVALID_LOGIN_CREDENTIALS'):
                    return {'error': 'Invalid email or password'}
                return {'error': msg}
            return {'uid': data['localId'], 'email': data['email']}
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def register(email, password, user_data):
        try:
            user = firebase_auth.create_user(email=email, password=password)
            from app.firebase_config import db
            if db:
                db.collection('users').document(user.uid).set({
                    'uid': user.uid,
                    'email': email,
                    'role': user_data.get('role', 'guest'),
                    'name': user_data.get('name', ''),
                    'phone': '',
                    'bio': '',
                    'profile_image': '',
                    'created_at': fs.SERVER_TIMESTAMP,
                    'updated_at': fs.SERVER_TIMESTAMP,
                })
            return user
        except firebase_auth.EmailAlreadyExistsError:
            return {'error': 'An account with this email already exists'}
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def verify_token(token):
        try:
            return firebase_auth.verify_id_token(token)
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def send_password_reset(email):
        if not FIREBASE_WEB_API_KEY:
            return {'error': 'Server configuration error: missing FIREBASE_WEB_API_KEY'}
        try:
            resp = requests.post(
                f'https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}',
                json={'requestType': 'PASSWORD_RESET', 'email': email},
                timeout=10,
            )
            data = resp.json()
            if 'error' in data:
                msg = data['error'].get('message', 'Failed to send reset email')
                if msg == 'EMAIL_NOT_FOUND':
                    return {'error': 'No account found with that email address'}
                return {'error': msg}
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def logout():
        session.clear()
