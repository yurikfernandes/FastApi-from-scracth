from fast_zero.security import Settings, create_access_token
from jwt import decode


settings = Settings()


def test_jwt():
    data = {"sub": "test@test.com"}
    token = create_access_token(data)

    result = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )

    assert result["sub"] == data["sub"]
    assert "exp" in result
