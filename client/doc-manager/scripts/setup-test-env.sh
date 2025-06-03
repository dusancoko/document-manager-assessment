#!/bin/bash

# Setup test environment
echo "🛠️  Setting up test environment..."

# Create test directories
mkdir -p src/__tests__
mkdir -p src/components/__tests__
mkdir -p src/pages/__tests__
mkdir -p src/context/__tests__
mkdir -p src/api/__tests__
mkdir -p src/utils/__tests__
mkdir -p reports
mkdir -p coverage

# Install test dependencies if not present
if ! npm list @testing-library/react >/dev/null 2>&1; then
    echo "📦 Installing testing dependencies..."
    npm install --save-dev \
        @testing-library/react \
        @testing-library/jest-dom \
        @testing-library/user-event \
        jest \
        jest-environment-jsdom \
        jest-junit \
        axios-mock-adapter \
        identity-obj-proxy
fi

echo "✅ Test environment setup complete!"
