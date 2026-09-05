from fastapi import FastAPI

from app.routers import projects, tasks

app = FastAPI()
app.include_router(projects.router)
app.include_router(tasks.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
