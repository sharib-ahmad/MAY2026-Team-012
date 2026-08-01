from fastapi import APIRouter

from app.features.admin.router import router as admin_router
from app.features.auth.router import router as auth_router
from app.features.bulk_pickups.router import router as bulk_pickups_router
from app.features.collection_ops.router import router as collection_ops_router
from app.features.complaints.router import router as complaints_router
from app.features.manager.router import router as manager_router
from app.features.notifications.router import router as notifications_router
from app.features.users.router import router as user_router
from app.features.wards.router import router as wards_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
# Deprecated aliases retained for already-deployed clients. New clients must
# use the approved /api/v1/auth/* contract.
router.include_router(auth_router)
router.include_router(user_router, prefix="/user")
router.include_router(bulk_pickups_router, prefix="/user")
router.include_router(complaints_router, prefix="/user")
router.include_router(collection_ops_router, prefix="/user")
router.include_router(notifications_router, prefix="/user")
router.include_router(wards_router)
router.include_router(admin_router, prefix="/admin")
router.include_router(manager_router)
