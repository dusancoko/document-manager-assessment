# src/tests/test_api_views.py
"""
Test cases for API views and endpoints
"""

from django.urls import reverse
from rest_framework import status

from propylon_document_manager.file_versions.models import FileVersion
from .base import BaseAPITestCase


class FileVersionAPITest(BaseAPITestCase):
    """Test cases for FileVersion API endpoints"""
    
    def setUp(self):
        super().setUp()
        
        # Create test files for both users
        self.file1 = FileVersion.objects.create(
            file_name="user1_file.txt",
            version_number=1,
            file_path=self.create_test_file("test1.txt", b"User 1 content"),
            uploader=self.user1,
            virtual_path="/documents/user1_file.txt",
            checksum="user1_checksum",
            mime_type="text/plain",
            file_size=13
        )
        
        self.file2 = FileVersion.objects.create(
            file_name="user2_file.txt", 
            version_number=1,
            file_path=self.create_test_file("test2.txt", b"User 2 content"),
            uploader=self.user2,
            virtual_path="/documents/user2_file.txt",
            checksum="user2_checksum",
            mime_type="text/plain",
            file_size=13
        )
        
        # Set root_file references
        self.file1.root_file = self.file1
        self.file1.save()
        self.file2.root_file = self.file2
        self.file2.save()
    
    def test_list_files_requires_authentication(self):
        """Test that listing files requires authentication"""
        url = reverse('api:fileversion-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_files_shows_only_user_files(self):
        """Test that users only see their own files"""
        self.authenticate_user1()
        url = reverse('api:fileversion-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['file_name'], 'user1_file.txt')
        self.assertEqual(response.data[0]['id'], self.file1.id)
    
    def test_list_files_excludes_non_root_versions(self):
        """Test that file list only shows root versions (not all versions)"""
        # Create a second version of user1's file
        version_2 = FileVersion.objects.create(
            file_name="user1_file.txt",
            version_number=2,
            file_path=self.create_test_file("test1_v2.txt", b"User 1 updated content"),
            uploader=self.user1,
            virtual_path="/documents/user1_file.txt",
            previous_version=self.file1,
            root_file=self.file1,
            checksum="user1_checksum_v2"
        )
        
        self.authenticate_user1()
        url = reverse('api:fileversion-list')
        response = self.client.get(url)
        
        # Should still only show 1 file (the root file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.file1.id)
        
        # But the versions should include both versions
        self.assertIn('versions', response.data[0])
        self.assertEqual(len(response.data[0]['versions']), 2)
    
    def test_retrieve_file_detail(self):
        """Test retrieving file details"""
        self.authenticate_user1()
        url = reverse('api:fileversion-detail', kwargs={'id': self.file1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['file_name'], 'user1_file.txt')
        self.assertEqual(response.data['virtual_path'], '/documents/user1_file.txt')
        self.assertEqual(response.data['checksum'], 'user1_checksum')
        self.assertIn('versions', response.data)
    
    def test_cannot_retrieve_other_user_file(self):
        """Test that users cannot retrieve other users' files"""
        self.authenticate_user1()
        url = reverse('api:fileversion-detail', kwargs={'id': self.file2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retrieve_nonexistent_file(self):
        """Test retrieving non-existent file returns 404"""
        self.authenticate_user1()
        url = reverse('api:fileversion-detail', kwargs={'id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_shared_files_endpoint_empty_by_default(self):
        """Test shared-with-me endpoint returns empty list by default"""
        self.authenticate_user1()
        url = reverse('api:fileversion-shared-with-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_shared_files_endpoint_requires_authentication(self):
        """Test that shared-with-me endpoint requires authentication"""
        url = reverse('api:fileversion-shared-with-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_file_detail_includes_metadata(self):
        """Test that file detail includes all expected metadata"""
        self.authenticate_user1()
        url = reverse('api:fileversion-detail', kwargs={'id': self.file1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_fields = [
            'id', 'file_name', 'version_number', 'virtual_path', 
            'mime_type', 'file_size', 'checksum', 'created_at', 'versions'
        ]
        
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # Check data types and values
        self.assertIsInstance(response.data['id'], int)
        self.assertIsInstance(response.data['version_number'], int)
        self.assertIsInstance(response.data['file_size'], int)
        self.assertIsInstance(response.data['versions'], list)
    
    def test_versions_are_properly_ordered(self):
        """Test that versions in API response are properly ordered"""
        # Create multiple versions
        v2 = FileVersion.objects.create(
            file_name="user1_file.txt",
            version_number=2,
            file_path=self.create_test_file("v2.txt", b"Version 2"),
            uploader=self.user1,
            virtual_path="/documents/user1_file.txt",
            previous_version=self.file1,
            root_file=self.file1,
            checksum="checksum_v2"
        )
        
        v3 = FileVersion.objects.create(
            file_name="user1_file.txt",
            version_number=3,
            file_path=self.create_test_file("v3.txt", b"Version 3"),
            uploader=self.user1,
            virtual_path="/documents/user1_file.txt",
            previous_version=v2,
            root_file=self.file1,
            checksum="checksum_v3"
        )
        
        self.authenticate_user1()
        url = reverse('api:fileversion-detail', kwargs={'id': self.file1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        versions = response.data['versions']
        self.assertEqual(len(versions), 3)
        
        # Should be ordered by version_number descending (newest first)
        version_numbers = [v['version_number'] for v in versions]
        self.assertEqual(version_numbers, [3, 2, 1])


class FileComparisonAPITest(BaseAPITestCase):
    """Test cases for file comparison API"""
    
    def setUp(self):
        super().setUp()
        
        # Create two file versions for comparison
        self.file_v1 = FileVersion.objects.create(
            file_name="compare_test.txt",
            version_number=1,
            file_path=self.create_test_file("v1.txt", b"Original content\nLine 2\nLine 3"),
            uploader=self.user1,
            virtual_path="/documents/compare_test.txt",
            checksum="checksum_v1",
            mime_type="text/plain"
        )
        self.file_v1.root_file = self.file_v1
        self.file_v1.save()
        
        self.file_v2 = FileVersion.objects.create(
            file_name="compare_test.txt",
            version_number=2,
            file_path=self.create_test_file("v2.txt", b"Modified content\nLine 2\nNew Line 3"),
            uploader=self.user1,
            virtual_path="/documents/compare_test.txt",
            previous_version=self.file_v1,
            root_file=self.file_v1,
            checksum="checksum_v2",
            mime_type="text/plain"
        )
        
        self.compare_url = reverse('file_compare')
    
    def test_compare_files_requires_authentication(self):
        """Test that file comparison requires authentication"""
        response = self.client.get(self.compare_url, {
            'left_id': self.file_v1.id, 
            'right_id': self.file_v2.id
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_successful_file_comparison(self):
        """Test successful file comparison"""
        self.authenticate_user1()
        
        response = self.client.get(self.compare_url, {
            'left_id': self.file_v1.id, 
            'right_id': self.file_v2.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('left_file', response.data)
        self.assertIn('right_file', response.data)
        
        # Check file data structure
        left_file = response.data['left_file']
        right_file = response.data['right_file']
        
        self.assertIn('id', left_file)
        self.assertIn('name', left_file)
        self.assertIn('text', left_file)
        
        self.assertEqual(left_file['id'], self.file_v1.id)
        self.assertEqual(right_file['id'], self.file_v2.id)
    
    def test_compare_missing_left_id_parameter(self):
        """Test comparison with missing left_id parameter"""
        self.authenticate_user1()
        
        response = self.client.get(self.compare_url, {'right_id': self.file_v2.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Both left_id and right_id are required', response.data['detail'])
    
    def test_compare_missing_right_id_parameter(self):
        """Test comparison with missing right_id parameter"""
        self.authenticate_user1()
        
        response = self.client.get(self.compare_url, {'left_id': self.file_v1.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Both left_id and right_id are required', response.data['detail'])
    
    def test_compare_missing_both_parameters(self):
        """Test comparison with missing both parameters"""
        self.authenticate_user1()
        
        response = self.client.get(self.compare_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Both left_id and right_id are required', response.data['detail'])
    
    def test_compare_nonexistent_left_file(self):
        """Test comparison with non-existent left file ID"""
        self.authenticate_user1()
        
        response = self.client.get(self.compare_url, {
            'left_id': 99999, 
            'right_id': self.file_v2.id
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_compare_nonexistent_right_file(self):
        """Test comparison with non-existent right file ID"""
        self.authenticate_user1()
        
        response = self.client.get(self.compare_url, {
            'left_id': self.file_v1.id, 
            'right_id': 99999
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_compare_other_user_files_forbidden(self):
        """Test that users cannot compare files they don't own"""
        # Create file for user2
        other_file = FileVersion.objects.create(
            file_name="other_user_file.txt",
            version_number=1,
            file_path=self.create_test_file("other.txt", b"Other user content"),
            uploader=self.user2,
            virtual_path="/documents/other_user_file.txt",
            checksum="other_checksum",
            mime_type="text/plain"
        )
        
        self.authenticate_user1()
        
        # Try to compare user1's file with user2's file
        response = self.client.get(self.compare_url, {
            'left_id': self.file_v1.id, 
            'right_id': other_file.id
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_compare_same_file_with_itself(self):
        """Test comparing a file with itself"""
        self.authenticate_user1()
        
        response = self.client.get(self.compare_url, {
            'left_id': self.file_v1.id, 
            'right_id': self.file_v1.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Both sides should have the same content
        left_text = response.data['left_file']['text']
        right_text = response.data['right_file']['text']
        self.assertEqual(left_text, right_text)


class FileDownloadAPITest(BaseAPITestCase):
    """Test cases for file download functionality"""
    
    def setUp(self):
        super().setUp()
        
        # Create test file with known content
        self.test_content = b"Test file content for download testing"
        self.file_version = FileVersion.objects.create(
            file_name="download_test.txt",
            version_number=1,
            file_path=self.create_test_file("test.txt", self.test_content),
            uploader=self.user1,
            virtual_path="/documents/download_test.txt",
            checksum="download_checksum",
            mime_type="text/plain",
            file_size=len(self.test_content)
        )
        self.file_version.root_file = self.file_version
        self.file_version.save()
    
    def test_download_requires_token(self):
        """Test that download requires authentication token"""
        url = reverse('file_download', kwargs={'path': 'documents/download_test.txt'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        self.assertIn('Authentication token was not provided', response.content.decode())
    
    def test_download_with_invalid_token(self):
        """Test download with invalid token"""
        url = reverse('file_download', kwargs={'path': 'documents/download_test.txt'})
        response = self.client.get(url, {'token': 'invalid_token'})
        self.assertEqual(response.status_code, 403)
        self.assertIn('Invalid authentication token', response.content.decode())
    
    def test_successful_file_download(self):
        """Test successful file download by owner"""
        url = reverse('file_download', kwargs={'path': 'documents/download_test.txt'})
        response = self.client.get(url, {'token': self.token1.key})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('download_test.txt', response['Content-Disposition'])
    
    def test_download_nonexistent_file(self):
        """Test downloading non-existent file"""
        url = reverse('file_download', kwargs={'path': 'documents/nonexistent.txt'})
        response = self.client.get(url, {'token': self.token1.key})
        self.assertEqual(response.status_code, 404)
    
    def test_download_other_user_file_forbidden(self):
        """Test that users cannot download other users' files without permission"""
        url = reverse('file_download', kwargs={'path': 'documents/download_test.txt'})
        response = self.client.get(url, {'token': self.token2.key})
        self.assertEqual(response.status_code, 403)
        self.assertIn("You don't have permission to access this file", response.content.decode())
    
    def test_download_specific_revision(self):
        """Test downloading a specific revision"""
        # Create second version
        second_content = b"Updated content for version 2"
        v2 = FileVersion.objects.create(
            file_name="download_test.txt",
            version_number=2,
            file_path=self.create_test_file("test_v2.txt", second_content),
            uploader=self.user1,
            virtual_path="/documents/download_test.txt",
            previous_version=self.file_version,
            root_file=self.file_version,
            checksum="download_checksum_v2",
            mime_type="text/plain"
        )
        
        url = reverse('file_download', kwargs={'path': 'documents/download_test.txt'})
        
        # Download first version specifically
        response = self.client.get(url, {
            'token': self.token1.key, 
            'revision': '1'
        })
        self.assertEqual(response.status_code, 200)
        
        # Download latest version (should be version 2)
        response = self.client.get(url, {'token': self.token1.key})
        self.assertEqual(response.status_code, 200)
    
    def test_download_invalid_revision(self):
        """Test downloading with invalid revision number"""
        url = reverse('file_download', kwargs={'path': 'documents/download_test.txt'})
        
        # Non-existent revision
        response = self.client.get(url, {
            'token': self.token1.key, 
            'revision': '999'
        })
        self.assertEqual(response.status_code, 404)
        
        # Invalid revision format
        response = self.client.get(url, {
            'token': self.token1.key, 
            'revision': 'invalid'
        })
        self.assertEqual(response.status_code, 404)
    
    def test_download_url_decoding(self):
        """Test that virtual paths are properly URL decoded"""
        # Create file with special characters in path
        special_file = FileVersion.objects.create(
            file_name="special file.txt",
            version_number=1,
            file_path=self.create_test_file("special.txt", b"Special content"),
            uploader=self.user1,
            virtual_path="/documents/special file with spaces.txt",
            checksum="special_checksum"
        )
        special_file.root_file = special_file
        special_file.save()
        
        # URL should be encoded when making request
        encoded_path = "documents/special%20file%20with%20spaces.txt"
        url = reverse('file_download', kwargs={'path': encoded_path})
        response = self.client.get(url, {'token': self.token1.key})
        
        self.assertEqual(response.status_code, 200)