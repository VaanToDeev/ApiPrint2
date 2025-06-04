from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, models, auth
from app.database import get_db

router = APIRouter(prefix="/professors", tags=["Professors"])

@router.get("/me", response_model=schemas.ProfessorPublic)
async def read_professor_me(
    current_user: models.Professor = Depends(auth.get_current_active_user)
):
    if not isinstance(current_user, models.Professor):
        raise HTTPException(status_code=403, detail="Not a professor account")
    return current_user

# Add more professor-specific endpoints (e.g., view TCCs they orient)