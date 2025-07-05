# MCP Server Technical Q&A

## General Architecture Questions

**Q: Should the MCP server be a single server exposing both AI-DB and AI-Frontend tools, or should they be separate servers?**
A: separate

**Q: What should be the package/module structure? Should ai-db and ai-frontend be imported as dependencies, or should the MCP server be part of a monorepo with shared code?**
A: you're already a part of a monorepo :) but import as dependencies!

**Q: Should the server maintain any state between tool calls, or should each tool call be completely stateless?**
A: whta do you think is best frmo the mcp point of view? mcp best practices? and our workflow. please google about mcp best practices and real life scenarios to know more. but generally it's not a2a, it's mcp. probably you can be simpler.

## AI-DB Tool Questions

**Q: For AI-DB operations, should we expose one unified tool that handles all operation types (schema_modify, data_modify, select, view_modify) or separate tools for each operation type?**
A: whats better in your opinion? i think different tools

**Q: How should we handle the permission levels? Should the MCP client specify them, or should we infer them from the operation?**
A: infer

**Q: For compiled query plans, should we expose a separate tool to execute pre-compiled plans, or is that out of scope for MCP?**
A: we should

**Q: Should transaction operations (BEGIN, COMMIT, ROLLBACK) be exposed as separate MCP tools or handled differently?**
A: i don't know. i think lets do. lets do transactions. but optional, if the client wants to call an atomic operations once, you should support it.

**Q: How should we handle the context/session state that the console maintains? Should MCP tools support some form of context passing?**
A: ummm console? you don't care about console. session.. .for transactions - yes. use best practices for mcp and common sense.

## AI-Frontend Tool Questions

**Q: Should frontend generation be a single tool or split into create_component, modify_component, create_page, etc.?**
A: a single tool of course, because it's the ai inside the ai-frontend who will decide what to do. you don't call ai models. and the queries are plaintext.

**Q: How should we pass the AI-DB schema context to AI-Frontend operations through MCP?**
A: you don't, you either call ai-db or ai-frontend, and from the config ai-frontend knows how to reach the db if it needs to

**Q: Should the MCP server directly invoke Claude Code CLI, or should ai-frontend library handle that?**
A: ai-frontend library will

**Q: For visual context features (Chrome integration, pointing gestures), how should these be handled in MCP context?**
A: it's not what you handle, it's irrelevant to you at all

## Implementation Details

**Q: What Python version should we target?**
A: 3.13.5

**Q: Should we use the official MCP Python SDK, or implement the protocol directly?**
A: research best practices. what's most stable, industry standard, and really good and doesnt have limitations and really suits us. i think sdk is better, but you can decide

**Q: How should we handle errors from ai-db/ai-frontend libraries? Should we wrap them in MCP error responses or let them propagate?**
A: whats best practice

**Q: Should the server support multiple concurrent operations, or enforce single-threaded operation as mentioned in the requirements?**
A: concurrent is ok

**Q: What logging framework should we use, and what should be logged?**
A: whats best practice

## Configuration Questions

**Q: Should the MCP server have any configuration file, or should everything be convention-based?**
A: whats best practice and makes most sense for our scenario

**Q: How should we handle the working directory for file operations? Should it be configurable or use the current working directory?**
A: it's not you, it's git-layer, it's irrelevant

**Q: Should there be any authentication or authorization at the MCP level?**
A: no, not in the poc

## Testing Questions

**Q: What testing approach should we use? Unit tests, integration tests, or both?**
A: for the mcp server per se - both

**Q: Should we create mock implementations of ai-db and ai-frontend for testing?**
A: yes

**Q: How should we test the stdio transport communication?**
A: stdio? hmm. stdio? you sure it's needed? maybe its something i don't know about in mcp. whats best practice

## Deployment Questions

**Q: How should the MCP server be packaged? As a standalone executable, Python package, or Docker container?**
A: whats best practice
btw we'll use docker for other components, but whats best practice

**Q: Should we provide any CLI arguments for the server startup?**
A: whats best practice and what makes most sense. libs will use configs, but whats best practice. you're an executable using those libs. whats best practice

**Q: What should be the entry point name for the stdio server?**
A: sorry I don't understand the question

## Error Handling Questions

**Q: How should we handle validation errors from ai-db (e.g., constraint violations)?**
A: the mcp should return an error, whats best practice

**Q: What should happen if ai-db or ai-frontend libraries are not installed?**
A: you shouldn't start. you call those libs, you import them

**Q: How should we handle Git-related errors from the git-layer?**
A: the mcp should return an error, whats best practice

## Additional Questions

**Q: Are there any specific MCP features we should use (like progress reporting, resource URIs, etc.)?**
A: not in the poc, but use something if it's available and you think it makes sense and easy to do

**Q: Should we implement any MCP prompts for user confirmation of destructive operations?**
A: whats best practice

**Q: Do we need to support any specific MCP client features or limitations?**
A: whats best practice, probably not

**Q: Should the MCP server provide any introspection tools (list schemas, list components, etc.)?**
A: schemas for sure. getting semantic descriptions of the database and of the frontend yes also for sure. bascially provide everything, full info and full control

**Q: How should long-running operations (like complex schema migrations) be handled?**
A: I think for you it's just an ordinary long running operation, when it finishes - you return the result