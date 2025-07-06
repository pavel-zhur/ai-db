"""Core AI-Frontend implementation."""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ai_frontend.api_generator import ApiGenerator
from ai_frontend.claude_integration import ClaudeCodeWrapper
from ai_frontend.compiler import FrontendCompiler
from ai_frontend.config import AiFrontendConfig
from ai_frontend.exceptions import GenerationError, TransactionError
from ai_frontend.skeleton_generator import SkeletonGenerator
from ai_frontend.utils import read_yaml, write_yaml

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of frontend generation operation."""
    
    success: bool
    output_path: Optional[Path] = None
    error: Optional[str] = None
    compiled: bool = False
    iterations_used: int = 0


@dataclass
class TransactionContext:
    """Transaction context from git-layer."""
    
    transaction_id: str
    working_directory: Path
    commit_message_callback: Optional[callable] = None


class AiFrontend:
    """Main AI-Frontend class for generating React frontends."""
    
    def __init__(self, config: AiFrontendConfig):
        self._config = config
        self._claude_wrapper = ClaudeCodeWrapper(config)
        self._skeleton_generator = SkeletonGenerator()
        self._api_generator = ApiGenerator()
        self._compiler = FrontendCompiler(config)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    
    async def generate_frontend(
        self,
        request: str,
        schema: Dict[str, Any],
        transaction_context: TransactionContext,
        project_name: str = "ai-frontend",
    ) -> GenerationResult:
        """Generate a complete frontend based on natural language request.
        
        Args:
            request: Natural language description of the frontend to generate
            schema: AI-DB schema dictionary
            transaction_context: Git-layer transaction context
            project_name: Name for the generated project
            
        Returns:
            GenerationResult with success status and details
        """
        try:
            project_dir = transaction_context.working_directory / "frontend"
            
            # Step 1: Generate React skeleton
            logger.info("Generating React project skeleton...")
            await self._skeleton_generator.generate(
                project_dir,
                project_name,
                self._config.api_base_url,
            )
            
            # Step 2: Generate API layer from schema
            logger.info("Generating API layer from schema...")
            await self._api_generator.generate_api_layer(
                project_dir,
                schema,
                self._config.api_base_url,
            )
            
            # Step 3: Prepare context files for Claude
            context_files = {
                "schema.yaml": await self._prepare_schema_context(schema),
                "api_types.ts": await self._read_generated_types(project_dir),
            }
            
            # Step 4: Generate frontend using Claude Code
            logger.info("Invoking Claude Code to generate frontend...")
            success = await self._claude_wrapper.generate_frontend(
                request,
                project_dir,
                context_files,
            )
            
            if not success:
                return GenerationResult(
                    success=False,
                    error="Claude Code failed to generate frontend after maximum iterations",
                    iterations_used=self._config.max_iterations,
                )
            
            # Step 5: Compile and validate
            logger.info("Compiling and validating generated frontend...")
            compile_success, compile_error = await self._compiler.compile_and_validate(
                project_dir
            )
            
            if not compile_success:
                # Try one more iteration with Claude to fix compilation errors
                logger.info("Compilation failed, asking Claude to fix errors...")
                fix_prompt = f"The frontend compilation failed with errors:\n\n{compile_error}\n\nPlease fix these errors."
                
                fix_success = await self._claude_wrapper.generate_frontend(
                    fix_prompt,
                    project_dir,
                    {"compilation_errors.txt": compile_error or "Unknown error"},
                )
                
                if fix_success:
                    compile_success, compile_error = await self._compiler.compile_and_validate(
                        project_dir
                    )
            
            # Prepare commit message if callback provided
            if transaction_context.commit_message_callback:
                commit_msg = f"Generate frontend: {request[:100]}..."
                transaction_context.commit_message_callback(commit_msg)
            
            return GenerationResult(
                success=compile_success,
                output_path=project_dir if compile_success else None,
                error=compile_error if not compile_success else None,
                compiled=compile_success,
                iterations_used=self._claude_wrapper._iteration_count,
            )
            
        except Exception as e:
            logger.error(f"Frontend generation failed: {e}", exc_info=True)
            return GenerationResult(
                success=False,
                error=str(e),
            )
    
    async def update_frontend(
        self,
        request: str,
        schema: Dict[str, Any],
        transaction_context: TransactionContext,
    ) -> GenerationResult:
        """Update an existing frontend based on natural language request.
        
        Args:
            request: Natural language description of changes to make
            schema: Updated AI-DB schema dictionary
            transaction_context: Git-layer transaction context
            
        Returns:
            GenerationResult with success status and details
        """
        try:
            project_dir = transaction_context.working_directory / "frontend"
            
            if not (project_dir / "package.json").exists():
                return GenerationResult(
                    success=False,
                    error="No existing frontend found to update",
                )
            
            # Regenerate API layer if schema changed
            logger.info("Updating API layer from schema...")
            await self._api_generator.generate_api_layer(
                project_dir,
                schema,
                self._config.api_base_url,
            )
            
            # Prepare context
            context_files = {
                "schema.yaml": await self._prepare_schema_context(schema),
                "api_types.ts": await self._read_generated_types(project_dir),
                "update_request.md": f"# Update Request\n\n{request}",
            }
            
            # Let Claude update the frontend
            logger.info("Invoking Claude Code to update frontend...")
            success = await self._claude_wrapper.generate_frontend(
                f"Update the existing frontend: {request}",
                project_dir,
                context_files,
            )
            
            if not success:
                return GenerationResult(
                    success=False,
                    error="Claude Code failed to update frontend",
                )
            
            # Compile and validate
            compile_success, compile_error = await self._compiler.compile_and_validate(
                project_dir
            )
            
            # Prepare commit message
            if transaction_context.commit_message_callback:
                commit_msg = f"Update frontend: {request[:100]}..."
                transaction_context.commit_message_callback(commit_msg)
            
            return GenerationResult(
                success=compile_success,
                output_path=project_dir if compile_success else None,
                error=compile_error if not compile_success else None,
                compiled=compile_success,
            )
            
        except Exception as e:
            logger.error(f"Frontend update failed: {e}", exc_info=True)
            return GenerationResult(
                success=False,
                error=str(e),
            )
    
    async def _prepare_schema_context(self, schema: Dict[str, Any]) -> str:
        """Prepare schema context for Claude."""
        import yaml
        
        # Add descriptions and context to schema
        enhanced_schema = {
            "description": "AI-DB Schema for frontend generation",
            "instructions": "Use this schema to understand the data model and generate appropriate UI components",
            **schema,
        }
        
        return yaml.dump(enhanced_schema, default_flow_style=False)
    
    async def _read_generated_types(self, project_dir: Path) -> str:
        """Read generated TypeScript types."""
        types_file = project_dir / "src/types/api.ts"
        if types_file.exists():
            with open(types_file, "r") as f:
                return f.read()
        return "// No types generated yet"