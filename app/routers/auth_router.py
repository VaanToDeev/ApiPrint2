from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # For form data login
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, auth, models
from app.database import get_db
from app.core.security import create_access_token
from app.core.config import settings
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me")
async def get_current_user(
    current_user: models.Professor | models.Estudante = Depends(auth.get_current_active_user)
):
    if isinstance(current_user, models.Professor):
        user_type = "professor"
        return {
            "id": current_user.id,
            "nome": current_user.nome,
            "email": current_user.email,
            "role": getattr(current_user, "role", None),
            "user_type": user_type,
            "siape": current_user.siape,
            "departamento": current_user.departamento,
            "titulacao": current_user.titulacao,
            "telefone": current_user.telefone
        }
    else:  # Estudante
        user_type = "estudante"
        return {
            "id": current_user.id,
            "nome": current_user.nome,
            "email": current_user.email,
            "matricula": current_user.matricula,
            "status": current_user.status.value if current_user.status else None,
            "turma": current_user.turma,
            "telefone": current_user.telefone,
            "curso_id": current_user.curso_id,
            "user_type": user_type
}

@router.post("/register/student", response_model=schemas.EstudantePublic, status_code=status.HTTP_201_CREATED)
async def register_student(
    student_in: schemas.EstudanteCreate, db: AsyncSession = Depends(get_db)
):
    db_student_email = await crud.get_estudante_by_email(db, email=student_in.email)
    if db_student_email:
        raise HTTPException(status_code=400, detail="Email already registered by a student")
    
    db_professor_email = await crud.get_professor_by_email(db, email=student_in.email)
    if db_professor_email:
        raise HTTPException(status_code=400, detail="Email already registered by a professor")

    db_student_matricula = await crud.get_estudante_by_matricula(db, matricula=student_in.matricula)
    if db_student_matricula:
        raise HTTPException(status_code=400, detail="Matricula already registered")
    
    # Optionally check if curso_id exists if provided
    if student_in.curso_id:
        curso = await crud.get_curso_by_id(db, student_in.curso_id)
        if not curso:
            raise HTTPException(status_code=404, detail=f"Curso with id {student_in.curso_id} not found.")

    return await crud.create_estudante(db=db, estudante=student_in)

@router.post("/register/professor", response_model=schemas.ProfessorPublic, status_code=status.HTTP_201_CREATED)
async def register_professor(
    professor_in: schemas.ProfessorCreate, db: AsyncSession = Depends(get_db)
):
    # Ensure only admins can create other professors with special roles (admin/coordenador)
    # For self-registration, role should default to PROFESSOR or be enforced.
    # Here we assume self-registration creates a standard professor.
    # If an admin is creating users, they might pass a role, handled in an admin endpoint.
    if professor_in.role != models.UserRole.PROFESSOR:
         raise HTTPException(status_code=403, detail="Cannot self-register with special roles. Contact an admin.")

    db_professor_email = await crud.get_professor_by_email(db, email=professor_in.email)
    if db_professor_email:
        raise HTTPException(status_code=400, detail="Email already registered by a professor")

    db_student_email = await crud.get_estudante_by_email(db, email=professor_in.email)
    if db_student_email:
        raise HTTPException(status_code=400, detail="Email already registered by a student")

    db_professor_siape = await crud.get_professor_by_siape(db, siape=professor_in.siape)
    if db_professor_siape:
        raise HTTPException(status_code=400, detail="SIAPE already registered")
    
    return await crud.create_professor(db=db, professor=professor_in, role=models.UserRole.PROFESSOR)


@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await auth.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_type = "professor" if isinstance(user, models.Professor) else "estudante"
    user_role = user.role if isinstance(user, models.Professor) else None
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": user_type, "role": user_role.value if user_role else None},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
    