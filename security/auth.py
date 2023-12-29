import os

from jose import jwt
from dotenv import load_dotenv
import bcrypt


load_dotenv()


PRIVATE_KEY = os.getenv('JWT_PRIVATE_KEY')
PUBLIC_KEY = os.getenv('JWT_PUBLIC_KEY')


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def encode_jwt(payload: dict) -> str:
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    return token


def decode_jwt(token: str) -> dict | None:
    try:
        decoded_payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return decoded_payload
    except:
        return None