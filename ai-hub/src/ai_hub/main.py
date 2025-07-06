"""Main entry point for AI-Hub."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Config
from .endpoints import router
from .exceptions import global_exception_handler
from .service import AIHubService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration
config = Config()

# Create service instance (singleton)
_service_instance: AIHubService | None = None


def get_service_instance() -> AIHubService:
    """Get the singleton service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AIHubService(config)
    return _service_instance


# Create FastAPI app
app = FastAPI(
    title="AI-Hub",
    description="HTTP API server for AI-DB frontend communication",
    version="0.1.0",
)

# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI-Hub API Server",
        "version": "0.1.0",
        "docs": "/docs",
        "git_repo_path": config.git_repo_path,
        "repo_exists": Path(config.git_repo_path).exists()
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    repo_path = Path(config.git_repo_path)
    return {
        "status": "healthy",
        "git_repo_path": config.git_repo_path,
        "repo_exists": repo_path.exists(),
        "repo_is_git": (repo_path / ".git").exists() if repo_path.exists() else False
    }


def main():
    """Main entry point for running the server."""
    import uvicorn

    logger.info(f"Starting AI-Hub server on {config.host}:{config.port}")
    logger.info(f"Git repository path: {config.git_repo_path}")

    # Ensure git repository path exists
    repo_path = Path(config.git_repo_path)
    if not repo_path.exists():
        logger.warning(f"Git repository path does not exist: {config.git_repo_path}")
        logger.info("Creating repository directory...")
        repo_path.mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.aidb_log_level.lower()
    )


if __name__ == "__main__":
    main()
