# Repository Analysis Guide

When gathering context about a target repository, check the following in order.
Not all items will exist in every repo — skip what's missing.

## 1. Project Documentation

- **CLAUDE.md** — Project conventions, build/test commands, architecture notes.
  This is the most important file. Read it fully.
- **README.md** — Project description, setup instructions, tech stack.
- **CONTRIBUTING.md** — Contribution guidelines, PR requirements.

## 2. Package Manifest

Look for one of these (in priority order):
- `package.json` (Node.js/JavaScript/TypeScript)
- `Cargo.toml` (Rust)
- `go.mod` (Go)
- `pyproject.toml` or `setup.py` (Python)
- `Gemfile` (Ruby)
- `pom.xml` or `build.gradle` (Java/Kotlin)
- `*.csproj` or `*.sln` (C#/.NET)

Extract: project name, dependencies, scripts/commands (especially `test`,
`build`, `lint`).

## 3. Source Layout

Use Glob to identify the directory structure:
```
**/src/**
**/lib/**
**/app/**
**/components/**
**/pages/**
**/api/**
```

Understand where different types of code live (components, utilities, routes,
models, etc.).

## 4. Test Patterns

Find test files:
```
**/*.test.*
**/*.spec.*
**/test/**
**/tests/**
**/__tests__/**
```

Identify: test framework (Jest, pytest, Go testing, etc.), test file naming
convention, helper/fixture patterns.

## 5. CI/CD Configuration

Check for:
- `.github/workflows/*.yml`
- `.gitlab-ci.yml`
- `Jenkinsfile`
- `.circleci/config.yml`

Understand: what runs on PR, required checks, deployment pipeline.

## 6. Configuration Files

- `.env.example` — environment variables needed
- `docker-compose.yml` — service dependencies
- Database migration directories (`migrations/`, `prisma/`, `drizzle/`)
- Linting/formatting config (`.eslintrc`, `.prettierrc`, `ruff.toml`)

## What to Record

After analysis, you should be able to answer:
1. What language(s) and framework(s) does this project use?
2. How do you run tests?
3. How do you build the project?
4. What's the directory convention for new features?
5. Are there existing patterns for the type of feature being planned?
6. What CI checks must pass before merge?
