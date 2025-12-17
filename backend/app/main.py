from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_keys.routes import router as api_keys_router
from .bom_extractor.routes import router as bom_router
from .chat_assistant.routes import router as chat_router
from .database import Base, engine
from .pdf_processing.routes import router as pdf_router
from .requirement_extractor.routes import router as requirement_router

Base.metadata.create_all(bind=engine)


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_keys_router)
app.include_router(pdf_router)
app.include_router(chat_router)
app.include_router(requirement_router)
app.include_router(bom_router)


@app.get("/")
async def root():
    return {"message": f"Welcome to my api"}
