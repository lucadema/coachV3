from fastapi import FastAPI

app = FastAPI(title="Coach V3 API")


@app.get("/session_initialise")
def session_initialise():
    return {"message": "default response from session_initialise"}


@app.post("/user_message")
def user_message():
    return {"message": "default response from user_message"}