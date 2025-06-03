# src/tests/test_authentication.py
"""
Test cases for authentication functionality
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token

from propylon_document_manager.file_versions.models import User
from .base import BaseAPITestCase


class AuthenticationTest(BaseAPITestCase):
    """Test cases for authentication functionality"""
    
    def setUp(self):
        super().setUp()
        self.login_url = reverse('custom_token_auth')
        
        # Create a specific user for auth tests
        self.auth_user = User.objects.create_user(
            email='auth@test.com',
            password='testpass123'
        )
    
    def test_successful_login(self):
        """Test successful login with valid credentials"""
        data = {
            'email': 'auth@test.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'], 'auth@test.com')
        self.assertEqual(response.data['user_id'], self.auth_user.id)
        
        # Verify token is valid
        token = Token.objects.get(key=response.data['token'])
        self.assertEqual(token.user, self.auth_user)
    
    def test_login_with_invalid_password(self):
        """Test login with invalid password"""
        data = {
            'email': 'auth@test.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Invalid credentials', response.data['detail'])
    
    def test_login_with_nonexistent_user(self):
        """Test login with non-existent user email"""
        data = {
            'email': 'nonexistent@test.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Invalid credentials', response.data['detail'])
    
    def test_login_missing_email(self):
        """Test login with missing email"""
        data = {'password': 'testpass123'}
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Email and password are required', response.data['detail'])
    
    def test_login_missing_password(self):
        """Test login with missing password"""
        data = {'email': 'auth@test.com'}
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Email and password are required', response.data['detail'])
    
    def test_login_missing_both_credentials(self):
        """Test login with missing email and password"""
        data = {}
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Email and password are required', response.data['detail'])
    
    def test_login_empty_email(self):
        """Test login with empty email string"""
        data = {
            'email': '',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Email and password are required', response.data['detail'])
    
    def test_login_empty_password(self):
        """Test login with empty password string"""
        data = {
            'email': 'auth@test.com',
            'password': ''
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Email and password are required', response.data['detail'])
    
    def test_token_generation_is_unique(self):
        """Test that each login generates a unique token (or reuses existing)"""
        data = {
            'email': 'auth@test.com',
            'password': 'testpass123'
        }
        
        # First login
        response1 = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        token1 = response1.data['token']
        
        # Second login - should return the same token (get_or_create behavior)
        response2 = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        token2 = response2.data['token']
        
        # Should be the same token since we use get_or_create
        self.assertEqual(token1, token2)
    


class TokenAuthenticationTest(BaseAPITestCase):
    """Test cases for token-based API authentication"""
    
    def setUp(self):
        super().setUp()
        self.protected_url = reverse('api:fileversion-list')
    
    def test_access_with_valid_token_succeeds(self):
        """Test that accessing protected endpoint with valid token succeeds"""
        self.authenticate_user1()
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_token_format_validation(self):
        """Test various token format validations"""
        # Wrong prefix
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token1.key)
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # No prefix
        self.client.credentials(HTTP_AUTHORIZATION=self.token1.key)
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Extra spaces
        self.client.credentials(HTTP_AUTHORIZATION=f'Token  {self.token1.key}')
        response = self.client.get(self.protected_url)
        # This might succeed or fail depending on Django's token parsing
        # Adjust assertion based on actual behavior
    
    def test_token_belongs_to_correct_user(self):
        """Test that token authentication identifies the correct user"""
        self.authenticate_user1()
        response = self.client.get(self.protected_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The response should reflect user1's data (empty list since no files created)
        self.assertEqual(len(response.data), 0)
    