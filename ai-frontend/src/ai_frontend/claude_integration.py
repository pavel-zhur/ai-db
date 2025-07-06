"""Claude Code CLI integration."""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional

from ai_frontend.config import AiFrontendConfig
from ai_frontend.exceptions import ClaudeCodeError
from ai_frontend.utils import write_file

logger = logging.getLogger(__name__)


class ClaudeCodeWrapper:
    """Wrapper for Claude Code CLI operations."""

    def __init__(self, config: AiFrontendConfig):
        self._config = config
        self._iteration_count = 0

    async def generate_frontend(
        self,
        prompt: str,
        working_dir: Path,
        context_files: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Generate frontend using Claude Code CLI.

        Args:
            prompt: Natural language description of what to generate
            working_dir: Directory to generate frontend in
            context_files: Additional context files to provide to Claude

        Returns:
            True if generation succeeded, False otherwise
        """
        self._iteration_count = 0

        # Prepare context files if provided
        if context_files:
            context_dir = working_dir / ".claude_context"
            context_dir.mkdir(exist_ok=True)

            for filename, content in context_files.items():
                await write_file(context_dir / filename, content)

        # Build the full prompt with instructions
        full_prompt = self._build_prompt(prompt, working_dir, context_files)

        # Create a temporary file for the prompt to avoid command line length limits
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(full_prompt)
            prompt_file = f.name

        try:
            success = await self._run_claude_iteration(prompt_file, working_dir)

            # Run multiple iterations if needed
            while not success and self._iteration_count < self._config.max_iterations:
                logger.info(
                    f"Running iteration {self._iteration_count + 1}/{self._config.max_iterations}"
                )

                # Create follow-up prompt
                follow_up = self._create_follow_up_prompt()
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".md", delete=False, encoding="utf-8"
                ) as f:
                    f.write(follow_up)
                    follow_up_file = f.name

                try:
                    success = await self._run_claude_iteration(follow_up_file, working_dir)
                finally:
                    os.unlink(follow_up_file)

            return success

        finally:
            os.unlink(prompt_file)
            # Clean up context directory
            if context_files and (context_dir := working_dir / ".claude_context").exists():
                import shutil

                shutil.rmtree(context_dir)

    def _build_prompt(
        self,
        user_prompt: str,
        working_dir: Path,
        context_files: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build the full prompt for Claude Code."""
        prompt_parts = [
            "# Frontend Generation Task",
            "",
            "## Environment",
            f"You are generating a React frontend in the directory: {working_dir}",
            "The frontend should:",
            "- Use React with TypeScript",
            "- Use Material-UI for components",
            "- Use Vite as the build tool",
            "- Generate static files (no server-side rendering)",
            "- Include proper error handling and loading states",
            "- Be fully self-contained with all dependencies",
            "",
        ]

        if context_files:
            prompt_parts.extend(
                ["## Context Files", "The following files provide context for the generation:", ""]
            )

            for filename in context_files:
                context_path = working_dir / ".claude_context" / filename
                prompt_parts.append(f"- {context_path}: {filename}")

            prompt_parts.extend(
                ["", "Please read these files to understand the schema and requirements.", ""]
            )

        prompt_parts.extend(
            [
                "## User Request",
                user_prompt,
                "",
                "## Requirements",
                "1. Create a complete, working React application",
                "2. Ensure all TypeScript types are properly defined",
                "3. Create an API client that communicates with the AI-DB backend",
                "4. Use async/await for all API calls with proper error handling",
                "5. Implement retry logic for failed API requests",
                "6. Create a clean, intuitive user interface",
                "7. Ensure the application compiles without errors",
                "8. Generate a semantic documentation file explaining the frontend structure",
                "",
                "## Final Steps",
                "After generating all components:",
                "1. Run `npm install` to install dependencies",
                "2. Run `npm run build` to ensure everything compiles",
                "3. Fix any compilation errors",
                "4. Create a SEMANTIC_DOCS.md file explaining the frontend architecture",
                "",
                "Please proceed with the implementation.",
            ]
        )

        return "\n".join(prompt_parts)

    def _create_follow_up_prompt(self) -> str:
        """Create a follow-up prompt for Claude to continue working."""
        return "\n".join(
            [
                "# Continue Frontend Development",
                "",
                "Please continue working on the frontend:",
                "1. Check if the build is successful by running `npm run build`",
                "2. Fix any TypeScript or build errors",
                "3. Ensure all components are properly typed",
                "4. Verify the API client is correctly implemented",
                "5. Complete any unfinished components",
                "",
                "If everything compiles successfully and the frontend is complete, ",
                "create or update the SEMANTIC_DOCS.md file with the final architecture.",
            ]
        )

    async def _run_claude_iteration(self, prompt_file: str, working_dir: Path) -> bool:
        """Run a single Claude Code iteration."""
        self._iteration_count += 1

        # Use Docker to run Claude Code
        abs_working_dir = working_dir.resolve()
        abs_prompt_file = Path(prompt_file).resolve()

        cmd = [
            "docker",
            "run",
            "--rm",  # Remove container after exit
            "-v",
            f"{abs_working_dir}:/workspace",  # Mount working directory
            "-v",
            f"{abs_prompt_file}:/prompt.md:ro",  # Mount prompt file as read-only
            "-w",
            "/workspace",  # Set working directory in container
            "--env",
            "ANTHROPIC_API_KEY",  # Pass through API key
        ]

        # Add any additional env vars
        env_vars = self._config.to_env_vars()
        for key, value in env_vars.items():
            cmd.extend(["--env", f"{key}={value}"])

        # Add the Docker image and Claude command
        cmd.extend(
            [
                self._config.claude_code_docker_image,
                "claude",
                "/prompt.md",
                "--no-interactive",
            ]
        )

        env = os.environ.copy()

        # Create a task for the command and one for progress updates
        async def run_with_progress() -> tuple[str, str]:
            # Start the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            # Progress feedback task
            async def print_progress() -> None:
                start_time = time.time()
                while True:
                    await asyncio.sleep(self._config.progress_interval_seconds)
                    elapsed = int(time.time() - start_time)
                    logger.info(f"Still working... ({elapsed}s elapsed)")
                    print(f"Still working... ({elapsed}s elapsed)")

            progress_task = asyncio.create_task(print_progress())

            try:
                # Wait for the command to complete
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self._config.timeout_seconds
                )
                exit_code = process.returncode

                stdout_text = stdout.decode("utf-8", errors="replace")
                stderr_text = stderr.decode("utf-8", errors="replace")

                if self._config.log_claude_output:
                    logger.info(f"Claude output:\n{stdout_text}")
                    if stderr_text:
                        logger.warning(f"Claude stderr:\n{stderr_text}")

                if exit_code != 0:
                    raise ClaudeCodeError(
                        f"Claude Code exited with code {exit_code}: {stderr_text}"
                    )

                return stdout_text, stderr_text

            finally:
                # Cancel progress task
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass

        try:
            stdout, stderr = await run_with_progress()

            # Check if build was successful
            return await self._check_build_success(working_dir)

        except asyncio.TimeoutError:
            raise ClaudeCodeError(
                f"Claude Code timed out after {self._config.timeout_seconds} seconds"
            )
        except Exception as e:
            raise ClaudeCodeError(f"Failed to run Claude Code: {e}")

    async def _check_build_success(self, working_dir: Path) -> bool:
        """Check if the frontend builds successfully."""
        package_json = working_dir / "package.json"

        if not package_json.exists():
            logger.warning("No package.json found, frontend not yet initialized")
            return False

        # Check if SEMANTIC_DOCS.md exists as a completion indicator
        semantic_docs = working_dir / "SEMANTIC_DOCS.md"
        if not semantic_docs.exists():
            logger.info("SEMANTIC_DOCS.md not found, frontend not complete")
            return False

        logger.info("Frontend generation appears complete")
        return True
