from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {
        "ok": True,
        "message": "Vercel Python is working"
    }
