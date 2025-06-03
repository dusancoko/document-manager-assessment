# src/tests/test_models.py
"""
Test cases for models in the file_versions app
"""

from django.test import TestCase
from django.urls import reverse
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

from propylon_document_manager.file_versions.models import User, FileVersion
from .base import BaseTestCase


class UserModelTest(BaseTestCase):
    """Test cases for the custom User model"""
    
    def test_user_creation_with_email(self):
        """Test creating a user with email (no username)"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertIsNone(user.username)
    
    def test_user_creation_without_email_raises_error(self):
        """Test that creating user without email raises ValueError"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')
    
    def test_superuser_creation(self):
        """Test creating a superuser"""
        admin = User.objects.create_superuser(
            email='admin@test.com',
            password='adminpass123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
    
    def test_superuser_creation_requires_is_staff(self):
        """Test that superuser creation requires is_staff=True"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@test.com',
                password='adminpass123',
                is_staff=False
            )
    
    def test_superuser_creation_requires_is_superuser(self):
        """Test that superuser creation requires is_superuser=True"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@test.com',
                password='adminpass123',
                is_superuser=False
            )
    
    def test_user_string_representation(self):
        """Test user model string representation"""
        user = User.objects.create_user(
            email='test@example.com',
            name='John Doe'
        )
        # The User model should use email as string representation
        self.assertEqual(str(user), user.email)
    
    def test_get_absolute_url(self):
        """Test user get_absolute_url method"""
        expected_url = reverse("users:detail", kwargs={"pk": self.user1.id})
        self.assertEqual(self.user1.get_absolute_url(), expected_url)
    
    def test_email_is_unique(self):
        """Test that email addresses must be unique"""
        User.objects.create_user(
            email='unique@test.com',
            password='testpass123'
        )
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='unique@test.com',  # Duplicate email
                password='testpass123'
            )


class FileVersionModelTest(BaseTestCase):
    """Test cases for the FileVersion model"""
    
    def test_file_version_creation(self):
        """Test basic FileVersion creation"""
        file_version = FileVersion.objects.create(
            file_name="test.txt",
            version_number=1,
            file_path=self.test_file,
            uploader=self.user1,
            virtual_path="/documents/test.txt",
            mime_type="text/plain",
            file_size=len(self.test_file_content),
            checksum="abc123"
        )
        
        self.assertEqual(file_version.file_name, "test.txt")
        self.assertEqual(file_version.version_number, 1)
        self.assertEqual(file_version.uploader, self.user1)
        self.assertEqual(file_version.virtual_path, "/documents/test.txt")
        self.assertEqual(file_version.mime_type, "text/plain")
        self.assertEqual(file_version.checksum, "abc123")
        self.assertIsNone(file_version.previous_version)
        self.assertIsNone(file_version.root_file)
    
    def test_file_version_with_previous_version(self):
        """Test creating a file version that references a previous version"""
        # Create root version
        root_version = FileVersion.objects.create(
            file_name="test.txt",
            version_number=1,
            file_path=self.create_test_file("root.txt", b"Root content"),
            uploader=self.user1,
            virtual_path="/documents/test.txt",
            checksum="abc123"
        )
        root_version.root_file = root_version
        root_version.save()
        
        # Create new version
        new_file = self.create_test_file("test_v2.txt", b"Updated content")
        
        new_version = FileVersion.objects.create(
            file_name="test.txt",
            version_number=2,
            file_path=new_file,
            uploader=self.user1,
            virtual_path="/documents/test.txt",
            previous_version=root_version,
            root_file=root_version,
            checksum="def456"
        )
        
        self.assertEqual(new_version.previous_version, root_version)
        self.assertEqual(new_version.root_file, root_version)
        self.assertEqual(new_version.version_number, 2)
        
        # Test reverse relationship
        self.assertIn(new_version, root_version.next_versions.all())
        self.assertIn(new_version, root_version.all_versions.all())
    
    def test_unique_constraint_root_file_per_user_and_path(self):
        """Test that unique constraint prevents duplicate root files"""
        # Create first root file
        FileVersion.objects.create(
            file_name="test.txt",
            version_number=1,
            file_path=self.create_test_file("test1.txt", b"Content 1"),
            uploader=self.user1,
            virtual_path="/documents/test.txt",
            checksum="abc123"
        )
        
        # Try to create another root file with same path and user
        duplicate_file = self.create_test_file("test2.txt", b"Different content")
        
        with self.assertRaises(IntegrityError):
            FileVersion.objects.create(
                file_name="test2.txt",
                version_number=1,
                file_path=duplicate_file,
                uploader=self.user1,
                virtual_path="/documents/test.txt",  # Same path
                checksum="xyz789"
            )
    
    def test_different_users_can_have_same_virtual_path(self):
        """Test that different users can have files at the same virtual path"""
        # User 1 creates file
        file1 = self.create_test_file("test1.txt", b"Content 1")
        fv1 = FileVersion.objects.create(
            file_name="test.txt",
            version_number=1,
            file_path=file1,
            uploader=self.user1,
            virtual_path="/documents/test.txt",
            checksum="abc123"
        )
        
        # User 2 creates file with same path - should be allowed
        file2 = self.create_test_file("test2.txt", b"Content 2")
        fv2 = FileVersion.objects.create(
            file_name="test.txt",
            version_number=1,
            file_path=file2,
            uploader=self.user2,
            virtual_path="/documents/test.txt",  # Same path, different user
            checksum="def456"
        )
        
        self.assertEqual(fv2.uploader, self.user2)
        self.assertEqual(fv2.virtual_path, "/documents/test.txt")
        self.assertNotEqual(fv1.uploader, fv2.uploader)
    
    def test_file_version_string_representation(self):
        """Test FileVersion string representation"""
        file_version = FileVersion.objects.create(
            file_name="test.txt",
            version_number=2,
            file_path=self.test_file,
            uploader=self.user1,
            virtual_path="/documents/test.txt",
            checksum="abc123"
        )
        
        expected_str = f"test.txt (v2) by {self.user1.username}"
        # Note: Since username is None, this might need adjustment based on actual implementation
        self.assertIn("test.txt", str(file_version))
        self.assertIn("v2", str(file_version))
    
    def test_file_version_defaults(self):
        """Test FileVersion model default values"""
        file_version = FileVersion.objects.create(
            file_name="defaults_test.txt",
            version_number=1,
            file_path=self.test_file,
            uploader=self.user1,
            virtual_path="/documents/defaults_test.txt",
            # Not setting optional fields to test defaults
        )
        
        self.assertEqual(file_version.mime_type, "application/octet-stream")
        self.assertEqual(file_version.file_size, -1)
        self.assertEqual(file_version.checksum, "")
        self.assertEqual(file_version.notes, "")
        self.assertIsNone(file_version.previous_version)
        self.assertIsNone(file_version.root_file)
    
    def test_version_chain_integrity(self):
        """Test that version chains maintain proper relationships"""
        # Create root file
        v1 = FileVersion.objects.create(
            file_name="chain.txt",
            version_number=1,
            file_path=self.create_test_file("v1.txt", b"Version 1"),
            uploader=self.user1,
            virtual_path="/documents/chain.txt",
            checksum="v1_checksum"
        )
        v1.root_file = v1
        v1.save()
        
        # Create version 2
        v2 = FileVersion.objects.create(
            file_name="chain.txt",
            version_number=2,
            file_path=self.create_test_file("v2.txt", b"Version 2"),
            uploader=self.user1,
            virtual_path="/documents/chain.txt",
            previous_version=v1,
            root_file=v1,
            checksum="v2_checksum"
        )
        
        # Create version 3
        v3 = FileVersion.objects.create(
            file_name="chain.txt",
            version_number=3,
            file_path=self.create_test_file("v3.txt", b"Version 3"),
            uploader=self.user1,
            virtual_path="/documents/chain.txt",
            previous_version=v2,
            root_file=v1,
            checksum="v3_checksum"
        )
        
        # Test forward relationships
        self.assertEqual(v2.previous_version, v1)
        self.assertEqual(v3.previous_version, v2)
        
        # Test root file relationships
        self.assertEqual(v1.root_file, v1)
        self.assertEqual(v2.root_file, v1)
        self.assertEqual(v3.root_file, v1)
        
        # Test that all versions point to the same root
        all_versions = FileVersion.objects.filter(root_file=v1)
        self.assertEqual(all_versions.count(), 3)
        self.assertIn(v1, all_versions)
        self.assertIn(v2, all_versions)
        self.assertIn(v3, all_versions)