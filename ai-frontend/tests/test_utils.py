"""Tests for utility functions."""

import pytest

from ai_frontend.utils import (
    extract_code_blocks,
    format_error_message,
    read_file,
    read_json,
    read_yaml,
    run_command,
    sanitize_component_name,
    to_camel_case,
    to_pascal_case,
    write_file,
    write_json,
    write_yaml,
)


@pytest.mark.asyncio
async def test_read_write_file(tmp_path):
    """Test file read and write operations."""
    test_file = tmp_path / "test.txt"
    content = "Hello, World!"

    await write_file(test_file, content)
    assert test_file.exists()

    read_content = await read_file(test_file)
    assert read_content == content


@pytest.mark.asyncio
async def test_read_write_json(tmp_path):
    """Test JSON read and write operations."""
    test_file = tmp_path / "test.json"
    data = {"name": "test", "value": 42, "items": ["a", "b", "c"]}

    await write_json(test_file, data)
    assert test_file.exists()

    read_data = await read_json(test_file)
    assert read_data == data


@pytest.mark.asyncio
async def test_read_write_yaml(tmp_path):
    """Test YAML read and write operations."""
    test_file = tmp_path / "test.yaml"
    data = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "tables": ["users", "posts"],
        }
    }

    await write_yaml(test_file, data)
    assert test_file.exists()

    read_data = await read_yaml(test_file)
    assert read_data == data


def test_sanitize_component_name():
    """Test React component name sanitization."""
    assert sanitize_component_name("user_profile") == "UserProfile"
    assert sanitize_component_name("user-profile") == "UserProfile"
    assert sanitize_component_name("user profile") == "UserProfile"
    assert sanitize_component_name("user_profile_123") == "UserProfile123"
    assert sanitize_component_name("123_users") == "123Users"
    assert sanitize_component_name("user@profile#data") == "UserProfileData"


def test_to_camel_case():
    """Test snake_case to camelCase conversion."""
    assert to_camel_case("user_profile") == "userProfile"
    assert to_camel_case("get_user_by_id") == "getUserById"
    assert to_camel_case("api") == "api"
    assert to_camel_case("API_KEY") == "APIKey"


def test_to_pascal_case():
    """Test snake_case to PascalCase conversion."""
    assert to_pascal_case("user_profile") == "UserProfile"
    assert to_pascal_case("get_user_by_id") == "GetUserById"
    assert to_pascal_case("api") == "Api"
    assert to_pascal_case("api_response") == "ApiResponse"


@pytest.mark.asyncio
async def test_run_command_success():
    """Test successful command execution."""
    exit_code, stdout, stderr = await run_command(["echo", "Hello"])

    assert exit_code == 0
    assert stdout.strip() == "Hello"
    assert stderr == ""


@pytest.mark.asyncio
async def test_run_command_with_cwd(tmp_path):
    """Test command execution with working directory."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create a test file
    test_file = test_dir / "test.txt"
    test_file.write_text("content")

    # List files in the directory
    exit_code, stdout, stderr = await run_command(["ls"], cwd=test_dir)

    assert exit_code == 0
    assert "test.txt" in stdout


@pytest.mark.asyncio
async def test_run_command_timeout():
    """Test command timeout."""
    with pytest.raises(TimeoutError) as exc_info:
        await run_command(["sleep", "10"], timeout=0.1)

    assert "Command timed out after 0.1 seconds" in str(exc_info.value)


def test_extract_code_blocks():
    """Test code block extraction from markdown."""
    text = """
Here is some code:

```python
def hello():
    print("Hello, World!")
```

And some more:

```javascript
console.log("Hello");
```

And language-agnostic:

```
plain text
```
"""

    blocks = extract_code_blocks(text)
    assert len(blocks) == 3
    assert "def hello():" in blocks[0]
    assert 'console.log("Hello");' in blocks[1]
    assert "plain text" in blocks[2]

    # Test with specific language
    python_blocks = extract_code_blocks(text, "python")
    assert len(python_blocks) == 1
    assert "def hello():" in python_blocks[0]


def test_format_error_message():
    """Test error message formatting."""
    try:
        raise ValueError("Something went wrong")
    except Exception as e:
        msg = format_error_message(e, "During processing")
        assert msg == "During processing: ValueError: Something went wrong"

    # Test with custom exception
    class CustomError(Exception):
        pass

    try:
        raise CustomError("Custom error occurred")
    except Exception as e:
        msg = format_error_message(e, "In custom operation")
        assert "In custom operation: CustomError: Custom error occurred" == msg


@pytest.mark.asyncio
async def test_write_file_creates_directories(tmp_path):
    """Test that write_file creates parent directories."""
    nested_file = tmp_path / "a/b/c/test.txt"

    await write_file(nested_file, "content")

    assert nested_file.exists()
    assert nested_file.read_text() == "content"
