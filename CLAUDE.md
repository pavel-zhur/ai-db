﻿# Python Code Guidelines for this project

This document outlines Python-specific coding standards for this project.

## Type System
- Use explicit type annotations everywhere (parameters, return types, variables)
- Follow strict mypy configuration - no Any except where necessary
- Mark non-public members (methods, properties, fields) with leading underscore (`_`) and prefer encapsulation with non-public members over public exposure
- Prefer avoiding union types. Prefer code to work with a single concrete type in each context through proper type narrowing, better conditional handling, or appropriate design patterns.
- Trust the type system - avoid excessive defensive programming or unnecessary null checks. Let errors propagate naturally where appropriate.

## Design Patterns
- Follow dependency injection using dependency_injector
- Use dataclasses for data containers with proper field typing
- Try to avoid optional parameters, default values, fallback logic
- Use explicit exception handling with proper types

## Best Practices
- Design for testability with clear dependency boundaries
- Use strongly typed configuration classes
- Don't catch exceptions just to log and re-raise them - let exceptions propagate to appropriate boundary layers where they can be properly handled and logged
- Avoid defensive programming patterns when the type system already guarantees correctness
- Trust the contract provided by interfaces and models - don't add unnecessary checks for conditions that can't occur if the types are correct

## Behavior

- Please don't do workarounds, do only best practices, and if something at hand doesn't work - analyze the reason, fix the root problem, or talk to me and let me decide.
