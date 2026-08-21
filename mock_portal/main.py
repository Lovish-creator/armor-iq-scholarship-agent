from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mock_portal.routes import router
from mock_portal.database import init_db

app = FastAPI(
    title="Mock Scholarship Portal API",
    description="Synthetic backend server simulating official scholarship portal endpoints",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mock_portal.main:app", host="127.0.0.1", port=8001, reload=True)
