# Error issues

### createsuperuser error

Error occuring when trying to create a user using command `python manage.py createsuperuser`. Resolved by creating custom class in `src/propylon_document_manager/file_versions/models.py`.

```python
    self.UserModel._default_manager.db_manager(database).create_superuser(
TypeError: UserManager.create_superuser() missing 1 required positional argument: 'username'
```

### Django REST framework built-in methods not working

Due to custom user model, I have been receiving various errors requesting argument `username`. Since this is a part of already built project, I'm tring to keep as much of the existing boilerplate as possible, so there are modifications required, which will be documented in the Project modifications section.


# Project modifications

## Users

### Authorization for Web UI / User model

Added authorization plugins to `src/propylon_document_manager/site/settings/base.py` to be visible in Django admin UI to register additional users.

**User** model was also registered to `src/propylon_document_manager/file_versions/admin.py` so it can be accessed via Web UI.

### Custom Token authentication

Per assigment, custom user object is provided without the username field, so using Django REST framework built-in features in not 

## Files

### FileVersion model modification

Switched out original **FileVersion** class for the new class in `src/propylon_document_manager/file_versions/models.py` for better file tracking information.

Models were added to `src/propylon_document_manager/file_versions/admin.py` to be visible in Django admin UI.