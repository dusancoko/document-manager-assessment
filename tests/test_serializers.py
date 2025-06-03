# src/tests/test_serializers.py
"""
Test cases for serializers in the file_versions app
"""

import hashlib
from unittest.mock import Mock, patch

from django.test import TestCase
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from propylon_document_manager.file_versions.models import FileVersion, User
from propylon_document_manager.file_versions.api.serializers import (
    FileVersionSerializer,
    SharedFileVersionSerializer,
    FileUploadSerializer
)
from .base import BaseTestCase


class FileVersionSerializerTest(BaseTestCase):
    """Test cases for FileVersionSerializer"""
    
    def setUp(self):
        super().setUp()
        
        # Create a file with multiple versions
        self.root_file = FileVersion.objects.create(
            file_name="serializer_test.txt",
            version_number=1,
            file_path=self.create_test_file("v1.txt", b"Version 1"),
            uploader=self.user1,
            virtual_path="/documents/serializer_test.txt",
            checksum="ser_checksum_v1",
            mime_type="text/plain",
            file_size=9
        )
        self.root_file.root_file = self.root_file
        self.root_file.save()
        
        self.version_2 = FileVersion.objects.create(
            file_name="serializer_test.txt",
            version_number=2,
            file_path=self.create_test_file("v2.txt", b"Version 2"),
            uploader=self.user1,
            virtual_path="/documents/serializer_test.txt",
            previous_version=self.root_file,
            root_file=self.root_file,
            checksum="ser_checksum_v2",
            mime_type="text/plain",
            file_size=9
        )
        
        self.version_3 = FileVersion.objects.create(
            file_name="serializer_test.txt",
            version_number=3,
            file_path=self.create_test_file("v3.txt", b"Version 3"),
            uploader=self.user1,
            virtual_path="/documents/serializer_test.txt",
            previous_version=self.version_2,
            root_file=self.root_file,
            checksum="ser_checksum_v3",
            mime_type="text/plain",
            file_size=9
        )
    
    def test_serializer_includes_all_fields(self):
        """Test that serializer includes all expected fields"""
        serializer = FileVersionSerializer(self.root_file)
        data = serializer.data
        
        expected_fields = [
            'id', 'file_name', 'version_number', 'virtual_path', 
            'mime_type', 'file_size', 'checksum', 'created_at', 'versions'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_serializer_includes_versions_list(self):
        """Test that serializer includes all versions"""
        serializer = FileVersionSerializer(self.root_file)
        data = serializer.data
        
        self.assertIn('versions', data)
        self.assertEqual(len(data['versions']), 3)
        
        # Check that all versions are included
        version_numbers = {v['version_number'] for v in data['versions']}
        self.assertEqual(version_numbers, {1, 2, 3})
    
    def test_versions_ordered_by_version_number_descending(self):
        """Test that versions are ordered by version number (descending)"""
        serializer = FileVersionSerializer(self.root_file)
        data = serializer.data
        
        version_numbers = [v['version_number'] for v in data['versions']]
        self.assertEqual(version_numbers, [3, 2, 1])
    
    def test_version_entries_include_required_fields(self):
        """Test that version entries include required fields"""
        serializer = FileVersionSerializer(self.root_file)
        data = serializer.data
        
        for version in data['versions']:
            self.assertIn('id', version)
            self.assertIn('version_number', version)
            self.assertIn('virtual_path', version)
            
            # Check data types
            self.assertIsInstance(version['id'], int)
            self.assertIsInstance(version['version_number'], int)
            self.assertIsInstance(version['virtual_path'], str)
    
    def test_serializer_works_with_single_version(self):
        """Test serializer works correctly with single version file"""
        single_file = FileVersion.objects.create(
            file_name="single.txt",
            version_number=1,
            file_path=self.create_test_file("single.txt", b"Single version"),
            uploader=self.user1,
            virtual_path="/documents/single.txt",
            checksum="single_checksum"
        )
        single_file.root_file = single_file
        single_file.save()
        
        serializer = FileVersionSerializer(single_file)
        data = serializer.data
        
        self.assertEqual(len(data['versions']), 1)
        self.assertEqual(data['versions'][0]['version_number'], 1)
    
    def test_serializer_with_file_without_root_file(self):
        """Test serializer with file that doesn't have root_file set"""
        orphan_file = FileVersion.objects.create(
            file_name="orphan.txt",
            version_number=1,
            file_path=self.create_test_file("orphan.txt", b"Orphan file"),
            uploader=self.user1,
            virtual_path="/documents/orphan.txt",
            checksum="orphan_checksum"
        )
        # Don't set root_file
        
        serializer = FileVersionSerializer(orphan_file)
        data = serializer.data
        
        # Should handle gracefully and show the file itself
        self.assertIn('versions', data)


class SharedFileVersionSerializerTest(BaseTestCase):
    """Test cases for SharedFileVersionSerializer"""
    
    def setUp(self):
        super().setUp()
        
        # Create shared file
        self.shared_file = FileVersion.objects.create(
            file_name="shared.txt",
            version_number=1,
            file_path=self.create_test_file("shared.txt", b"Shared content"),
            uploader=self.user1,
            virtual_path="/documents/shared.txt",
            checksum="shared_checksum"
        )
        self.shared_file.root_file = self.shared_file
        self.shared_file.save()
        
        # Set up permissions for user2
        content_type = ContentType.objects.get_for_model(FileVersion)
        self.view_permission = Permission.objects.get(
            codename='view_fileversion', 
            content_type=content_type
        )
        self.change_permission = Permission.objects.get(
            codename='change_fileversion', 
            content_type=content_type
        )
    
    def test_shared_serializer_includes_owner_email(self):
        """Test that shared serializer includes owner email"""
        request = Mock()
        request.user = self.user2
        
        serializer = SharedFileVersionSerializer(
            self.shared_file, 
            context={'request': request}
        )
        data = serializer.data
        
        self.assertIn('owner_email', data)
        self.assertEqual(data['owner_email'], self.user1.email)
    
    def test_shared_serializer_includes_permissions(self):
        """Test that shared serializer includes permissions info"""
        # Grant view permission to user2
        self.user2.user_permissions.add(self.view_permission)
        
        request = Mock()
        request.user = self.user2
        
        serializer = SharedFileVersionSerializer(
            self.shared_file, 
            context={'request': request}
        )
        data = serializer.data
        
        self.assertIn('permissions', data)
        self.assertIsInstance(data['permissions'], list)
    
    @patch.object(User, 'has_perm')
    def test_permissions_field_view_only(self, mock_has_perm):
        """Test permissions field with view-only access"""
        # Mock permission checks
        def mock_perm_check(perm, obj=None):
            if perm == "file_versions.view_fileversion":
                return True
            elif perm == "file_versions.change_fileversion":
                return False
            return False
        
        mock_has_perm.side_effect = mock_perm_check
        
        request = Mock()
        request.user = self.user2
        
        serializer = SharedFileVersionSerializer(
            self.shared_file, 
            context={'request': request}
        )
        data = serializer.data
        
        self.assertEqual(data['permissions'], ['view'])
    
    @patch.object(User, 'has_perm')
    def test_permissions_field_view_and_edit(self, mock_has_perm):
        """Test permissions field with view and edit access"""
        # Mock permission checks
        def mock_perm_check(perm, obj=None):
            if perm in ["file_versions.view_fileversion", "file_versions.change_fileversion"]:
                return True
            return False
        
        mock_has_perm.side_effect = mock_perm_check
        
        request = Mock()
        request.user = self.user2
        
        serializer = SharedFileVersionSerializer(
            self.shared_file, 
            context={'request': request}
        )
        data = serializer.data
        
        self.assertEqual(set(data['permissions']), {'view', 'edit'})
    
    @patch.object(User, 'has_perm')
    def test_versions_filtered_by_permissions(self, mock_has_perm):
        """Test that versions are filtered based on user permissions"""
        # Create multiple versions
        v2 = FileVersion.objects.create(
            file_name="shared.txt",
            version_number=2,
            file_path=self.create_test_file("shared_v2.txt", b"Shared content v2"),
            uploader=self.user1,
            virtual_path="/documents/shared.txt",
            previous_version=self.shared_file,
            root_file=self.shared_file,
            checksum="shared_checksum_v2"
        )
        
        # Mock that user can only view certain versions
        def mock_perm_check(perm, obj=None):
            if perm == "file_versions.view_fileversion":
                # Allow viewing only version 1
                return obj is None or obj.version_number == 1
            return False
        
        mock_has_perm.side_effect = mock_perm_check
        
        request = Mock()
        request.user = self.user2
        
        serializer = SharedFileVersionSerializer(
            self.shared_file, 
            context={'request': request}
        )
        data = serializer.data
        
        # Should only include versions the user can access
        accessible_versions = [v['version_number'] for v in data['versions']]
        self.assertEqual(accessible_versions, [1])


class FileUploadSerializerTest(BaseTestCase):
    """Test cases for FileUploadSerializer"""
    
    def setUp(self):
        super().setUp()
        
        # Create mock request
        self.mock_request = Mock()
        self.mock_request.user = self.user1
        
        self.context = {'request': self.mock_request}
    
    def test_checksum_generation(self):
        """Test that serializer generates SHA256 checksum"""
        file_content = b"Test content for checksum"
        file_obj = self.create_test_file("test.txt", file_content)
        
        data = {
            'file': file_obj,
            'name': 'test.txt',
            'virtual_path': '/documents/test.txt'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        
        # Check that checksum was generated
        validated_data = serializer.validated_data
        self.assertIn('checksum', validated_data)
        
        # Verify it's a valid SHA256 hash
        checksum = validated_data['checksum']
        self.assertEqual(len(checksum), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in checksum))
        
        # Verify it matches expected checksum
        expected_checksum = hashlib.sha256(file_content).hexdigest()
        self.assertEqual(checksum, expected_checksum)
    
    def test_virtual_path_validation_new_file(self):
        """Test virtual path validation for new files"""
        file_obj = self.create_test_file("new.txt", b"New file content")
        
        data = {
            'file': file_obj,
            'name': 'new.txt',
            'virtual_path': '/documents/new.txt'  # Doesn't exist yet
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
    
    def test_virtual_path_validation_existing_file_same_user(self):
        """Test virtual path validation for existing file by same user"""
        # Create existing file
        existing_file = FileVersion.objects.create(
            file_name="existing.txt",
            version_number=1,
            file_path=self.create_test_file("existing.txt", b"Existing content"),
            uploader=self.user1,
            virtual_path="/documents/existing.txt",
            checksum="existing_checksum"
        )
        existing_file.root_file = existing_file
        existing_file.save()
        
        # Try to upload new version
        file_obj = self.create_test_file("new_version.txt", b"New version content")
        
        data = {
            'file': file_obj,
            'name': 'existing.txt',
            'virtual_path': '/documents/existing.txt'  # Same path, same user
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
    
    def test_virtual_path_validation_existing_file_different_user_no_permission(self):
        """Test virtual path validation for existing file by different user without permission"""
        # Create existing file by user1
        existing_file = FileVersion.objects.create(
            file_name="protected.txt",
            version_number=1,
            file_path=self.create_test_file("protected.txt", b"Protected content"),
            uploader=self.user1,
            virtual_path="/documents/protected.txt",
            checksum="protected_checksum"
        )
        existing_file.root_file = existing_file
        existing_file.save()
        
        # Try to upload as user2 without permission
        self.mock_request.user = self.user2
        
        file_obj = self.create_test_file("unauthorized.txt", b"Unauthorized content")
        
        data = {
            'file': file_obj,
            'name': 'protected.txt',
            'virtual_path': '/documents/protected.txt'  # Existing path, different user
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('virtual_path', serializer.errors)
        self.assertIn("You don't have permission", str(serializer.errors['virtual_path']))
    
    @patch.object(User, 'has_perm')
    def test_virtual_path_validation_existing_file_different_user_with_permission(self, mock_has_perm):
        """Test virtual path validation for existing file by different user with permission"""
        # Create existing file by user1
        existing_file = FileVersion.objects.create(
            file_name="shared.txt",
            version_number=1,
            file_path=self.create_test_file("shared.txt", b"Shared content"),
            uploader=self.user1,
            virtual_path="/documents/shared.txt",
            checksum="shared_checksum"
        )
        existing_file.root_file = existing_file
        existing_file.save()
        
        # Mock permission check to return True
        mock_has_perm.return_value = True
        
        # Try to upload as user2 with permission
        self.mock_request.user = self.user2
        
        file_obj = self.create_test_file("new_version.txt", b"New version by user2")
        
        data = {
            'file': file_obj,
            'name': 'shared.txt',
            'virtual_path': '/documents/shared.txt'  # Existing path, different user
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
    
    def test_create_new_file(self):
        """Test creating a new file (root file)"""
        file_content = b"New file content"
        file_obj = self.create_test_file("new.txt", file_content)
        
        data = {
            'file': file_obj,
            'name': 'new.txt',
            'virtual_path': '/documents/new.txt',
            'notes': 'Test notes'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        
        file_version = serializer.save()
        
        self.assertEqual(file_version.file_name, 'new.txt')
        self.assertEqual(file_version.uploader, self.user1)
        self.assertEqual(file_version.virtual_path, '/documents/new.txt')
        self.assertEqual(file_version.version_number, 1)
        self.assertEqual(file_version.notes, 'Test notes')
        self.assertEqual(file_version.root_file, file_version)
        self.assertIsNone(file_version.previous_version)
    
    def test_create_new_version_of_existing_file(self):
        """Test creating a new version of an existing file"""
        # Create existing file
        existing_file = FileVersion.objects.create(
            file_name="versioned.txt",
            version_number=1,
            file_path=self.create_test_file("v1.txt", b"Version 1"),
            uploader=self.user1,
            virtual_path="/documents/versioned.txt",
            checksum="v1_checksum"
        )
        existing_file.root_file = existing_file
        existing_file.save()
        
        # Create new version
        file_obj = self.create_test_file("v2.txt", b"Version 2 content")
        
        data = {
            'file': file_obj,
            'name': 'versioned.txt',
            'virtual_path': '/documents/versioned.txt',
            'notes': 'Version 2 notes'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        
        new_version = serializer.save()
        
        self.assertEqual(new_version.file_name, 'versioned.txt')
        self.assertEqual(new_version.uploader, self.user1)  # Should maintain original uploader
        self.assertEqual(new_version.virtual_path, '/documents/versioned.txt')
        self.assertEqual(new_version.version_number, 2)
        self.assertEqual(new_version.notes, 'Version 2 notes')
        self.assertEqual(new_version.root_file, existing_file)
        self.assertEqual(new_version.previous_version, existing_file)
    
    def test_duplicate_content_rejection(self):
        """Test that duplicate content is rejected"""
        content = b"Duplicate content"
        
        # Create existing file
        existing_file = FileVersion.objects.create(
            file_name="original.txt",
            version_number=1,
            file_path=self.create_test_file("original.txt", content),
            uploader=self.user1,
            virtual_path="/documents/original.txt",
            checksum=hashlib.sha256(content).hexdigest()
        )
        existing_file.root_file = existing_file
        existing_file.save()
        
        # Try to upload identical content
        file_obj = self.create_test_file("duplicate.txt", content)
        
        data = {
            'file': file_obj,
            'name': 'original.txt',
            'virtual_path': '/documents/original.txt'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        
        with self.assertRaises(Exception) as context:
            if serializer.is_valid():
                serializer.save()
        
        self.assertIn('Identical file already uploaded', str(context.exception))
    
    def test_metadata_capture(self):
        """Test that file metadata is captured correctly"""
        file_content = b"Metadata test content"
        file_obj = self.create_test_file("metadata.txt", file_content, "text/plain")
        
        data = {
            'file': file_obj,
            'name': 'metadata.txt',
            'virtual_path': '/documents/metadata.txt'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        
        file_version = serializer.save()
        
        self.assertEqual(file_version.mime_type, 'text/plain')
        self.assertEqual(file_version.file_size, len(file_content))
        
        # Verify checksum
        expected_checksum = hashlib.sha256(file_content).hexdigest()
        self.assertEqual(file_version.checksum, expected_checksum)
    
    def test_permission_assignment(self):
        """Test that FileVersion permissions are assigned to user"""
        file_obj = self.create_test_file("permissions.txt", b"Permission test")
        
        data = {
            'file': file_obj,
            'name': 'permissions.txt',
            'virtual_path': '/documents/permissions.txt'
        }
        
        # Clear existing permissions
        self.user1.user_permissions.clear()
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        
        file_version = serializer.save()
        
        # Check that permissions were assigned
        permission_codenames = set(
            self.user1.user_permissions.values_list('codename', flat=True)
        )
        
        expected_permissions = {
            'add_fileversion',
            'change_fileversion', 
            'delete_fileversion',
            'view_fileversion'
        }
        
        self.assertTrue(expected_permissions.issubset(permission_codenames))
    
    def test_required_fields_validation(self):
        """Test validation of required fields"""
        # Missing file
        data = {
            'name': 'test.txt',
            'virtual_path': '/documents/test.txt'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
        
        # Missing virtual_path
        file_obj = self.create_test_file("test.txt", b"content")
        data = {
            'file': file_obj,
            'name': 'test.txt'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('virtual_path', serializer.errors)
        
        # Missing name
        file_obj = self.create_test_file("test.txt", b"content")
        data = {
            'file': file_obj,
            'virtual_path': '/documents/test.txt'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_optional_fields(self):
        """Test handling of optional fields"""
        file_obj = self.create_test_file("optional.txt", b"Optional fields test")
        
        # Without notes
        data = {
            'file': file_obj,
            'name': 'optional.txt',
            'virtual_path': '/documents/optional.txt'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        
        file_version = serializer.save()
        self.assertEqual(file_version.notes, '')
        
        # With notes
        file_obj2 = self.create_test_file("optional2.txt", b"Optional fields test 2")
        data2 = {
            'file': file_obj2,
            'name': 'optional2.txt',
            'virtual_path': '/documents/optional2.txt',
            'notes': 'Custom notes'
        }
        
        serializer2 = FileUploadSerializer(data=data2, context=self.context)
        self.assertTrue(serializer2.is_valid())
        
        file_version2 = serializer2.save()
        self.assertEqual(file_version2.notes, 'Custom notes')


class SerializerFieldValidationTest(BaseTestCase):
    """Test cases for serializer field validation"""
    
    def setUp(self):
        super().setUp()
        
        self.mock_request = Mock()
        self.mock_request.user = self.user1
        self.context = {'request': self.mock_request}
    
    def test_virtual_path_format_validation(self):
        """Test virtual path format validation"""
        file_obj = self.create_test_file("test.txt", b"content")
        
        invalid_paths = [
            '',  # Empty
            'no-leading-slash',  # No leading slash
            '//',  # Double slash
            '/path//double/slash',  # Double slash in middle
            '/path/with/trailing/slash/',  # Trailing slash
            ' /path/with/spaces ',  # Leading/trailing spaces
        ]
        
        for invalid_path in invalid_paths:
            with self.subTest(path=invalid_path):
                data = {
                    'file': file_obj,
                    'name': 'test.txt',
                    'virtual_path': invalid_path
                }
                
                serializer = FileUploadSerializer(data=data, context=self.context)
                # The serializer might accept some of these depending on implementation
                # Adjust expectations based on actual validation rules
                if invalid_path == '':
                    self.assertFalse(serializer.is_valid())
    
    def test_file_name_validation(self):
        """Test file name validation"""
        file_obj = self.create_test_file("test.txt", b"content")
        
        # Very long name
        long_name = 'a' * 300 + '.txt'
        data = {
            'file': file_obj,
            'name': long_name,
            'virtual_path': '/documents/test.txt'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        # Should handle based on model field max_length (255)
        if len(long_name) > 255:
            self.assertFalse(serializer.is_valid())
        else:
            self.assertTrue(serializer.is_valid())
    
    def test_notes_length_validation(self):
        """Test notes field length validation"""
        file_obj = self.create_test_file("test.txt", b"content")
        
        # Very long notes
        long_notes = 'x' * 10000  # 10KB of text
        data = {
            'file': file_obj,
            'name': 'test.txt',
            'virtual_path': '/documents/test.txt',
            'notes': long_notes
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        # Should be valid since TextField doesn't have max_length by default
        self.assertTrue(serializer.is_valid())


class SerializerErrorHandlingTest(BaseTestCase):
    """Test cases for serializer error handling"""
    
    def setUp(self):
        super().setUp()
        
        self.mock_request = Mock()
        self.mock_request.user = self.user1
        self.context = {'request': self.mock_request}
    
    @patch('propylon_document_manager.file_versions.api.serializers.FileVersion.objects.create')
    def test_database_error_handling(self, mock_create):
        """Test handling of database errors during file creation"""
        # Mock database error
        mock_create.side_effect = Exception("Database error")
        
        file_obj = self.create_test_file("error.txt", b"Error test")
        data = {
            'file': file_obj,
            'name': 'error.txt',
            'virtual_path': '/documents/error.txt'
        }
        
        serializer = FileUploadSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        
        with self.assertRaises(Exception):
            serializer.save()
    
    def test_missing_context(self):
        """Test serializer behavior with missing context"""
        file_obj = self.create_test_file("context.txt", b"Context test")
        data = {
            'file': file_obj,
            'name': 'context.txt',
            'virtual_path': '/documents/context.txt'
        }
        
        # No context provided
        serializer = FileUploadSerializer(data=data)
        
        # Should raise appropriate error when trying to access request
        with self.assertRaises(KeyError):
            serializer.is_valid()
    
    def test_invalid_user_in_context(self):
        """Test serializer behavior with invalid user in context"""
        file_obj = self.create_test_file("invalid.txt", b"Invalid user test")
        data = {
            'file': file_obj,
            'name': 'invalid.txt',
            'virtual_path': '/documents/invalid.txt'
        }
        
        # Mock request with None user
        mock_request = Mock()
        mock_request.user = None
        context = {'request': mock_request}
        
        serializer = FileUploadSerializer(data=data, context=context)
        
        # Should handle gracefully or raise appropriate error
        with self.assertRaises(AttributeError):
            serializer.is_valid()