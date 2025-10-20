from fast_zero.models import User

from sqlalchemy import select


def test_create_user(session):
    new_user = User(
        username="testuser",
        email="testuser@example.com",
        password="securepassword",
    )
    session.add(new_user)
    session.commit()

    result = session.scalar(
        select(User).where(User.email == "testuser@example.com")
    )

    assert result.username == "testuser"
    assert result.id is not None
