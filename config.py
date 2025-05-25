import os

# OpenAlex API Configuration
OPENALEX_API_BASE_URL = "https://api.openalex.org"
# It's good practice to use environment variables for sensitive or deployment-specific info
OPENALEX_POLITE_EMAIL = os.getenv("OPENALEX_POLITE_EMAIL", "default.email@example.com") # Provide a default or ensure it's set in the env

# JWT Secret Key - loading from existing auth/security.py for consistency if needed elsewhere,
# or can be defined directly here if preferred.
# For now, assume it's managed in auth/security.py or a dedicated secrets management system.
# from auth.security import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Database URL - can also be centralized here if not already managed.
# SQLALCHEMY_DATABASE_URL = "sqlite:///./ris.db"
