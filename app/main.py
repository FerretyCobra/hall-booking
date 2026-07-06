"""FastAPI entrypoint. Serves the JSON API and the two static front-ends:
  /            -> booking portal (static/index.html)
  /dashboard   -> IT dashboard  (static/dashboard.html)
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from .config import SECRET_KEY, BASE_DIR
from .seed import init_db
from .routers import public, auth, halls, features, dashboard

app = FastAPI(title="Hall Booking")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=False)

app.include_router(public.router)
app.include_router(auth.router)
app.include_router(halls.router)
app.include_router(features.router)
app.include_router(dashboard.router)

STATIC_DIR = BASE_DIR / "static"


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/")
def portal():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/dashboard")
def dash():
    return FileResponse(STATIC_DIR / "dashboard.html")


# CSS/JS assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
