"""Tests for TypeScript type generation."""

import pytest

from ai_frontend.type_generator import TypeScriptGenerator


@pytest.fixture
def generator():
    """Create a TypeScriptGenerator instance."""
    return TypeScriptGenerator()


def test_basic_type_generation(generator):
    """Test basic TypeScript type generation from schema."""
    schema = {
        "tables": {
            "users": {
                "columns": {
                    "id": {"type": "integer", "primary_key": True},
                    "name": {"type": "string", "required": True},
                    "email": {"type": "string", "format": "email", "nullable": True},
                }
            }
        }
    }

    result = generator.generate_from_schema(schema)

    assert "export interface Users {" in result
    assert "id: number;" in result
    assert "name: string;" in result
    assert "email?: string;" in result
    assert "export interface CreateUsersDTO {" in result
    assert "export interface UpdateUsersDTO {" in result


def test_enum_type_generation(generator):
    """Test enum type generation."""
    schema = {
        "tables": {
            "tasks": {
                "columns": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed"],
                    }
                }
            }
        }
    }

    result = generator.generate_from_schema(schema)

    assert 'status: "pending" | "in_progress" | "completed";' in result


def test_array_type_generation(generator):
    """Test array type generation."""
    schema = {
        "tables": {
            "posts": {
                "columns": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                }
            }
        }
    }

    result = generator.generate_from_schema(schema)

    assert "tags: string[];" in result


def test_view_type_generation(generator):
    """Test view type generation."""
    schema = {
        "views": {
            "user_summary": {
                "result_schema": {
                    "user_count": {"type": "integer"},
                    "active_count": {"type": "integer", "nullable": True},
                }
            }
        }
    }

    result = generator.generate_from_schema(schema)

    assert "export interface UserSummaryView {" in result
    assert "user_count: number;" in result
    assert "active_count?: number;" in result


def test_api_response_types(generator):
    """Test API response type generation."""
    schema = {"tables": {}}
    result = generator.generate_from_schema(schema)

    assert "export interface ApiResponse<T> {" in result
    assert "export interface QueryResult<T> {" in result
    assert "export interface MutationResult {" in result
    assert "export interface ApiError {" in result


def test_dto_generation_excludes_auto_fields(generator):
    """Test that DTOs exclude auto-generated fields."""
    schema = {
        "tables": {
            "posts": {
                "columns": {
                    "id": {"type": "integer", "auto_increment": True},
                    "title": {"type": "string", "required": True},
                    "content": {"type": "string"},
                    "created_at": {"type": "string", "generated": True},
                    "updated_at": {"type": "string", "immutable": False},
                }
            }
        }
    }

    result = generator.generate_from_schema(schema)

    # CreateDTO should not have auto_increment or generated fields
    create_dto_section = result[
        result.find("export interface CreatePostsDTO") : result.find(
            "export interface UpdatePostsDTO"
        )
    ]
    assert "id:" not in create_dto_section
    assert "created_at:" not in create_dto_section
    assert "title: string;" in create_dto_section

    # UpdateDTO should not have immutable or auto_increment fields
    update_dto_start = result.find("export interface UpdatePostsDTO")
    update_dto_end = result.find("}", update_dto_start) + 1
    update_dto_section = result[update_dto_start:update_dto_end]
    assert "  id?:" not in update_dto_section  # Check for field definition, not just "id?"
    assert "title?: string;" in update_dto_section


def test_complex_object_type(generator):
    """Test complex nested object type generation."""
    schema = {
        "tables": {
            "configs": {
                "columns": {
                    "id": {"type": "integer"},
                    "settings": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string"},
                            "notifications": {"type": "boolean"},
                        },
                        "required": ["theme"],
                    },
                }
            }
        }
    }

    result = generator.generate_from_schema(schema)

    # Should generate inline object types
    assert "settings: { theme: string; notifications?: boolean }" in result.replace("\n", " ")
