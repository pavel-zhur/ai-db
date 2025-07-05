# AI-Frontend Deployment Guide

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Claude Code CLI installed and configured
- Git (for git-layer integration)

## Installation

### From Source

```bash
git clone https://github.com/your-org/ai-frontend
cd ai-frontend
pip install -e .
```

### Using pip

```bash
pip install ai-frontend
```

## Docker Deployment

### Building the Docker Image

```bash
docker build -t ai-frontend:latest .
```

### Running with Docker

```bash
docker run -it \
  -v /path/to/workspace:/workspace \
  -v /path/to/git-repo:/repo \
  -e CLAUDE_API_KEY=your-api-key \
  ai-frontend:latest
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  ai-frontend:
    image: ai-frontend:latest
    volumes:
      - ./workspace:/workspace
      - ./repo:/repo
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - API_BASE_URL=http://ai-db:8000
    depends_on:
      - ai-db

  ai-db:
    image: ai-db:latest
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
```

## Configuration

### Environment Variables

- `CLAUDE_CODE_PATH`: Path to Claude Code CLI (default: "claude")
- `API_BASE_URL`: Base URL for AI-DB API (default: "http://localhost:8000")
- `LOG_LEVEL`: Logging level (default: "INFO")

### Configuration File

Create a `config.yaml`:

```yaml
claude_code_path: /usr/local/bin/claude
max_iterations: 5
timeout_seconds: 300
api_base_url: https://api.example.com
enable_chrome_mcp: true
```

## Production Considerations

### Resource Requirements

- **CPU**: 2+ cores recommended for Claude Code execution
- **Memory**: 4GB minimum, 8GB recommended
- **Disk**: 10GB for dependencies and generated code

### Security

1. **API Keys**: Store Claude API keys securely using environment variables or secrets management
2. **Network**: Ensure AI-DB API is accessible only from trusted sources
3. **File System**: Set appropriate permissions on workspace directories

### Monitoring

1. **Logs**: Configure centralized logging for generation operations
2. **Metrics**: Track generation success rates and compilation times
3. **Alerts**: Set up alerts for generation failures

### Scaling

AI-Frontend operations are CPU-intensive but stateless. For scaling:

1. Use a job queue (e.g., Celery) for async generation
2. Deploy multiple workers for parallel generation
3. Use shared storage for git repositories

## Troubleshooting

### Common Issues

1. **Claude Code not found**
   - Ensure Claude Code CLI is installed and in PATH
   - Check `claude_code_path` configuration

2. **Compilation failures**
   - Verify Node.js version (18+)
   - Check npm registry connectivity
   - Review TypeScript errors in logs

3. **Git-layer integration issues**
   - Ensure git repository is accessible
   - Check file permissions in workspace

### Debug Mode

Enable debug logging:

```python
config = AiFrontendConfig(log_level="DEBUG", log_claude_output=True)
```