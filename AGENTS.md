# AGENTS.md - Agentic Coding Guidelines

This file provides guidelines for AI agents operating in this repository.

## Build, Lint, and Test Commands

### Running the Full Test Suite

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode during development
npm test -- --watch

# Run tests with verbose output
npm test -- --verbose
```

### Running a Single Test

```bash
# Run a specific test file
npm test -- path/to/test-file.test.ts

# Run tests matching a specific name pattern
npm test -- --testNamePattern="user authentication"

# Run a specific test by exact name
npm test -- --testNamePattern="should validate email format"

# Run tests in a specific directory
npm test -- src/components/__tests__/

# Run a single test case
it('should handle null input', () => {
  expect(handleNull(null)).toBeDefined();
});
```

### Linting and Formatting

```bash
# Run ESLint on the entire project
npm run lint

# Fix auto-fixable linting issues
npm run lint -- --fix

# Run Prettier formatting check
npm run format:check

# Format code with Prettier
npm run format

# Run type checking
npm run typecheck

# Run all checks (lint + format + typecheck)
npm run check
```

### Building the Project

```bash
# Build for development
npm run build:dev

# Build for production
npm run build

# Build with source maps
npm run build:source-maps

# Clean build artifacts
npm run clean
```

### Development Commands

```bash
# Start development server
npm run dev

# Start development server with specific port
PORT=3000 npm run dev

# Run storybook for component development
npm run storybook

# Generate new component/slice
npm run generate component MyComponent
```

## Code Style Guidelines

### General Principles

- Write clean, readable code over clever code
- Keep functions small and focused (single responsibility)
- Use meaningful variable and function names
- Comment the "why", not the "what"
- Prefer explicit over implicit

### TypeScript/JavaScript Conventions

#### Types

```typescript
// Use explicit return types for public functions
function calculateTotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// Use interfaces for object shapes
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

// Prefer type aliases for unions and primitives
type Status = 'pending' | 'active' | 'completed';
type ID = string | number;
```

#### Naming Conventions

```typescript
// Variables and functions: camelCase
const userName = 'John';
function getUserById(id: string) {}

// Classes, interfaces (when used as types), enums: PascalCase
class UserService {}
interface ApiConfig {}
enum HttpStatus {}

// Constants: SCREAMING_SNAKE_CASE
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';

// Private members: prefix with underscore
class Service {
  private _cache: Map<string, unknown>;
}
```

#### Imports

```typescript
// Order imports alphabetically within each group
import React from 'react';                    // External
import { useState, useEffect } from 'react';  // Named external

import { Button } from '@/components';        // Alias imports
import { formatDate } from '@/utils';         // Utils

import { User } from '../types';              // Relative imports
import { api } from './api';                  // Local imports

// Use path aliases (@/) for absolute imports from src root
// Group imports: external > aliases > relative
```

#### Formatting

```typescript
// Use 2 spaces for indentation
// Maximum line length: 100 characters
// Use semicolons
// Use single quotes for strings
// Prefer arrow functions for callbacks
const filtered = items.filter((item) => item.active);

// Destructure when possible
const { id, name, email } = user;

// Use async/await over raw promises
async function fetchUser(id: string): Promise<User> {
  const response = await api.get(`/users/${id}`);
  return response.data;
}
```

### Error Handling

```typescript
// Use custom error classes for domain errors
class ValidationError extends Error {
  constructor(message: string, public field: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

// Always handle async errors with try/catch
async function getData() {
  try {
    const result = await fetchData();
    return result;
  } catch (error) {
    if (error instanceof ValidationError) {
      // Handle specific error type
      throw error;
    }
    // Log and wrap unknown errors
    logger.error('Failed to fetch data', { error });
    throw new ApiError('Failed to fetch data');
  }
}

// Use Result types for explicit error handling
type Result<T, E = Error> = { success: true; data: T } | { success: false; error: E };
```

### React/Component Guidelines

```typescript
// Functional components with TypeScript
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

// Destructure props with defaults
function Button({ label, onClick, variant = 'primary' }: ButtonProps) {
  return (
    <button className={`btn btn-${variant}`} onClick={onClick}>
      {label}
    </button>
  );
}

// Use custom hooks for reusable logic
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser(userId).then(setUser).finally(() => setLoading(false));
  }, [userId]);

  return { user, loading };
}
```

### Testing Guidelines

```typescript
// Use descriptive test names
describe('UserService', () => {
  describe('createUser', () => {
    it('should create a user with valid email', async () => {
      const user = await userService.createUser({
        email: 'test@example.com',
        name: 'Test User',
      });
      expect(user.id).toBeDefined();
    });

    it('should throw ValidationError for invalid email', async () => {
      await expect(
        userService.createUser({ email: 'invalid', name: 'Test' })
      ).rejects.toThrow(ValidationError);
    });
  });
});

// Use beforeEach for common setup
beforeEach(() => {
  jest.clearAllMocks();
  container = render(<Component />);
});
```

### Git Conventions

```bash
# Use conventional commits
git commit -m "feat: add user authentication"
git commit -m "fix: resolve memory leak in cache"
git commit -m "docs: update API documentation"

# Types: feat, fix, docs, style, refactor, test, chore
```

## Additional Guidelines

- Always run `npm run check` before committing
- Ensure all tests pass before pushing
- Update documentation when changing APIs
- Use TypeScript strict mode
- Enable ESLint and Prettier in your editor
