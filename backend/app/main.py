from fastapi import FastAPI

from app.routers import ingest
from app.routers import threads
from app.routers import contacts

app = FastAPI(title="SenAI CRM")

app.include_router(ingest.router)
app.include_router(threads.router)
app.include_router(contacts.router)

@app.get("/")
def root():
    return {"message": "SenAI CRM Backend"}