from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from routers.orders import router as orders_router
from routers.users import router as users_router
from routers.installers import router as installers_router
from db import Database
from auth import router as auth_router

app = FastAPI()

# Add CORS middleware to allow connections from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and create tables
db = Database()
db.create_tables()

app.include_router(auth_router)
app.include_router(orders_router)

app.include_router(users_router)
app.include_router(installers_router)


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse("/docs")

