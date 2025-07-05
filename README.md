# AI-DB: An AI-Native Database and AI-Generated Frontend

## What is this?

AI-DB is a database where AI is the database engine itself, not just a translation layer. It also includes AI-generated frontends for analytics and data management.

You can communicate with it using natural language, SQL, or any programming language - C#, TypeScript, Python, anything. The AI interprets your intent and executes the appropriate operations.

## How it works

Traditional databases with AI:
```
You → SQL → Database → Results
You → AI → SQL → Database → Results  (adds translation layer)
```

AI-DB:
```
You → AI → Files → Results  (AI directly manipulates data)
```

## Key Features

1. **Any input language** - Natural language, SQL, C#, TypeScript, or any code
2. **AI-managed migrations** - Schema changes through conversation
3. **Git as storage layer** - Version control built-in
4. **Git as transaction engine** - Branches provide ACID properties
5. **Query compilation** - Queries that return data compile to Python for performance
6. **Safety features** - Permission levels and data loss indicators
7. **Constraints** - Foreign keys and check constraints with strict AI-generated Python validation
8. **Session context** - Console remembers previous queries and operations

## Components

- **ai-db**: Core database engine
- **console**: Interactive chat interface
- **mcp**: MCP server for AI tool integration
- **ai-frontend**: AI-managed React UI generation
- **git-layer**: Git-based storage and transaction support

## AI-Generated Frontend

The ai-frontend component allows you to generate and modify React UIs through natural language. Simply describe what you want - dashboards, forms, reports - and AI creates the components. When your data schema changes, tell AI to update the UI accordingly. The generated frontend automatically understands your data structure and includes proper TypeScript types.

Features include:
- Voice input and pointing gestures for natural interaction
- Automatic accessibility compliance and responsive design
- Chrome integration for visual context during generation
- Documentation generated alongside components

## Storage

Data is stored as YAML files, which means you can:
- Read data directly
- Edit with any text editor
- Use version control
- Understand exactly what's stored

The AI handles queries, constraints, and validations by generating Python code when needed. Data integrity is ensured through constant validation against schemas. All schemas include AI-generated documentation with semantic explanations for better understanding.

## Status

This is a proof of concept exploring how databases might work when AI is the core engine rather than an add-on feature.