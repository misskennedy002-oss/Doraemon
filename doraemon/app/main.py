from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import chat
from app.database import engine, Base
import app.models # Import models so SQLAlchemy knows they exist

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Doraemon AI Assistant")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(chat.router)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="chat/index.html")