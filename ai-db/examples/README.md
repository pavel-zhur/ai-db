# AI-DB Examples

This directory contains examples demonstrating how to use AI-DB.

## Basic Usage

```python
import asyncio
from ai_db import AIDB, PermissionLevel
from git_layer import GitTransaction  # Assuming git-layer provides this

async def main():
    # Create a git transaction
    async with GitTransaction() as transaction:
        db = AIDB()
        
        # Create a table using natural language
        result = await db.execute(
            "Create a customers table with id (primary key), name, email (unique), and created_at timestamp",
            permissions=PermissionLevel.SCHEMA_MODIFY,
            transaction=transaction
        )
        print(f"Table created: {result.status}")
        
        # Insert data
        result = await db.execute(
            "Add customer John Doe with email john@example.com",
            permissions=PermissionLevel.DATA_MODIFY,
            transaction=transaction
        )
        print(f"Data inserted: {result.status}")
        
        # Query data
        result = await db.execute(
            "Show all customers ordered by name",
            permissions=PermissionLevel.SELECT,
            transaction=transaction
        )
        print(f"Customers: {result.data}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Using SQL

AI-DB understands SQL as well:

```python
async def sql_example():
    async with GitTransaction() as transaction:
        db = AIDB()
        
        # SQL CREATE TABLE
        await db.execute(
            """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) CHECK (price > 0),
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
            """,
            permissions=PermissionLevel.SCHEMA_MODIFY,
            transaction=transaction
        )
        
        # SQL INSERT
        await db.execute(
            "INSERT INTO products (id, name, price, category_id) VALUES (1, 'Widget', 9.99, 1)",
            permissions=PermissionLevel.DATA_MODIFY,
            transaction=transaction
        )
        
        # SQL SELECT with JOIN
        result = await db.execute(
            """
            SELECT p.name, p.price, c.name as category
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.price < 20
            """,
            permissions=PermissionLevel.SELECT,
            transaction=transaction
        )
```

## Compiled Queries

For performance-critical queries, compile them once and reuse:

```python
async def compiled_query_example():
    async with GitTransaction() as transaction:
        db = AIDB()
        
        # First execution compiles the query
        result = await db.execute(
            "SELECT * FROM users WHERE is_active = true ORDER BY created_at DESC",
            permissions=PermissionLevel.SELECT,
            transaction=transaction
        )
        
        # Save the compiled plan
        compiled_plan = result.compiled_plan
        
        # Later, execute the compiled plan directly (no AI processing)
        result = db.execute_compiled(compiled_plan, transaction)
        print(f"Active users: {result.data}")
```

## Complex Constraints

```python
async def constraints_example():
    async with GitTransaction() as transaction:
        db = AIDB()
        
        # Create table with complex constraints
        await db.execute(
            """
            Create an orders table with:
            - id (primary key)
            - user_id (foreign key to users.id)
            - product_id (foreign key to products.id)
            - quantity (must be positive)
            - total_price (must be positive)
            - status (must be one of: pending, processing, shipped, delivered)
            - created_at timestamp
            
            Ensure that the same user can't order the same product twice in pending status
            """,
            permissions=PermissionLevel.SCHEMA_MODIFY,
            transaction=transaction
        )
```

## View Creation

```python
async def view_example():
    async with GitTransaction() as transaction:
        db = AIDB()
        
        # Create a view using natural language
        result = await db.execute(
            """
            Create a view called 'customer_order_summary' that shows:
            - Customer name
            - Total number of orders
            - Total amount spent
            - Average order value
            - Last order date
            Group by customer and only include customers with at least one order
            """,
            permissions=PermissionLevel.VIEW_MODIFY,
            transaction=transaction
        )
        
        # The view is compiled to Python and can be queried
        result = await db.execute(
            "SELECT * FROM customer_order_summary WHERE total_spent > 1000",
            permissions=PermissionLevel.SELECT,
            transaction=transaction
        )
```

## Error Handling

```python
async def error_handling_example():
    async with GitTransaction() as transaction:
        db = AIDB()
        
        # Permission error
        result = await db.execute(
            "DROP TABLE users",  # Requires SCHEMA_MODIFY
            permissions=PermissionLevel.SELECT,  # Wrong permission
            transaction=transaction
        )
        if not result.status:
            print(f"Error: {result.error}")
        
        # Constraint violation (AI will try to fix automatically)
        result = await db.execute(
            "Insert user with id 1 (duplicate)",  # If id 1 exists
            permissions=PermissionLevel.DATA_MODIFY,
            transaction=transaction
        )
        print(f"AI handled constraint: {result.ai_comment}")
```

## Using Different Languages

AI-DB understands queries in various programming languages:

```python
async def multi_language_example():
    async with GitTransaction() as transaction:
        db = AIDB()
        
        # C# LINQ style
        result = await db.execute(
            """
            from user in users
            where user.IsActive && user.Age >= 18
            orderby user.Name
            select new { user.Name, user.Email }
            """,
            permissions=PermissionLevel.SELECT,
            transaction=transaction
        )
        
        # Python style
        result = await db.execute(
            "[u for u in users if u['is_active'] and u['age'] >= 18]",
            permissions=PermissionLevel.SELECT,
            transaction=transaction
        )
        
        # Natural language
        result = await db.execute(
            "Find all adult active users and show their names and emails sorted alphabetically",
            permissions=PermissionLevel.SELECT,
            transaction=transaction
        )
```