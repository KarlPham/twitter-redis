from fastapi import FastAPI

app = FastAPI(title="Mini Twitter")

@app.get("/health")
async def health():
    return {"status": "ok"}