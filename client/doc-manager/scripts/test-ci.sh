#!/bin/bash

# CI/CD Testing Script
set -e

echo "🔄 Running CI tests..."

# Install dependencies
npm ci

# Audit for security vulnerabilities
npm audit --audit-level high

# Run linting with JUnit output
npx eslint src/ --ext .js,.jsx --format junit --output-file reports/eslint-results.xml

# Run tests
npm run test:coverage

# Check if coverage meets requirements
COVERAGE_THRESHOLD=70
COVERAGE_LINES=$(npx jest --coverage --silent --passWithNoTests | grep "Lines" | grep -o '[0-9]*\.[0-9]*' | head -1)

if (( $(echo "$COVERAGE_LINES < $COVERAGE_THRESHOLD" | bc -l) )); then
    echo "❌ Coverage ($COVERAGE_LINES%) is below threshold ($COVERAGE_THRESHOLD%)"
    exit 1
fi

echo "✅ All CI checks passed!"
