from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "8byte-devops-api"}


@router.get("/health/db")
def db_health_check(db: Session = Depends(get_db)):
    """Health check including DB connectivity"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
