"""Main entry point for AI-Hub."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Config

# Create FastAPI app
app = FastAPI(
    title="AI-Hub",
    description="HTTP API server for AI-DB frontend communication",
    version="0.1.0",
)

# Load configuration
config = Config()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI-Hub API Server"}


def main():
    """Main entry point for running the server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()