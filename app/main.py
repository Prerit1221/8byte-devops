from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.database import engine, Base
from app.routers import items, health

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="8Byte DevOps Demo API",
    description="A simple CRUD API built for DevOps assignment",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics — exposes /metrics endpoint automatically
Instrumentator().instrument(app).expose(app)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(items.router, prefix="/items", tags=["Items"])


@app.get("/", tags=["Root"])
def root():
    return {"message": "8Byte DevOps Demo API is running 🚀"}
