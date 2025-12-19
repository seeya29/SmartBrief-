from fastapi import FastAPI
from .service import router

app = FastAPI()
app.include_router(router)

