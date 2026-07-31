from fastapi import APIRouter

from app.features.admin.router import router as admin_router
from app.features.auth.router import router as auth_router
from app.features.users.router import router as user_router
from app.features.wards.router import router as wards_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(user_router, prefix="/user")
router.include_router(wards_router)
router.include_router(admin_router, prefix="/admin")
