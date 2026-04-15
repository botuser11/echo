from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.health import router as health_router
from app.api.public import router as public_router
from app.core.config import settings

app = FastAPI(
    title='Echo Backend',
    description='API for the Echo public figure position intelligence engine.',
    version='0.1.0'
)

app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(public_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=f'{settings.API_V1_PREFIX}/admin')
