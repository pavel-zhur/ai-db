"""Example using ai-frontend with git-layer for transaction support."""

import asyncio
from pathlib import Path

# These would be imported from the actual packages
# from git_layer import GitLayer, GitTransaction
# from ai_frontend import AiFrontend, AiFrontendConfig
# from ai_frontend.core import TransactionContext


async def main():
    """Example showing integration with git-layer for transactions."""
    
    # This is pseudocode showing how it would work with git-layer
    """
    # Initialize git-layer
    git = GitLayer(repo_path="/path/to/repo")
    
    # Initialize ai-frontend
    config = AiFrontendConfig(
        claude_code_path="claude",
        max_iterations=5,
    )
    frontend = AiFrontend(config)
    
    # Start a transaction
    async with git.begin_transaction() as transaction:
        # Create transaction context for ai-frontend
        context = TransactionContext(
            transaction_id=transaction.id,
            working_directory=transaction.working_directory,
            commit_message_callback=transaction.set_commit_message,
        )
        
        # Generate frontend
        result = await frontend.generate_frontend(
            request="Create a customer relationship management dashboard",
            schema=crm_schema,
            transaction_context=context,
        )
        
        if result.success:
            # Transaction will be committed when exiting the context
            print("Frontend generated successfully")
        else:
            # Transaction will be rolled back
            raise Exception(f"Frontend generation failed: {result.error}")
    """
    
    print("This example shows how ai-frontend would integrate with git-layer")
    print("See the source code for the integration pattern")


if __name__ == "__main__":
    asyncio.run(main())