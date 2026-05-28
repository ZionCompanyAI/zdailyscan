from fastapi import FastAPI

app = FastAPI(title="ZDailyScan")


@app.get("/health")
def health():
    return {"status": "ok", "service": "zdailyscan"}
