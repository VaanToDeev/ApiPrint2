from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, models, auth
from app.database import get_db

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/me", response_model=schemas.EstudantePublic)
async def read_student_me(
    current_user: models.Estudante = Depends(auth.get_current_active_user)
):
    if not isinstance(current_user, models.Estudante):
        raise HTTPException(status_code=403, detail="Not a student account")
    return current_user

# Add more student-specific endpoints here based on ERD (e.g., view TCCs)