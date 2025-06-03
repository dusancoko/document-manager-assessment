# Propylon Document Manager - Developer Manual

This manual provides comprehensive instructions for setting up and running the Propylon Document Manager development environment on Debian/Ubuntu-based distributions.

## Prerequisites

### System Dependencies

Install the required build tools and development packages:

```bash
sudo apt update
sudo apt install build-essential pkg-config cmake autoconf automake libtool git
```

### Repository Setup

1. **Clone the repository** in your desired parent directory:
   ```bash
   git clone https://github.com/dusancoko/document-manager-assessment.git
   cd document-manager-assessment
   ```

2. **Verify Python version** - This project requires Python 3.11:
   ```bash
   python3.11 --version
   ```

## Backend API Setup

### Environment Configuration

1. **Build the virtual environment and database**:
   ```bash
   make build
   make makemigrations
   make migrate
   ```

2. **Set required environment variables**:
   ```bash
   export PYTHONPATH=.
   export DJANGO_SETTINGS_MODULE=propylon_document_manager.site.settings.local
   ```

3. **Activate the virtual environment**:
   ```bash
   source .env_python3.11/bin/activate
   ```

### User Management

#### Create Administrative User

Create a superuser account for administrative access:

```bash
python manage.py createsuperuser
```

Follow the interactive prompts to set up your administrator credentials.

#### Create Additional Users

For testing and development purposes, create additional users using the custom management command:

**Interactive user creation:**
```bash
python manage.py create_user
```

**Non-interactive user creation:**
```bash
# Regular user
python manage.py create_user --email user@example.com --name "John Doe"

# Staff user
python manage.py create_user --email staff@example.com --name "Staff User" --staff

# Superuser
python manage.py create_user --email admin@example.com --name "Admin User" --superuser
```

**Batch user creation with parameters:**
```bash
python manage.py create_user \
    --email developer@propylon.com \
    --name "Developer User" \
    --password "SecurePassword123"
```

### Development Server

Start the development server on port 8001:

```bash
make plain-serve
```

The server will be accessible at: `http://127.0.0.1:8001`

### Administrative Interface

Access the Django admin interface to manage users, files, and system configuration:

**URL:** [http://127.0.0.1:8001/admin](http://127.0.0.1:8001/admin)

Log in using your superuser credentials to:
- Manage user accounts and permissions
- View file upload history
- Configure system settings
- Monitor application status

### Testing

Execute the test suite to verify system functionality:

```bash
make test
```

This command runs all unit tests and integration tests to ensure the application is functioning correctly.

## API Endpoints

The backend provides RESTful API endpoints for:

- **Authentication:** `/api/token/`
- **File Management:** `/api/file_versions/`
- **File Upload:** `/api/upload/`
- **File Download:** `/api/download/<path>/`
- **File Sharing:** `/api/share/`
- **Version Comparison:** `/api/compare/`

Refer to the API documentation or examine the `urls.py` file for complete endpoint specifications.

## Development Workflow

1. **Activate environment** before starting development:
   ```bash
   source .env_python3.11/bin/activate
   ```

2. **Run migrations** after model changes:
   ```bash
   make makemigrations
   make migrate
   ```

3. **Test changes** before committing:
   ```bash
   make test
   ```

4. **Start development server** for testing:
   ```bash
   make plain-serve
   ```

## Troubleshooting

### Common Issues

- **Virtual environment not found:** Ensure `make build` completed successfully
- **Database errors:** Run `make migrate` to apply pending migrations
- **Permission errors:** Verify the virtual environment is activated
- **Port conflicts:** Ensure port 8001 is available or modify server configuration

### Log Files

Monitor application logs for debugging information during development and testing.

## Frontend Application Setup

The frontend is a React application that provides a modern web interface for the document management system.

### Prerequisites

Ensure you have Node.js and npm installed:

```bash
# Install Node.js (version 16 or higher recommended)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

### Installation

1. **Navigate to the frontend directory**:
   ```bash
   cd document-manager-assessment/client/doc-manager
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Install additional required packages** (if not already in package.json):
   ```bash
   npm install react-router-dom@5.3.4
   npm install react-hook-form
   npm install dayjs
   npm install axios
   npm install @fortawesome/fontawesome-free
   npm install @fortawesome/react-fontawesome
   npm install @fortawesome/free-solid-svg-icons
   npm install react-diff-viewer
   ```

### Configuration

**API Configuration**: The frontend is configured to connect to the backend API at `http://127.0.0.1:8001/api`. This is set in `src/api/client.js`.

### Development Server

Start the React development server:

```bash
npm start
```

The frontend application will be accessible at: `http://localhost:3000`


### Frontend Features

The React application provides:

- **Authentication System**: Login/logout functionality
- **File Management**: Upload, download, and organize files
- **Version Control**: Create and manage file versions
- **File Sharing**: Share files with other users with permission controls
- **Version Comparison**: Side-by-side diff view for supported file types
- **Responsive Design**: Mobile-friendly interface

### Application Structure

```
frontend/
├── public/
│   ├── index.html
│   └── Propylon.svg          # Company logo
├── src/
│   ├── api/
│   │   └── client.js         # Axios API client configuration
│   ├── components/
│   │   ├── Layout.js         # Main layout wrapper
│   │   ├── FileShareModal.js # File sharing modal
│   │   └── PropylonLogo.js   # Logo component
│   ├── context/
│   │   ├── AuthContext.js    # Authentication state management
│   │   └── PrivateRoute.js   # Protected route component
│   ├── pages/
│   │   ├── LoginPage.js      # User authentication
│   │   ├── MyFilesPage.js    # User's files dashboard
│   │   ├── SharedWithMePage.js # Shared files view
│   │   ├── UploadPage.js     # File upload interface
│   │   └── CompareVersionsPage.js # Version comparison
│   ├── App.js               # Main application component
│   ├── index.js             # Application entry point
│   └── custom-ui.css        # Custom styling
```

### Testing the Frontend

1. **Ensure backend is running** on port 8001
2. **Start frontend development server** on port 3000
3. **Navigate to** `http://localhost:3000`
4. **Login** using credentials created with the backend user management commands

### Frontend Development Workflow

1. **Start both servers**:
   ```bash
   # Terminal 1 - Backend
   cd document-manager-assessment
   source .env_python3.11/bin/activate
   make plain-serve

   # Terminal 2 - Frontend
   cd document-manager-assessment/client/doc-manager
   npm start
   ```

2. **Development cycle**:
   - Make changes to React components
   - The development server auto-reloads on file changes
   - Test functionality in the browser
   - Check browser console for any errors

3. **API Integration**:
   - Frontend communicates with backend via REST API
   - Authentication tokens are stored in localStorage
   - All API calls include proper authentication headers

### Troubleshooting Frontend Issues

#### Common Problems

- **CORS errors**: Ensure backend allows frontend origin
- **API connection refused**: Verify backend server is running on port 8001
- **Authentication issues**: Check if user credentials are valid
- **Missing dependencies**: Run `npm install` to install all packages
- **Port conflicts**: Change ports if 3000 is occupied

#### Debug Steps

1. **Check browser console** for JavaScript errors
2. **Verify API endpoints** are responding (use browser dev tools Network tab)
3. **Confirm backend API** is accessible at `http://127.0.0.1:8001/api`
4. **Test authentication** by logging in through Django admin first


**Access the application**:
   - Frontend: `http://localhost:3000`
   - Backend Admin: `http://127.0.0.1:8001/admin`
   - API Endpoints: `http://127.0.0.1:8001/api/`

#### Jest frontend test
```
# Install new dependencies
npm install

# Run tests once
npm test

# Run tests in watch mode  
npm run test:watch

# Generate coverage report
npm run test:coverage

# Run linting
npm run lint

# Fix linting issues automatically
npm run lint:fix

# Security audit
npm run audit

# CI testing
npm run test:ci
```