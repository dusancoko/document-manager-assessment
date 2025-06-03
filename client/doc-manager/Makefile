.PHONY: test test-watch test-coverage test-ci setup-tests clean-tests

# Default test command
test:
	npm test

# Watch mode for development
test-watch:
	npm run test:watch

# Run tests with coverage
test-coverage:
	npm run test:coverage
	@echo "Coverage report generated in coverage/ directory"

# CI/CD test command
test-ci:
	./scripts/test-ci.sh

# Setup test environment
setup-tests:
	./scripts/setup-test-env.sh

# Clean test artifacts
clean-tests:
	rm -rf coverage/
	rm -rf reports/
	rm -rf node_modules/.cache/

# Run linting
lint:
	npm run lint

# Fix linting issues
lint-fix:
	npm run lint:fix

# Run security audit
audit:
	npm audit --audit-level high

# Install and run all checks
check-all: setup-tests lint audit test-coverage
	@echo "✅ All checks completed successfully!"

# Docker commands for testing
docker-test:
	docker run --rm -v $(PWD):/app -w /app node:18 npm run test:ci

docker-test-interactive:
	docker run --rm -it -v $(PWD):/app -w /app node:18 bash

# Performance testing
perf-test:
	npm run build
	npx lighthouse http://localhost:3000 --output html --output-path ./reports/lighthouse-report.html

# README.md - Testing section
## Testing

This project includes comprehensive Jest-based testing for the React frontend.

### Test Structure

```
src/
├── __tests__/                 # Integration tests
├── components/__tests__/      # Component unit tests  
├── pages/__tests__/          # Page component tests
├── context/__tests__/        # Context provider tests
├── api/__tests__/           # API client tests
└── utils/__tests__/         # Utility function tests
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run tests for CI
npm run test:ci

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix
```

### Test Categories

1. **Unit Tests**: Individual component and function testing
2. **Integration Tests**: Full application flow testing
3. **Performance Tests**: Large dataset and efficiency testing
4. **Edge Case Tests**: Error conditions and boundary testing

### Coverage Requirements

- **Lines**: 70% minimum
- **Functions**: 70% minimum  
- **Branches**: 70% minimum
- **Statements**: 70% minimum

### Mocking Strategy

- **API calls**: MockAdapter for axios
- **Browser APIs**: localStorage, window.open
- **External libraries**: FontAwesome, dayjs
- **React Router**: MemoryRouter for testing

### Writing Tests

Example test structure:

```javascript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MockAdapter from 'axios-mock-adapter';
import api from '../api/client';
import Component from '../Component';

const mockAxios = new MockAdapter(api);

describe('Component', () => {
  beforeEach(() => {
    mockAxios.reset();
  });

  test('should render correctly', () => {
    render(<Component />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });
});
```

### CI/CD Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Multiple Node.js versions (16.x, 18.x, 20.x)

### Performance Monitoring

- Lighthouse CI for performance metrics
- Bundle size analysis
- Memory usage monitoring

# docker-compose.test.yml
version: '3.8'

services:
  frontend-test:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - CI=true
      - NODE_ENV=test
    command: npm run test:ci

  frontend-lint:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - .:/app
      - /app/node_modules
    command: npm run lint

  frontend-audit:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - .:/app
      - /app/node_modules
    command: npm audit --audit-level high

# Dockerfile.test
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Create directories for reports
RUN mkdir -p reports coverage

# Default command
CMD ["npm", "run", "test:ci"]

# scripts/test-summary.sh
#!/bin/bash

# Generate test summary report
echo "📊 Test Summary Report"
echo "======================"

# Check if coverage exists
if [ -f "coverage/lcov-report/index.html" ]; then
    echo "✅ Coverage report available at: coverage/lcov-report/index.html"
    
    # Extract coverage percentages
    LINES_COV=$(grep -o 'Lines.*[0-9]*\.[0-9]*%' coverage/lcov-report/index.html | grep -o '[0-9]*\.[0-9]*')
    FUNCTIONS_COV=$(grep -o 'Functions.*[0-9]*\.[0-9]*%' coverage/lcov-report/index.html | grep -o '[0-9]*\.[0-9]*')
    BRANCHES_COV=$(grep -o 'Branches.*[0-9]*\.[0-9]*%' coverage/lcov-report/index.html | grep -o '[0-9]*\.[0-9]*')
    
    echo "📈 Coverage Metrics:"
    echo "   Lines: ${LINES_COV}%"
    echo "   Functions: ${FUNCTIONS_COV}%"
    echo "   Branches: ${BRANCHES_COV}%"
else
    echo "❌ No coverage report found"
fi

# Check test results
if [ -f "reports/jest-results.xml" ]; then
    echo "✅ Test results available at: reports/jest-results.xml"
    
    # Count tests
    TOTAL_TESTS=$(grep -o 'tests="[0-9]*"' reports/jest-results.xml | grep -o '[0-9]*')
    FAILED_TESTS=$(grep -o 'failures="[0-9]*"' reports/jest-results.xml | grep -o '[0-9]*')
    
    echo "🧪 Test Results:"
    echo "   Total: ${TOTAL_TESTS}"
    echo "   Failed: ${FAILED_TESTS}"
    echo "   Passed: $((TOTAL_TESTS - FAILED_TESTS))"
else
    echo "❌ No test results found"
fi

# Check linting results
if [ -f "reports/eslint-results.xml" ]; then
    echo "✅ Lint results available at: reports/eslint-results.xml"
    
    # Count lint issues
    LINT_ERRORS=$(grep -c 'severity="error"' reports/eslint-results.xml || echo "0")
    LINT_WARNINGS=$(grep -c 'severity="warning"' reports/eslint-results.xml || echo "0")
    
    echo "🔍 Lint Results:"
    echo "   Errors: ${LINT_ERRORS}"
    echo "   Warnings: ${LINT_WARNINGS}"
else
    echo "❌ No lint results found"
fi

echo ""
echo "📝 Reports generated:"
ls -la reports/ 2>/dev/null || echo "No reports directory found"

echo ""
echo "🎯 Quick Commands:"
echo "   View coverage: open coverage/lcov-report/index.html"
echo "   Run tests: npm test"
echo "   Watch mode: npm run test:watch"
echo "   Full check: make check-all"