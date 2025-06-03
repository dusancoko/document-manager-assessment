from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import CharField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..utils.file_management import unique_file_upload_path

class UserManager(BaseUserManager):
    """Custom user manager for the User model. Resolves the issue of missing username field."""
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Default custom user model for Propylon Document Manager.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """
    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})


class FileVersion(models.Model):
    file_name = models.CharField(max_length=255)
    version_number = models.PositiveIntegerField()
    file_path = models.FileField(upload_to=unique_file_upload_path)
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_files")
    created_at = models.DateTimeField(auto_now_add=True)

    # New required virtual path
    virtual_path = models.CharField(max_length=500)

    # Optional metadata
    mime_type = models.CharField(max_length=100, default="application/octet-stream")
    file_size = models.IntegerField(default=-1)
    checksum = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)

    # Versioning references
    previous_version = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="next_versions"
    )
    root_file = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="all_versions"
    )

    def __str__(self):
        return f"{self.file_name} (v{self.version_number}) by {self.uploader.username}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['virtual_path', 'uploader'],
                condition=models.Q(previous_version__isnull=True),
                name='unique_root_file_per_user_and_path'
            )
        ]

