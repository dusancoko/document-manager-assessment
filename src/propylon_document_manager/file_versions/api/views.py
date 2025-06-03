from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from urllib.parse import unquote
from pathlib import Path
from django.db.models import Q

# Guardian imports for object-level permissions
from guardian.shortcuts import assign_perm, get_objects_for_user, remove_perm

from ..models import FileVersion
from .serializers import FileVersionSerializer, FileUploadSerializer, SharedFileVersionSerializer
from .permissions import HasFileVersionPermission
from propylon_document_manager.utils.file_extraction import extract_text


class FileVersionViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = FileVersionSerializer
    permission_classes = [IsAuthenticated, HasFileVersionPermission]
    queryset = FileVersion.objects.all()
    lookup_field = "id"

    def get_queryset(self):
        return FileVersion.objects.filter(uploader=self.request.user, previous_version__isnull=True)

    @action(detail=False, methods=['get'], url_path='shared-with-me')
    def shared_with_me(self, request):
        """
        Returns files that have been shared with the current user via object-level permissions
        """
        user = request.user
        
        # Use django-guardian to get files with view permission
        shared_files = get_objects_for_user(
            user, 
            'file_versions.view_fileversion',
            klass=FileVersion.objects.filter(previous_version__isnull=True),
            accept_global_perms=False  # Only object-level permissions
        ).exclude(uploader=user)  # Exclude files uploaded by the user
        
        # Use the shared file serializer to include permission info
        serializer = SharedFileVersionSerializer(shared_files, many=True, context={'request': request})
        return Response(serializer.data)


class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                "message": "File uploaded",
                "version": result.version_number,
                "checksum": result.checksum,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class FileDownloadByNameView(APIView):
    """
    Allows users to download a file version via virtual_path and optional revision
    """
    permission_classes = []
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        raw_virtual_path = kwargs.get("path")
        if not raw_virtual_path:
            raise Http404("No virtual path provided")

        token_key = request.query_params.get("token")
        if not token_key:
            return HttpResponseForbidden("Authentication token was not provided.")

        try:
            token = Token.objects.select_related("user").get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return HttpResponseForbidden("Invalid authentication token.")

        # Virtual path
        virtual_path = unquote(raw_virtual_path)
        revision = request.query_params.get("revision")

        file_versions = FileVersion.objects.filter(virtual_path=virtual_path)

        if not file_versions.exists():
            raise Http404("No such file found")

        if revision is not None:
            try:
                version_number = int(revision)
                file_version = file_versions.get(version_number=version_number)
            except (ValueError, FileVersion.DoesNotExist):
                raise Http404("Specified revision not found")
        else:
            file_version = file_versions.order_by("-version_number").first()
            if not file_version:
                raise Http404("No versions available")

        # Check permissions: either user owns the file or has view permission
        root_file = file_version.root_file or file_version
        if file_version.uploader != user and not user.has_perm("file_versions.view_fileversion", root_file):
            return HttpResponseForbidden("You don't have permission to access this file.")

        file_path = file_version.file_path.path
        if not Path(file_path).exists():
            raise Http404("File not found on disk")

        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=file_version.file_name)


class FileCompareView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        left_id = request.GET.get("left_id")
        right_id = request.GET.get("right_id")
        if not left_id or not right_id:
            return Response({"detail": "Both left_id and right_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        left = get_object_or_404(FileVersion, pk=left_id)
        right = get_object_or_404(FileVersion, pk=right_id)

        user = request.user
        
        # Check permissions for both files (check root files)
        left_root = left.root_file or left
        right_root = right.root_file or right
        
        if (left.uploader != user and not user.has_perm("file_versions.view_fileversion", left_root)):
            return Response({"detail": "You don't have permission to access the left file."}, status=status.HTTP_403_FORBIDDEN)
            
        if (right.uploader != user and not user.has_perm("file_versions.view_fileversion", right_root)):
            return Response({"detail": "You don't have permission to access the right file."}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "left_file": {
                "id": left.id,
                "name": left.file_name,
                "text": extract_text(left)
            },
            "right_file": {
                "id": right.id,
                "name": right.file_name,
                "text": extract_text(right)
            }
        }, status=200)


class FileShareView(APIView):
    """
    API endpoint to share files with other users using django-guardian object-level permissions
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_id = request.data.get("file_id")
        user_email = request.data.get("user_email")
        can_edit = request.data.get("can_edit", False)

        if not file_id or not user_email:
            return Response({"detail": "file_id and user_email are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_version = FileVersion.objects.get(id=file_id)
        except FileVersion.DoesNotExist:
            return Response({"detail": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        # Only the file owner can share the file
        if file_version.uploader != request.user:
            return Response({"detail": "You can only share files you own"}, status=status.HTTP_403_FORBIDDEN)

        try:
            from ..models import User
            target_user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response({"detail": "User with this email not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get the root file (the one to share permissions with)
        root_file = file_version.root_file or file_version

        # Grant object-level permissions using django-guardian
        assign_perm('view_fileversion', target_user, root_file)
        permissions_granted = ["view"]
        
        if can_edit:
            assign_perm('change_fileversion', target_user, root_file)
            permissions_granted.append("edit")
        else:
            # Remove edit permission if not requested
            remove_perm('change_fileversion', target_user, root_file)

        return Response({
            "message": f"File shared with {user_email}",
            "permissions": permissions_granted
        }, status=status.HTTP_200_OK)


class CustomObtainAuthToken(ObtainAuthToken):
    """
    Custom authentication view to handle user login and token generation.
    Implemented because user model uses email instead of username.
    """

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request=request, email=email, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user_id": user.id,
            "email": user.email,
            "last_login": user.last_login,
        })