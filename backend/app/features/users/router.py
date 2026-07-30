# app/features/users/router.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])
