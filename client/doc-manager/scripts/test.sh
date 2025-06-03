#!/bin/bash

# Frontend Testing Script for Propylon Document Manager

set -e  # Exit on any error

echo "🧪 Starting Frontend Test Suite..."

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run linting
echo "🔍 Running ESLint..."
npx eslint src/ --ext .js,.jsx --max-warnings 0

# Run tests with coverage
echo "🧪 Running Jest tests with coverage..."
npm run test:coverage

# Check coverage thresholds
echo "📊 Checking coverage thresholds..."
npx jest --coverage --passWithNoTests

# Generate test report
echo "📄 Generating test reports..."
mkdir -p reports

# Run tests with JUnit reporter for CI
npx jest --reporters=default --reporters=jest-junit --outputFile=reports/jest-results.xml

echo "✅ All tests completed successfully!"

# Display coverage summary
echo "📊 Coverage Summary:"
npx jest --coverage --silent --passWithNoTests | tail -n 10