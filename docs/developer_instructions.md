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

## Additional Resources

- Django documentation: [https://docs.djangoproject.com/](https://docs.djangoproject.com/)
- Django REST Framework: [https://www.django-rest-framework.org/](https://www.django-rest-framework.org/)
- Project repository: [https://github.com/dusancoko/document-manager-assessment](https://github.com/dusancoko/document-manager-assessment)