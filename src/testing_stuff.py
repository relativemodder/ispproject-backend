from fastapi.routing import APIRouter


testing_router = APIRouter(
    prefix="/testing",
    tags=["Testing"]
)


@testing_router.get("/available")
async def get_is_service_available():
    return {"is_available": True}