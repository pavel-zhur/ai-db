# AI-DB Technical Q&A

## Architecture & Design

### Core Engine
1. **AI Model Integration**: How should the AI model be integrated? Should I use a specific API (OpenAI, Anthropic, etc.) or design it to be pluggable with different providers?
any openai-compatible api. it should be a bit agentic, you may use langchain or langgraph if you wish, but please be very simple. use only best practices. bascially ai decides what kind of operation that is, what kind of elevation is needed and is it provided byt he permissions supplied, decides if there's python to create (if it's a select or a view creation), or if it's some kind of modification - it just reads files and returns full new updated files content for now. then there's python validation (data to schema integrity etc).

2. **Query Processing Pipeline**: What's the exact flow from natural language input to execution? Should there be intermediate representations?
probably no. basically ai either updates files or returns some kind of error or generates python for views. that should cover most of the requirements. roughly. you'll need to think.

3. **Error Recovery**: When the AI makes mistakes interpreting queries, how should the recovery mechanism work? Should it retry with different prompts or fail fast?
a few attempts. ai should decide to return an error or to keep trying. hard iterations limit specified in the configs.

4. **AI Context Management**: How much context should be passed to the AI for each operation? Should it include schema history, recent operations, or just current state?
you decide! think which contexts there will be. including semantic docs etc.

## Data Storage

### YAML Structure
5. **File Organization**: How should tables be organized in the filesystem? One file per table? Directory structure?
decide whats better

6. **Primary Keys**: How should primary keys be handled in YAML? As part of the data or separate?
in yaml of course

7. **Indexes**: Should we support indexes? If so, how are they stored and maintained?
no

8. **Large Tables**: What's the strategy for tables with millions of rows? Pagination in files? Partitioning?
no millions of rows. dont think about size, size will be small

### Schema Storage
9. **Schema Format**: What exact YAML structure for schemas? Should it mirror standard SQL DDL concepts?
probably

10. **Schema Evolution**: How are schema migrations tracked? Do we keep a history of all schema versions?
git will. the git library. for the ai-db, there's only current state. which is in the file system. in a location provided by the git library (whether that's a cloned copy or anything - it'll decide). git library will probably need to know if there's a write escalation.

11. **Schema Documentation**: Where is the AI-generated documentation stored? Inline in schema files or separate?
you decide whats better given the high level picture and the use cases and important factors

## Query Compilation

### Python Generation
12. **Code Generation Strategy**: Should queries compile to pure Python functions or use a query execution framework?
pure python

13. **Performance Optimization**: What level of query optimization should the AI attempt? Join order optimization? Index usage?
up to ai

14. **Compiled Query Storage**: Where are compiled queries cached? In memory? On disk?
views - on disk, they're part of db. selects - returned as a serialized string, not stored. a separate method accepts them deserializes and executes without ai.

15. **Invalidation**: When do compiled queries need to be invalidated and recompiled?
the library shouldnt worry. it's the lib user responsiblity to forget them when schema changed. no longer valid queries will naturally return an error, or execute and return a wrong result, or correct result, it's fine.

## Constraints & Validation

### Implementation
16. **Constraint Functions**: Should constraint validation functions be stored as Python files or embedded in YAML?
up to you

17. **Foreign Key Checking**: When are foreign keys validated? On every write or batch validation?
after every execution, before that execution is stored to disk. in the middle, ai may decide it needs to fix something if validation returns errors

18. **Check Constraints**: What Python features are allowed in check constraints? Full Python or a subset?
somehow it needs to be executed safely. whats best practice

19. **Validation Timing**: Should validation happen before writing to disk or after (with rollback)?
before. data integrity checks, guarantee written data is good

## Transaction Support

### Git-Layer Integration
20. **Transaction Isolation**: Since we're single-threaded, do we need any isolation between read and write operations within a transaction?
no

21. **Transaction State**: How is transaction state passed between ai-db and git-layer? Context object? Global state?
whats best best practices given architecture, python, modularity, etc

22. **Partial Commits**: Can transactions be partially committed (some tables but not others)?
no

23. **Transaction Metadata**: Should we store metadata about each transaction (timestamp, description)?
git will

## API Design

### Public Interface
24. **Method Signatures**: Should the main execute method take typed objects or just strings? What about the response?
generally, make typed parameters. string query, enum permissions, etc. generally all python best best practices for production-ready code

25. **Async Support**: Should operations be async/await compatible for future use cases?
yes

26. **Batch Operations**: Should there be special handling for bulk inserts/updates?
no

27. **Connection Model**: Is there a connection/session object or are operations stateless?
i think you'll accept a mandatory git transaction parameter. it'll be wrapped in the with statement by the user. git lib will take care. you'll get the location, an interface to call the write escalation on (git may decide to move you to a temp folder, you'll get a folder update in return), etc

## Performance & Limits

### Practical Considerations
28. **AI Token Limits**: How should we handle queries that might exceed AI context limits?
dont worry about it

29. **Memory Management**: For large result sets, should we stream results or load everything into memory?
memory

30. **Query Timeout**: Should there be timeouts for AI interpretation or query execution?
standard, configurable, approach. best practices for a library

31. **Caching Strategy**: What should be cached? Schema? Compiled queries? AI responses?
nothing. file persistence or nothing. compiled queries returned to user as strings and they'll cache them

## Error Handling

### Failure Modes
32. **AI Failures**: What happens when the AI service is unavailable or returns invalid responses?
error :)
but generally - execute fully until valid - then store to files.

33. **Data Corruption**: How do we detect and handle corrupted YAML files?
raise an error

34. **Constraint Violations**: What information should be included in constraint violation errors?
since it's python-validated, preferably include info useful for the ai model to remediate

35. **Transaction Conflicts**: Even though single-threaded, how do we handle git merge conflicts if they occur?
we dooont. they'll never occur

## Testing & Validation

### Quality Assurance
36. **AI Response Validation**: How do we validate that AI-generated Python code is safe to execute?
what are best practices? if no best practices or too hard to do, dont validate that, allow it to execute. in the poc.

37. **Sandboxing**: Should AI-generated code run in a restricted environment?
not sure how easy it is in python. should only go with easy options, or not do it in the poc

38. **Test Data**: Should there be built-in support for test data generation?
no, because ai model natively will, it's a kind of a query, you don't need to worry

39. **Benchmarking**: Should the library include performance benchmarking capabilities?
no

## Integration Points

### External Systems
40. **Import/Export**: Should there be built-in support for importing from/exporting to standard formats (CSV, JSON, SQL)?
import from - no, because ai natively will, you dont need to worry
export - no, return native python objects (dicts, lists, etc) as results
basically the cell types may be dict, list... it's a schema, right. whatever it allows. lets support what and only what is supported by the.. whats most popular? json schemas? standard? lets do standard json schemas, best practice. well known. but store only in yaml.

41. **Schema Inference**: Can the AI infer schema from existing data files?
no

42. **Migration Tools**: Should there be tools to migrate from traditional databases?
no, ai natively will

43. **Monitoring**: What metrics/logs should the library expose for monitoring?
metrics - probably ai usage, good to be. or maybe it's built in the openai api? then none. but there needs to be an option for the user to configure it. logs - well, pretty much good .info logs. standard.

## Advanced Features

### Future Considerations
44. **Views**: How are views stored? As Python functions? As query strings?
python. and the database semantical meaning will always be included in the semantical meanings file. because that file will describe the db schema, including the views.

45. **Triggers**: Should we support triggers? How would they be implemented?
no.

46. **Computed Columns**: Should we support computed/virtual columns?
no.

47. **Full-Text Search**: Any special handling for text search capabilities?
no.

## Security

### Safety Measures
48. **Code Injection**: How do we prevent malicious code injection through AI prompts?
either by python safe execution contexts if its easy to do, or we dont

49. **File System Access**: Should AI-generated code have restricted file system access?
preferably, if easy to do

50. **Secrets Management**: How should sensitive data (like connection strings in imports) be handled?
dont worry

Please provide answers to these questions so I can implement ai-db according to your vision and requirements.