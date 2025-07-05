"""Tests for TypeScript type generation."""

import pytest

from ai_frontend.type_generator import TypeScriptGenerator


def test_basic_type_generation():
    """Test basic TypeScript type generation from schema."""
    generator = TypeScriptGenerator()
    
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


def test_enum_type_generation():
    """Test enum type generation."""
    generator = TypeScriptGenerator()
    
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


def test_array_type_generation():
    """Test array type generation."""
    generator = TypeScriptGenerator()
    
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


def test_view_type_generation():
    """Test view type generation."""
    generator = TypeScriptGenerator()
    
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


def test_api_response_types():
    """Test API response type generation."""
    generator = TypeScriptGenerator()
    
    schema = {"tables": {}}
    result = generator.generate_from_schema(schema)
    
    assert "export interface ApiResponse<T> {" in result
    assert "export interface QueryResult<T> {" in result
    assert "export interface MutationResult {" in result
    assert "export interface ApiError {" in result