"""Compilation and validation system for generated frontends."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Tuple

from ai_frontend.config import AiFrontendConfig
from ai_frontend.utils import run_command

logger = logging.getLogger(__name__)


class FrontendCompiler:
    """Compile and validate generated React frontends."""

    def __init__(self, config: AiFrontendConfig):
        self._config = config

    async def compile_and_validate(self, project_dir: Path) -> Tuple[bool, Optional[str]]:
        """Compile the frontend and validate it builds successfully.

        Args:
            project_dir: Root directory of the React project

        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Compiling frontend in {project_dir}")

        # Check if package.json exists
        if not (project_dir / "package.json").exists():
            return False, "No package.json found - frontend not initialized"

        # Install dependencies if node_modules doesn't exist
        if not (project_dir / "node_modules").exists():
            logger.info("Installing dependencies...")
            success, error = await self._install_dependencies(project_dir)
            if not success:
                return False, f"Failed to install dependencies: {error}"

        # Run TypeScript type checking
        logger.info("Running TypeScript type check...")
        success, error = await self._run_type_check(project_dir)
        if not success:
            return False, f"TypeScript errors: {error}"

        # Run build
        logger.info("Building frontend...")
        success, error = await self._run_build(project_dir)
        if not success:
            return False, f"Build failed: {error}"

        # Verify build output exists
        if not (project_dir / "dist").exists():
            return False, "Build succeeded but no dist directory created"

        logger.info("Frontend compiled successfully")
        return True, None

    async def _install_dependencies(self, project_dir: Path) -> Tuple[bool, Optional[str]]:
        """Install npm dependencies."""
        try:
            exit_code, stdout, stderr = await run_command(
                ["npm", "install"],
                cwd=project_dir,
                timeout=300,  # 5 minute timeout for install
            )

            if exit_code != 0:
                return False, stderr or "npm install failed"

            return True, None

        except Exception as e:
            return False, str(e)

    async def _run_type_check(self, project_dir: Path) -> Tuple[bool, Optional[str]]:
        """Run TypeScript type checking."""
        try:
            exit_code, stdout, stderr = await run_command(
                ["npm", "run", "type-check"],
                cwd=project_dir,
                timeout=60,
            )

            if exit_code != 0:
                # Extract relevant error messages
                errors = self._extract_typescript_errors(stdout + stderr)
                return False, errors

            return True, None

        except Exception as e:
            return False, str(e)

    async def _run_build(self, project_dir: Path) -> Tuple[bool, Optional[str]]:
        """Run the build process."""
        try:
            exit_code, stdout, stderr = await run_command(
                ["npm", "run", "build"],
                cwd=project_dir,
                timeout=180,  # 3 minute timeout for build
            )

            if exit_code != 0:
                return False, stderr or "Build failed"

            return True, None

        except Exception as e:
            return False, str(e)

    def _extract_typescript_errors(self, output: str) -> str:
        """Extract meaningful TypeScript errors from compiler output."""
        lines = output.split("\n")
        error_lines = []
        in_error = False

        for line in lines:
            if "error TS" in line:
                in_error = True
                error_lines.append(line)
            elif in_error and line.strip():
                error_lines.append(line)
            elif in_error and not line.strip():
                in_error = False

        if not error_lines:
            # Return first 10 lines if no specific errors found
            return "\n".join(lines[:10])

        # Return up to 20 error lines
        return "\n".join(error_lines[:20])

    async def validate_development_server(self, project_dir: Path) -> Tuple[bool, Optional[str]]:
        """Validate that the development server can start."""
        logger.info("Validating development server...")

        try:
            # Start dev server
            process = await asyncio.create_subprocess_exec(
                "npm",
                "run",
                "dev",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait a bit for server to start
            try:
                await asyncio.wait_for(asyncio.sleep(5), timeout=5)
            except asyncio.TimeoutError:
                pass

            # Check if process is still running
            if process.returncode is not None:
                stdout, stderr = await process.communicate()
                return False, f"Dev server exited: {stderr.decode()}"

            # Kill the process
            process.terminate()
            await process.wait()

            return True, None

        except Exception as e:
            return False, str(e)
