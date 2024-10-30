from fastapi import FastAPI

from epg import dependencies
from epg.endpoints import clients, methods

app = FastAPI(root_path="/api", lifespan=dependencies.lifespan)
app.include_router(clients.app, prefix='/clients')
app.include_router(methods.app, prefix='/list')
