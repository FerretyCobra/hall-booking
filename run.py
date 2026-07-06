"""Run the server on the LAN. Equivalent to:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
Other machines reach it at http://<this-machine-ip>:8000/
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
