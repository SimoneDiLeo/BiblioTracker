from passlib.context import CryptContext

# It's recommended to use a modern hashing algorithm like bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# For JWT
# These should ideally be in a config file or environment variables
SECRET_KEY = "your-secret-key"  # Replace with a strong, random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
