from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def session():
    return "Hello World!"