from http import HTTPStatus
from fast_zero.schemas import UserPublic
from unittest.mock import patch


def test_root_deve_retornar_ok_e_ola_mundo(client):
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Hello World!"}


def test_create_user(client):
    response = client.post(
        "/users/",
        json={
            "username": "user",
            "email": "user@example.com",
            "password": "secret",
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        "username": "user",
        "email": "user@example.com",
        "id": 1,
    }


def test_create_user_username_exists(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()
    username = user_schema["username"]
    response = client.post(
        "/users/",
        json={
            "username": username,
            "email": "testuser@example.com",
            "password": "secret",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "Username already exists"}


def test_create_user_email_exists(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()
    email = user_schema["email"]
    response = client.post(
        "/users/",
        json={
            "username": "anotheruser",
            "email": email,
            "password": "secret",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "Email already exists"}


def test_read_users_empty(client):
    response = client.get("/users/")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"users": []}


def test_read_users_when_has_user(client, user, token):
    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"users": [user_schema]}


def test_read_user_by_id(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()

    response = client.get("/users/1/")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == user_schema


def test_read_user_not_found(client):
    response = client.get("/users/999")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": "User not found"}


def test_update_user(client, user, token):
    response = client.put(
        f"/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "updated_user",
            "email": "updated_user@example.com",
            "password": "mynewpassword",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "username": "updated_user",
        "email": "updated_user@example.com",
        "id": 1,
    }


def test_update_user_not_found(client, token):
    response = client.put(
        "/users/999",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "nonexistent_user",
            "email": "nonexistent_user@example.com",
            "password": "mynewpassword",
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": "Not enough permissions"}


def test_delete_user(client, user, token):
    response = client.delete(f"/users/{user.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "User deleted"}


def test_delete_user_not_found(client, token):
    response = client.delete("/users/999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": "Not enough permissions"}


def test_get_token(client, user):
    response = client.post(
        "/token",
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
        "/token",
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


@patch('fast_zero.security.decode')
def test_current_user_missing_sub_with_patch(mock_decode, client, user):
    mock_decode.return_value = {"some": "data"}
    
    response = client.delete(
        f"/users/{user.id}",
        headers={"Authorization": "Bearer any_token"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


def test_current_user_not_found_in_database(client):
    from jwt import encode
    from fast_zero.security import SECRET_KEY, ALGORITHM
    
    payload = {"sub": "nonexistent@example.com"}
    token = encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    response = client.delete(
        "/users/999",  # Qualquer endpoint que use get_current_user
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}