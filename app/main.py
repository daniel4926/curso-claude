from fastapi import FastAPI

from app.routers import projects

app = FastAPI()
app.include_router(projects.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
