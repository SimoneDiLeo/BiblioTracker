from fastapi import FastAPI

# Importing database initialization function and router
from database.database_setup import init_db
from api import auth_routes # Assuming your router is named 'router' in auth_routes.py

app = FastAPI()

# Event handler for application startup
@app.on_event("startup")
async def startup_event():
    init_db() # Create database tables

# Include the authentication routes
app.include_router(auth_routes.router, prefix="/api", tags=["Authentication"]) # Added a prefix for API versioning

# Importing and including the researcher routes
from api import researcher_routes
app.include_router(researcher_routes.router, prefix="/api/researchers", tags=["Researchers"])

# Importing and including the OpenAlex routes
from api import openalex_routes # New import
app.include_router(openalex_routes.openalex_router) # Default prefix from the router itself (/api/openalex)

# Importing and including the Bibliometric routes
from api import bibliometric_routes # New import
app.include_router(bibliometric_routes.bibliometric_router) # Default prefix from the router itself (/api/bibliometrics)

# Importing and including the Collaboration routes
from api import collaboration_routes # New import
app.include_router(collaboration_routes.collaboration_router) # Default prefix from the router itself (/api/collaborations)

# Importing and including the Analysis routes
from api import analysis_routes # New import
app.include_router(analysis_routes.analysis_router) # Default prefix from the router itself (/api/analysis)

@app.get("/")
async def root():
    return {"message": "Welcome to the Research Information System API"}
