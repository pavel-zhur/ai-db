#!/usr/bin/env python3
"""Basic usage example for git-layer."""

import git_layer
from pathlib import Path


def main():
    """Demonstrate basic git-layer usage."""
    repo_path = "/tmp/git-layer-example"
    
    print(f"Using repository at: {repo_path}")
    
    # Example 1: Simple write transaction
    print("\n1. Simple write transaction:")
    with git_layer.begin(repo_path, message="Add user data") as txn:
        print(f"   Transaction ID: {txn.transaction_id}")
        
        # Signal that we're about to write
        txn.write_escalation_required()
        print(f"   Working in: {txn.path}")
        
        # Write a file
        users_file = Path(txn.path) / "users.yaml"
        users_file.write_text("""users:
  - id: 1
    name: Alice
    email: alice@example.com
  - id: 2
    name: Bob
    email: bob@example.com
""")
        print("   Created users.yaml")
    
    print("   Transaction committed!")
    
    # Example 2: Transaction with multiple operations
    print("\n2. Transaction with multiple operations:")
    with git_layer.begin(repo_path, message="Add products and update users") as txn:
        txn.write_escalation_required()
        
        # Add products
        products_file = Path(txn.path) / "products.yaml"
        products_file.write_text("""products:
  - id: 1
    name: Widget
    price: 19.99
  - id: 2
    name: Gadget
    price: 29.99
""")
        print("   Added products.yaml")
        
        # Create checkpoint
        txn.checkpoint("Added products")
        
        # Update users
        users_file = Path(txn.path) / "users.yaml"
        content = users_file.read_text()
        content += """  - id: 3
    name: Charlie
    email: charlie@example.com
"""
        users_file.write_text(content)
        print("   Updated users.yaml")
        
        # Another checkpoint
        txn.checkpoint("Added Charlie")
    
    print("   Transaction committed!")
    
    # Example 3: Failed transaction (rollback)
    print("\n3. Failed transaction (will rollback):")
    try:
        with git_layer.begin(repo_path, message="This will fail") as txn:
            txn.write_escalation_required()
            
            # Write some data
            temp_file = Path(txn.path) / "temporary.txt"
            temp_file.write_text("This will be rolled back")
            print("   Created temporary.txt")
            
            # Simulate an error
            raise ValueError("Simulated error!")
            
    except ValueError as e:
        print(f"   Transaction failed: {e}")
        print("   Changes rolled back!")
    
    # Verify the file doesn't exist
    if not (Path(repo_path) / "temporary.txt").exists():
        print("   Confirmed: temporary.txt was not committed")
    
    # Example 4: Read-only transaction
    print("\n4. Read-only transaction:")
    with git_layer.begin(repo_path, message="Read data") as txn:
        # Don't call write_escalation_required()
        
        users_file = Path(txn.path) / "users.yaml"
        if users_file.exists():
            lines = users_file.read_text().count('\n')
            print(f"   Users file has {lines} lines")
        
        products_file = Path(txn.path) / "products.yaml"
        if products_file.exists():
            lines = products_file.read_text().count('\n')
            print(f"   Products file has {lines} lines")
    
    print("\nExample complete!")


if __name__ == "__main__":
    main()