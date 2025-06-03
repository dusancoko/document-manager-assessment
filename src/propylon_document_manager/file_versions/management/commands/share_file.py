# management/commands/share_file.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from propylon_document_manager.file_versions.models import FileVersion, User


class Command(BaseCommand):
    help = 'Share a file with a user by granting permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file-id',
            type=int,
            required=True,
            help='ID of the file to share'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            required=True,
            help='Email of the user to share the file with'
        )
        parser.add_argument(
            '--can-edit',
            action='store_true',
            help='Grant edit permissions in addition to view'
        )

    def handle(self, *args, **options):
        file_id = options['file_id']
        user_email = options['user_email']
        can_edit = options['can_edit']

        try:
            file_version = FileVersion.objects.get(id=file_id)
        except FileVersion.DoesNotExist:
            raise CommandError(f'File with ID {file_id} does not exist')

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise CommandError(f'User with email {user_email} does not exist')

        # Get content type for FileVersion
        content_type = ContentType.objects.get_for_model(FileVersion)
        
        # Grant view permission
        view_permission = Permission.objects.get(
            codename='view_fileversion',
            content_type=content_type
        )
        user.user_permissions.add(view_permission)
        
        permissions_granted = ['view']
        
        if can_edit:
            change_permission = Permission.objects.get(
                codename='change_fileversion',
                content_type=content_type
            )
            user.user_permissions.add(change_permission)
            permissions_granted.append('edit')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully shared file "{file_version.file_name}" with {user_email}. '
                f'Permissions granted: {", ".join(permissions_granted)}'
            )
        )

        # Also show how to test this
        self.stdout.write(
            self.style.WARNING(
                f'\nTo test:\n'
                f'1. Login as {user_email}\n'
                f'2. Navigate to "Shared with me" page\n'
                f'3. You should see the file "{file_version.file_name}"\n'
            )
        )