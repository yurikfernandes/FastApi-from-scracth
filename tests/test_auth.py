from http import HTTPStatus
from unittest.mock import patch

from fast_zero.security import Settings
from jwt import encode


settings = Settings()


def test_get_token(client, user):
    response = client.post(
        "/auth/token",
        data={
            "username": user.email,
            "password": user.clean_password,
        },
    )
    assert response.status_code == HTTPStatus.OK
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "Bearer"


def test_get_token_invalid_credentials(client, user):
    response = client.post(
        "/auth/token",
        data={
            "username": user.email,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Incorrect email or password"}


def test_jwt_invalid_token(client, user):
    response = client.delete(
        f"/users/{user.id}",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


@patch("fast_zero.security.decode")
def test_current_user_missing_sub_with_patch(mock_decode, client, user):
    mock_decode.return_value = {"some": "data"}

    response = client.delete(
        f"/users/{user.id}",
        headers={"Authorization": "Bearer any_token"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


def test_current_user_not_found_in_database(client):
    payload = {"sub": "nonexistent@example.com"}
    token = encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    response = client.delete(
        "/users/999",  # Qualquer endpoint que use get_current_user
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}
