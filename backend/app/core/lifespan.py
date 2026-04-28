from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.startup import initialize_container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown hook.
    Initializes reusable singletons once per container instance.
    """
    app.state.container = initialize_container()
    yield
    app.state.container.cache.clear()
