from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from fast_zero.models import User
from fast_zero.database import get_session
from fast_zero.schemas import Message, UserList, UserPublic, UserSchema, Token
from fast_zero.security import (
    get_current_user,
    get_password_hash,
    verify_password,
    create_access_token,
)

app = FastAPI()


@app.get("/", response_model=Message)
def read_root():
    return {"message": "Hello World!"}


@app.post("/users/", status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(
    user: UserSchema,
    session=Depends(get_session),
):
    db_user = session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )
    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Username already exists",
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Email already exists",
            )

    db_user = User(
        username=user.username,
        password=get_password_hash(user.password),
        email=user.email,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@app.get("/users/", response_model=UserList)
def read_users(
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    users = session.scalars(select(User).limit(limit).offset(offset))
    return {"users": users}


@app.get("/users/{user_id}", response_model=UserPublic)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user = session.scalar(select(User).where(User.id == user_id))
    if user:
        return user

    raise HTTPException(
        status_code=HTTPStatus.NOT_FOUND, detail="User not found"
    )


@app.put("/users/{user_id}", response_model=UserPublic)
def update_user(
    user_id: int,
    user: UserSchema,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Not enough permissions",
        )

    current_user.username = user.username
    current_user.email = user.email
    current_user.password = get_password_hash(user.password)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user


@app.delete("/users/{user_id}", response_model=Message)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Not enough permissions",
        )
    session.delete(current_user)
    session.commit()

    return {"message": "User deleted"}


@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user_db = session.scalar(
        select(User).where(User.email == form_data.username)
    )
    if not user_db or not verify_password(
        form_data.password, user_db.password
    ):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": user_db.email})
    return {"access_token": access_token, "token_type": "Bearer"}
