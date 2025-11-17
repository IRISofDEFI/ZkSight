# Contributing to Chimera Analytics

## Development Setup

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker and Docker Compose
- Git

### Initial Setup

1. Clone the repository
2. Run the setup script:
   - Unix/Mac: `bash scripts/setup.sh`
   - Windows: `powershell scripts/setup.ps1`
3. Configure environment variables in `.env` files
4. Verify setup: `bash scripts/verify-setup.sh` (or `.ps1` on Windows)

## Project Structure

See [STRUCTURE.md](STRUCTURE.md) for detailed project organization.

## Development Workflow

### Starting Development Environment

```bash
# Start infrastructure services
docker-compose up -d

# Verify services are running
bash scripts/verify-setup.sh

# Start API server (Terminal 1)
npm run dev:api

# Start dashboard (Terminal 2)
npm run dev:dashboard
```

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run linting and formatting: `npm run lint && npm run format`
4. Run tests: `npm run test`
5. Commit your changes with clear messages
6. Push and create a pull request

## Code Style

### TypeScript/JavaScript

- Use ESLint and Prettier (configured in each package)
- Run `npm run lint` to check
- Run `npm run format` to auto-fix
- Follow TypeScript strict mode guidelines
- Use meaningful variable and function names
- Add JSDoc comments for public APIs

### Python

- Use Black for formatting (line length: 100)
- Use isort for import sorting
- Use Pylint for linting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Use docstrings for modules, classes, and functions

### Commit Messages

Follow conventional commits format:

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add query submission endpoint
fix(agents): resolve configuration validation error
docs(readme): update setup instructions
```

## Testing

### Running Tests

```bash
# All tests
npm run test

# Specific package
npm run test --workspace=@chimera/api

# Python tests
cd packages/agents && pytest
```

### Writing Tests

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies

### Test Structure

```typescript
// TypeScript (Vitest)
describe('FeatureName', () => {
  it('should do something specific', () => {
    // Arrange
    const input = 'test';
    
    // Act
    const result = doSomething(input);
    
    // Assert
    expect(result).toBe('expected');
  });
});
```

```python
# Python (pytest)
def test_feature_does_something_specific():
    """Test that feature does something specific"""
    # Arrange
    input_value = "test"
    
    # Act
    result = do_something(input_value)
    
    # Assert
    assert result == "expected"
```

## Package-Specific Guidelines

### packages/agents (Python)

- Use Pydantic for data validation
- Follow async/await patterns for I/O operations
- Use type hints consistently
- Add comprehensive docstrings
- Handle errors gracefully with proper logging

### packages/api (TypeScript)

- Use Zod for request validation
- Follow Express best practices
- Implement proper error handling middleware
- Use async/await for asynchronous operations
- Add OpenAPI documentation for endpoints

### packages/sdk (TypeScript)

- Maintain backward compatibility
- Export clear, typed interfaces
- Handle errors gracefully
- Provide helpful error messages
- Include usage examples in comments

### packages/dashboard (React)

- Use functional components with hooks
- Follow React best practices
- Keep components small and focused
- Use TypeScript for props and state
- Implement proper error boundaries
- Ensure accessibility (a11y) compliance

## Configuration Management

### Environment Variables

- Never commit `.env` files
- Update `.env.example` when adding new variables
- Document all environment variables
- Use validation for all configuration values

### Adding New Configuration

1. Add to `.env.example` with description
2. Add validation in config files:
   - Python: `packages/agents/src/config.py`
   - TypeScript: `packages/api/src/config.ts`
3. Update documentation

## Database Migrations

### MongoDB

- Create migration scripts in `packages/api/migrations/`
- Use timestamps in filenames: `YYYYMMDD_description.ts`
- Test migrations on development data first
- Document breaking changes

### InfluxDB

- Define schemas in design documents
- Use retention policies appropriately
- Document measurement structures

## Docker and Infrastructure

### Modifying Docker Compose

- Test changes locally first
- Update documentation if ports or services change
- Ensure backward compatibility
- Update health checks if needed

### Adding New Services

1. Add service to `docker-compose.yml`
2. Update configuration files
3. Update setup scripts
4. Update verification scripts
5. Document in README.md

## Documentation

### Code Documentation

- Add comments for complex logic
- Use JSDoc/docstrings for public APIs
- Keep comments up to date with code changes
- Explain "why" not "what" in comments

### Project Documentation

- Update README.md for user-facing changes
- Update STRUCTURE.md for architectural changes
- Update design documents for major features
- Keep examples current

## Pull Request Process

1. Update documentation as needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Run linting and formatting
5. Update CHANGELOG.md (if applicable)
6. Request review from maintainers
7. Address review feedback
8. Squash commits if requested

## Getting Help

- Check existing documentation first
- Review design documents in `.kiro/specs/`
- Ask questions in pull request comments
- Reach out to maintainers

## Code Review Guidelines

### For Authors

- Keep PRs focused and reasonably sized
- Provide context in PR description
- Respond to feedback promptly
- Be open to suggestions

### For Reviewers

- Be constructive and respectful
- Focus on code quality and maintainability
- Check for test coverage
- Verify documentation updates
- Test changes locally when possible

## Performance Considerations

- Profile before optimizing
- Consider scalability implications
- Use appropriate data structures
- Implement caching where beneficial
- Monitor resource usage

## Security Considerations

- Never commit secrets or credentials
- Validate all user inputs
- Use parameterized queries
- Implement proper authentication/authorization
- Follow OWASP guidelines
- Report security issues privately

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
