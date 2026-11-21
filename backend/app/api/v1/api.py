from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, clients, projects, scope_items, tasks, requests, lessons

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(scope_items.router, prefix="/scope-items", tags=["Scope Items"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["Lessons"])
