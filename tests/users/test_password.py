"""Unit tests for the password hashing utility (argon2 via pwdlib)."""

from app.domains.users.password import hash_password, verify_password


def test_hash_password_returns_argon2_hash_not_plaintext():
    # Arrange
    plain = "correct horse battery staple"

    # Act
    hashed = hash_password(plain)

    # Assert
    assert hashed != plain
    assert hashed.startswith("$argon2")


def test_verify_password_accepts_correct_password():
    # Arrange
    plain = "s3cret-passw0rd"
    hashed = hash_password(plain)

    # Act
    result = verify_password(plain, hashed)

    # Assert
    assert result is True


def test_verify_password_rejects_wrong_password():
    # Arrange
    hashed = hash_password("the-right-one")

    # Act
    result = verify_password("the-wrong-one", hashed)

    # Assert
    assert result is False


def test_hash_password_is_salted_so_same_input_differs():
    # Arrange
    plain = "same-password"

    # Act
    first = hash_password(plain)
    second = hash_password(plain)

    # Assert - distinct hashes (random salt) that both still verify
    assert first != second
    assert verify_password(plain, first)
    assert verify_password(plain, second)


def test_verify_password_handles_unicode():
    # Arrange
    plain = "pâssw0rd-é-🔒"
    hashed = hash_password(plain)

    # Act / Assert
    assert verify_password(plain, hashed) is True
    assert verify_password("password", hashed) is False
