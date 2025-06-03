from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import getpass

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a new user for the Propylon Document Manager'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email address',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='User display name',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='User password',
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Create a superuser with admin privileges',
        )
        parser.add_argument(
            '--staff',
            action='store_true',
            help='Give the user staff status',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        name = options.get('name', '')
        password = options.get('password')
        superuser = options.get('superuser', False)
        staff = options.get('staff', False)

        # Get email if not provided
        if not email:
            email = input('Email address: ').strip()
        
        # Validate email
        if not email:
            raise CommandError('Email address is required')
        
        if '@' not in email:
            raise CommandError('Please provide a valid email address')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email "{email}" already exists')
        
        # Get name if not provided
        if not name:
            name = input('Display name (optional): ').strip()
        
        # Get password if not provided
        if not password:
            while True:
                password = getpass.getpass('Password: ')
                if not password:
                    self.stdout.write(self.style.ERROR('Password cannot be empty'))
                    continue
                
                password_confirm = getpass.getpass('Password (again): ')
                if password != password_confirm:
                    self.stdout.write(self.style.ERROR('Passwords do not match'))
                    continue
                break
        
        # Create user
        try:
            if superuser:
                user = User.objects.create_superuser(
                    email=email,
                    password=password,
                    name=name
                )
                user_type = "superuser"
            else:
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    name=name
                )
                user.is_staff = staff
                user.save()
                user_type = "staff user" if staff else "regular user"
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {user_type}: {email}'
                )
            )
            
        except IntegrityError as e:
            raise CommandError(f'Error creating user: {e}')
        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')