from http import HTTPStatus
from fast_zero.schemas import UserPublic


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
    response = client.get(
        "/users/", headers={"Authorization": f"Bearer {token}"}
    )
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
    response = client.delete(
        f"/users/{user.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "User deleted"}


def test_delete_user_not_found(client, token):
    response = client.delete(
        "/users/999", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": "Not enough permissions"}
