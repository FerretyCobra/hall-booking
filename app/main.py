"""FastAPI entrypoint. Serves the JSON API and the two static front-ends:
  /            -> booking portal (static/index.html)
  /dashboard   -> IT dashboard  (static/dashboard.html)
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from .config import SECRET_KEY, BASE_DIR, SESSION_COOKIE_HTTPS_ONLY
from .seed import init_db
from .routers import public, auth, halls, features, dashboard

app = FastAPI(title="Hall Booking")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=SESSION_COOKIE_HTTPS_ONLY)

app.include_router(public.router)
app.include_router(auth.router)
app.include_router(halls.router)
app.include_router(features.router)
app.include_router(dashboard.router)

STATIC_DIR = BASE_DIR / "static"


@app.on_event("startup")
def _startup():
    init_db()
    
    # Start the daily department notifications background scheduler
    import threading
    import time
    import datetime
    from .database import SessionLocal
    from .services.notifications import send_department_notifications, send_upcoming_reminders

    def run_scheduler():
        # Check every 60 seconds
        while True:
            now = datetime.datetime.now()
            today_str = now.date().isoformat()
            
            # Run daily department notifications if it is 18:00 (6 PM) or later and hasn't run today
            if now.hour >= 18:
                db = SessionLocal()
                try:
                    from .services.settings import get_setting, save_settings
                    last_run = get_setting(db, "last_summary_notification_date", "")
                    if last_run != today_str:
                        send_department_notifications(db)
                        save_settings(db, {"last_summary_notification_date": today_str})
                except Exception as e:
                    print(f"Error running daily department notifications: {e}")
                finally:
                    db.close()
            
            # Run meeting reminders
            db = SessionLocal()
            try:
                send_upcoming_reminders(db)
            except Exception as e:
                print(f"Error running meeting reminders: {e}")
            finally:
                db.close()
                
            time.sleep(60)  # Check every 60 seconds

    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()


@app.get("/")
def portal():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/dashboard")
def dash():
    return FileResponse(STATIC_DIR / "dashboard.html")


# CSS/JS assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
