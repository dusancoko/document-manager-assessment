# src/tests/test_file_operations.py
"""
Test cases for file upload, versioning, and related operations
"""

from django.urls import reverse
from rest_framework import status

from propylon_document_manager.file_versions.models import FileVersion
from .base import BaseAPITestCase


class FileUploadAPITest(BaseAPITestCase):
    """Test cases for file upload functionality"""
    
    def setUp(self):
        super().setUp()
        self.upload_url = reverse('file_upload')
    
    def test_file_upload_requires_authentication(self):
        """Test that file upload requires authentication"""
        file_data = self.create_test_file("test.txt", b"content")
        data = {
            'file': file_data,
            'virtual_path': '/documents/test.txt',
            'name': 'test.txt'
        }
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_successful_file_upload(self):
        """Test successful file upload"""
        self.authenticate_user1()
        
        file_data = self.create_test_file("test.txt", b"test content")
        data = {
            'file': file_data,
            'virtual_path': '/documents/test.txt',
            'name': 'test.txt'
        }
        
        response = self.client.post(self.upload_url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('version', response.data)
        self.assertIn('checksum', response.data)
        self.assertEqual(response.data['version'], 1)
        
        # Verify file was created in database
        file_version = FileVersion.objects.get(virtual_path='/documents/test.txt')
        self.assertEqual(file_version.file_name, 'test.txt')
        self.assertEqual(file_version.uploader, self.user1)
        self.assertEqual(file_version.version_number, 1)
        self.assertEqual(file_version.root_file, file_version)
    
    def test_file_upload_creates_new_version(self):
        """Test that uploading to existing path creates new version"""
        self.authenticate_user1()
        
        # Upload first version
        file_data1 = self.create_test_file("test.txt", b"version 1 content")
        data1 = {
            'file': file_data1,
            'virtual_path': '/documents/test.txt',
            'name': 'test.txt'
        }
        response1 = self.client.post(self.upload_url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data['version'], 1)
        
        # Upload second version
        file_data2 = self.create_test_file("test.txt", b"version 2 content")
        data2 = {
            'file': file_data2,
            'virtual_path': '/documents/test.txt',  # Same path
            'name': 'test.txt'
        }
        response2 = self.client.post(self.upload_url, data2, format='multipart')
        
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data['version'], 2)
        
        # Verify both versions exist
        versions = FileVersion.objects.filter(virtual_path='/documents/test.txt').order_by('version_number')
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version_number, 1)
        self.assertEqual(versions[1].version_number, 2)
        self.assertEqual(versions[1].previous_version, versions[0])
        self.assertEqual(versions[1].root_file, versions[0])
    
    def test_upload_identical_file_rejected(self):
        """Test that uploading identical content is rejected"""
        self.authenticate_user1()
        
        # Upload first file
        file_content = b"identical content"
        file_data1 = self.create_test_file("test.txt", file_content)
        data1 = {
            'file': file_data1,
            'virtual_path': '/documents/test.txt',
            'name': 'test.txt'
        }
        response1 = self.client.post(self.upload_url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Try to upload identical content
        file_data2 = self.create_test_file("test.txt", file_content)
        data2 = {
            'file': file_data2,
            'virtual_path': '/documents/test.txt',
            'name': 'test.txt'
        }
        response2 = self.client.post(self.upload_url, data2, format='multipart')
        
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Identical file already uploaded', str(response2.data))
    
    def test_upload_missing_file(self):
        """Test upload with missing file"""
        self.authenticate_user1()
        
        data = {
            'virtual_path': '/documents/test.txt',
            'name': 'test.txt'
        }
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
    
    def test_upload_missing_virtual_path(self):
        """Test upload with missing virtual_path"""
        self.authenticate_user1()
        
        file_data = self.create_test_file("test.txt", b"content")
        data = {
            'file': file_data,
            'name': 'test.txt'
        }
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('virtual_path', response.data)
    
    def test_upload_auto_generates_name(self):
        """Test that name is auto-generated from filename if not provided"""
        self.authenticate_user1()
        
        file_data = self.create_test_file("auto_name.txt", b"content")
        data = {
            'file': file_data,
            'virtual_path': '/documents/auto_name.txt'
            # name not provided
        }
        response = self.client.post(self.upload_url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that file was created with the original filename
        file_version = FileVersion.objects.get(virtual_path='/documents/auto_name.txt')
        self.assertEqual(file_version.file_name, 'auto_name.txt')
    
    def test_upload_generates_checksum(self):
        """Test that upload generates SHA256 checksum"""
        self.authenticate_user1()
        
        file_content = b"content for checksum test"
        file_data = self.create_test_file("checksum_test.txt", file_content)
        data = {
            'file': file_data,
            'virtual_path': '/documents/checksum_test.txt',
            'name': 'checksum_test.txt'
        }
        
        response = self.client.post(self.upload_url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('checksum', response.data)
        
        # Verify checksum is SHA256 (64 hex characters)
        checksum = response.data['checksum']
        self.assertEqual(len(checksum), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in checksum))
        
        # Verify checksum in database matches
        file_version = FileVersion.objects.get(virtual_path='/documents/checksum_test.txt')
        self.assertEqual(file_version.checksum, checksum)
    
    def test_upload_captures_file_metadata(self):
        """Test that upload captures file metadata correctly"""
        self.authenticate_user1()
        
        file_content = b"metadata test content"
        file_data = self.create_test_file("metadata.txt", file_content, "text/plain")
        data = {
            'file': file_data,
            'virtual_path': '/documents/metadata.txt',
            'name': 'metadata.txt'
        }
        
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        file_version = FileVersion.objects.get(virtual_path='/documents/metadata.txt')
        self.assertEqual(file_version.mime_type, 'text/plain')
        self.assertEqual(file_version.file_size, len(file_content))
    
    def test_upload_with_notes(self):
        """Test uploading file with notes"""
        self.authenticate_user1()
        
        file_data = self.create_test_file("notes_test.txt", b"content")
        data = {
            'file': file_data,
            'virtual_path': '/documents/notes_test.txt',
            'name': 'notes_test.txt',
            'notes': 'This is a test file with notes'
        }
        
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        file_version = FileVersion.objects.get(virtual_path='/documents/notes_test.txt')
        self.assertEqual(file_version.notes, 'This is a test file with notes')
    
    def test_upload_different_users_same_path(self):
        """Test that different users can upload to the same virtual path"""
        # User 1 uploads
        self.authenticate_user1()
        file_data1 = self.create_test_file("user1.txt", b"user 1 content")
        data1 = {
            'file': file_data1,
            'virtual_path': '/shared/same_name.txt',
            'name': 'same_name.txt'
        }
        response1 = self.client.post(self.upload_url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # User 2 uploads to same path - should succeed
        self.authenticate_user2()
        file_data2 = self.create_test_file("user2.txt", b"user 2 content")
        data2 = {
            'file': file_data2,
            'virtual_path': '/shared/same_name.txt',  # Same path
            'name': 'same_name.txt'
        }
        response2 = self.client.post(self.upload_url, data2, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Verify both files exist with different uploaders
        files = FileVersion.objects.filter(virtual_path='/shared/same_name.txt')
        self.assertEqual(len(files), 2)
        uploaders = {f.uploader for f in files}
        self.assertEqual(uploaders, {self.user1, self.user2})


class FileVersioningTest(BaseAPITestCase):
    """Test cases for file versioning functionality"""
    
    def setUp(self):
        super().setUp()
        self.upload_url = reverse('file_upload')
        self.authenticate_user1()
        
        # Create initial file
        file_data = self.create_test_file("versioning.txt", b"Version 1 content")
        data = {
            'file': file_data,
            'virtual_path': '/documents/versioning.txt',
            'name': 'versioning.txt'
        }
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.root_file = FileVersion.objects.get(virtual_path='/documents/versioning.txt')
    
    def test_version_chain_creation(self):
        """Test that version chains are created correctly"""
        # Upload version 2
        file_data2 = self.create_test_file("versioning_v2.txt", b"Version 2 content")
        data2 = {
            'file': file_data2,
            'virtual_path': '/documents/versioning.txt',
            'name': 'versioning.txt'
        }
        response2 = self.client.post(self.upload_url, data2, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data['version'], 2)
        
        # Upload version 3
        file_data3 = self.create_test_file("versioning_v3.txt", b"Version 3 content")
        data3 = {
            'file': file_data3,
            'virtual_path': '/documents/versioning.txt',
            'name': 'versioning.txt'
        }
        response3 = self.client.post(self.upload_url, data3, format='multipart')
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response3.data['version'], 3)
        
        # Verify version chain
        versions = FileVersion.objects.filter(
            virtual_path='/documents/versioning.txt'
        ).order_by('version_number')
        
        self.assertEqual(len(versions), 3)
        
        v1, v2, v3 = versions
        
        # Check version numbers
        self.assertEqual(v1.version_number, 1)
        self.assertEqual(v2.version_number, 2)
        self.assertEqual(v3.version_number, 3)
        
        # Check previous version links
        self.assertIsNone(v1.previous_version)
        self.assertEqual(v2.previous_version, v1)
        self.assertEqual(v3.previous_version, v2)
        
        # Check root file links
        self.assertEqual(v1.root_file, v1)
        self.assertEqual(v2.root_file, v1)
        self.assertEqual(v3.root_file, v1)
    
    def test_version_uploader_consistency(self):
        """Test that new versions maintain the original uploader"""
        original_uploader = self.root_file.uploader
        
        # Upload new version
        file_data = self.create_test_file("v2.txt", b"Version 2 content")
        data = {
            'file': file_data,
            'virtual_path': '/documents/versioning.txt',
            'name': 'versioning.txt'
        }
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        v2 = FileVersion.objects.get(version_number=2, virtual_path='/documents/versioning.txt')
        
        # New version should have the same uploader as the root file
        self.assertEqual(v2.uploader, original_uploader)
        self.assertEqual(v2.uploader, self.user1)
    
    def test_version_increments_correctly(self):
        """Test that version numbers increment correctly"""
        # Create multiple versions and verify incremental numbering
        for i in range(2, 6):  # Create versions 2, 3, 4, 5
            file_data = self.create_test_file(f"v{i}.txt", f"Version {i} content".encode())
            data = {
                'file': file_data,
                'virtual_path': '/documents/versioning.txt',
                'name': 'versioning.txt'
            }
            response = self.client.post(self.upload_url, data, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['version'], i)
        
        # Verify all versions exist with correct numbers
        versions = FileVersion.objects.filter(
            virtual_path='/documents/versioning.txt'
        ).order_by('version_number')
        
        self.assertEqual(len(versions), 5)
        for i, version in enumerate(versions, 1):
            self.assertEqual(version.version_number, i)


class FileMetadataTest(BaseAPITestCase):
    """Test cases for file metadata handling"""
    
    def setUp(self):
        super().setUp()
        self.upload_url = reverse('file_upload')
        self.authenticate_user1()
    
    def test_mime_type_detection(self):
        """Test MIME type detection for different file types"""
        test_cases = [
            ("test.txt", b"text content", "text/plain"),
            ("test.json", b'{"key": "value"}', "application/json"),
            ("test.html", b"<html></html>", "text/html"),
            ("test.css", b"body { color: red; }", "text/css"),
        ]
        
        for filename, content, expected_mime in test_cases:
            with self.subTest(filename=filename):
                file_data = self.create_test_file(filename, content, expected_mime)
                data = {
                    'file': file_data,
                    'virtual_path': f'/documents/{filename}',
                    'name': filename
                }
                
                response = self.client.post(self.upload_url, data, format='multipart')
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                
                file_version = FileVersion.objects.get(virtual_path=f'/documents/{filename}')
                self.assertEqual(file_version.mime_type, expected_mime)
    
    def test_file_size_calculation(self):
        """Test that file size is calculated correctly"""
        test_sizes = [
            (b"", 0),
            (b"a", 1),
            (b"hello world", 11),
            (b"x" * 1024, 1024),  # 1KB
            (b"y" * (1024 * 1024), 1024 * 1024),  # 1MB
        ]
        
        for content, expected_size in test_sizes:
            with self.subTest(size=expected_size):
                filename = f"size_test_{expected_size}.txt"
                file_data = self.create_test_file(filename, content)
                data = {
                    'file': file_data,
                    'virtual_path': f'/documents/{filename}',
                    'name': filename
                }
                
                response = self.client.post(self.upload_url, data, format='multipart')
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                
                file_version = FileVersion.objects.get(virtual_path=f'/documents/{filename}')
                self.assertEqual(file_version.file_size, expected_size)
    
    def test_checksum_uniqueness(self):
        """Test that different files have different checksums"""
        # Upload two different files
        file1_data = self.create_test_file("file1.txt", b"content 1")
        data1 = {
            'file': file1_data,
            'virtual_path': '/documents/file1.txt',
            'name': 'file1.txt'
        }
        response1 = self.client.post(self.upload_url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        file2_data = self.create_test_file("file2.txt", b"content 2")
        data2 = {
            'file': file2_data,
            'virtual_path': '/documents/file2.txt',
            'name': 'file2.txt'
        }
        response2 = self.client.post(self.upload_url, data2, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Checksums should be different
        checksum1 = response1.data['checksum']
        checksum2 = response2.data['checksum']
        self.assertNotEqual(checksum1, checksum2)
    
    def test_checksum_consistency(self):
        """Test that identical content produces identical checksums"""
        content = b"identical content for checksum test"
        
        # Upload same content twice to different paths
        file1_data = self.create_test_file("identical1.txt", content)
        data1 = {
            'file': file1_data,
            'virtual_path': '/documents/identical1.txt',
            'name': 'identical1.txt'
        }
        response1 = self.client.post(self.upload_url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        file2_data = self.create_test_file("identical2.txt", content)
        data2 = {
            'file': file2_data,
            'virtual_path': '/documents/identical2.txt',
            'name': 'identical2.txt'
        }
        response2 = self.client.post(self.upload_url, data2, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Checksums should be identical
        checksum1 = response1.data['checksum']
        checksum2 = response2.data['checksum']
        self.assertEqual(checksum1, checksum2)


class ContentAddressableStorageTest(BaseAPITestCase):
    """Test cases for Content Addressable Storage functionality"""
    
    def setUp(self):
        super().setUp()
        self.upload_url = reverse('file_upload')
        self.authenticate_user1()
    
    def test_cas_prevents_duplicate_content(self):
        """Test that CAS prevents storing duplicate content"""
        content = b"duplicate content test"
        
        # Upload first file
        file1_data = self.create_test_file("original.txt", content)
        data1 = {
            'file': file1_data,
            'virtual_path': '/documents/original.txt',
            'name': 'original.txt'
        }
        response1 = self.client.post(self.upload_url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Try to upload identical content as new version
        file2_data = self.create_test_file("duplicate.txt", content)
        data2 = {
            'file': file2_data,
            'virtual_path': '/documents/original.txt',  # Same path
            'name': 'original.txt'
        }
        response2 = self.client.post(self.upload_url, data2, format='multipart')
        
        # Should be rejected due to identical content
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Identical file already uploaded', str(response2.data))
    
    def test_cas_allows_different_content_same_path(self):
        """Test that CAS allows different content at the same path"""
        # Upload first version
        file1_data = self.create_test_file("file.txt", b"version 1 content")
        data1 = {
            'file': file1_data,
            'virtual_path': '/documents/file.txt',
            'name': 'file.txt'
        }
        response1 = self.client.post(self.upload_url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Upload different content to same path
        file2_data = self.create_test_file("file.txt", b"version 2 content")
        data2 = {
            'file': file2_data,
            'virtual_path': '/documents/file.txt',  # Same path
            'name': 'file.txt'
        }
        response2 = self.client.post(self.upload_url, data2, format='multipart')
        
        # Should succeed because content is different
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data['version'], 2)
    
    def test_cas_works_across_different_paths(self):
        """Test that CAS works across different virtual paths"""
        content = b"shared content across paths"
        
        # Upload to first path
        file1_data = self.create_test_file("path1.txt", content)
        data1 = {
            'file': file1_data,
            'virtual_path': '/documents/path1.txt',
            'name': 'path1.txt'
        }
        response1 = self.client.post(self.upload_url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Upload identical content to different path - should succeed
        file2_data = self.create_test_file("path2.txt", content)
        data2 = {
            'file': file2_data,
            'virtual_path': '/documents/path2.txt',  # Different path
            'name': 'path2.txt'
        }
        response2 = self.client.post(self.upload_url, data2, format='multipart')
        
        # Should succeed because it's a different virtual path (new root file)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # But checksums should be the same
        self.assertEqual(response1.data['checksum'], response2.data['checksum'])
    
    def test_checksum_based_deduplication(self):
        """Test that checksum-based deduplication works correctly"""
        # Create file with specific content
        content = b"checksum test content"
        expected_checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # SHA256 of empty string
        
        # Calculate actual checksum for our content
        import hashlib
        actual_checksum = hashlib.sha256(content).hexdigest()
        
        file_data = self.create_test_file("checksum.txt", content)
        data = {
            'file': file_data,
            'virtual_path': '/documents/checksum.txt',
            'name': 'checksum.txt'
        }
        
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['checksum'], actual_checksum)
        
        # Verify checksum in database
        file_version = FileVersion.objects.get(virtual_path='/documents/checksum.txt')
        self.assertEqual(file_version.checksum, actual_checksum)