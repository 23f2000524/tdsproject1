# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi[standard]",
#   "uvicorn",
# ]
# ///
import os
from fastapi import Fastapi

def validate_secret(secret: str) -> bool:
    return secret == os.get_env("SECRET_KEY")

def round1():
    pass

def round2():
    pass


def create_repo():
    pass

def enable_pages():
    pass

def push_files_to_pages():
    pass

app = Fastapi()

@app.post("/handle_task")
def handle_task(data: dict):
    if not validate_secret(data.get("secret", "")):
        return {"error": "Incorrect secret"}
    else:
        if data.get("round") == 1:
            round1()
        elif data.get("round") == 2:
            round2()
        else:
            return {"error", "Invalid round"}
    print(data)
    return {"message": "Task recieved", "data": data}

if __name__ == "__main__":
    import uvicron
    uvicron.run(app,host="0.0.0.0",port=8000)