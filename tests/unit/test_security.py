import pytest
from auth.security import get_password_hash, verify_password

def test_password_hashing_and_verification():
    password = "securepassword123"
    
    # Test hashing
    hashed_password = get_password_hash(password)
    assert hashed_password is not None
    assert hashed_password != password # Ensure it's not storing plain text
    
    # Test verification - correct password
    assert verify_password(password, hashed_password) is True
    
    # Test verification - incorrect password
    assert verify_password("wrongpassword", hashed_password) is False

def test_verify_password_with_different_hash():
    password = "securepassword123"
    hashed_password1 = get_password_hash(password)
    
    # A hash of a different password
    hashed_password2 = get_password_hash("anotherpassword")
    
    assert verify_password(password, hashed_password1) is True
    assert verify_password(password, hashed_password2) is False

def test_password_hash_is_consistent_for_bcrypt():
    # Bcrypt generates a new salt each time, so hashes of the same password will be different.
    # This test ensures that verify_password still works.
    password = "mypassword"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    assert hash1 != hash2 # Hashes should be different due to different salts
    assert verify_password(password, hash1) # Verification should still work
    assert verify_password(password, hash2) # Verification should still work
