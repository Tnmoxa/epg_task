from fastapi import FastAPI

from epg import clients


app = FastAPI(root_path="/api")
app.mount('/clients', clients.app)
