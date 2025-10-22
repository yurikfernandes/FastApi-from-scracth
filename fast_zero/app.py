from fastapi import FastAPI

from fast_zero.schemas import Message
from fast_zero.routers import users, auth

app = FastAPI()
app.include_router(users.router)
app.include_router(auth.router)


@app.get("/", response_model=Message)
def read_root():
    return {"message": "Hello World!"}
