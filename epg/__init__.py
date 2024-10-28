from fastapi import FastAPI

from epg import clients, dependencies

app = FastAPI(root_path="/api", lifespan=dependencies.lifespan)
app.mount('/clients', clients.app)
