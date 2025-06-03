import hashlib
from rest_framework import serializers
from ..models import FileVersion
from django.contrib.auth.models import Permission


class FileVersionSerializer(serializers.ModelSerializer):
    versions = serializers.SerializerMethodField()

    class Meta:
        model = FileVersion
        fields = [
            'id', 'file_name', 'version_number', 'virtual_path', 'mime_type',
            'file_size', 'checksum', 'created_at', 'versions'
        ]

    def get_versions(self, obj):
        all_versions = FileVersion.objects.filter(root_file=obj.root_file or obj).order_by('-version_number')
        return [
            {
                'id': fv.id,
                'version_number': fv.version_number,
                'virtual_path': fv.virtual_path,
            }
            for fv in all_versions
        ]


class SharedFileVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for files shared with the current user, including permission info
    """
    versions = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    owner_email = serializers.CharField(source='uploader.email', read_only=True)

    class Meta:
        model = FileVersion
        fields = [
            'id', 'file_name', 'version_number', 'virtual_path', 'mime_type',
            'file_size', 'checksum', 'created_at', 'versions', 'permissions', 'owner_email'
        ]

    def get_versions(self, obj):
        user = self.context['request'].user
        all_versions = FileVersion.objects.filter(root_file=obj.root_file or obj).order_by('-version_number')
        
        # Filter versions based on user permissions
        accessible_versions = []
        for fv in all_versions:
            if user.has_perm("file_versions.view_fileversion", fv):
                accessible_versions.append({
                    'id': fv.id,
                    'version_number': fv.version_number,
                    'virtual_path': fv.virtual_path,
                })
        
        return accessible_versions

    def get_permissions(self, obj):
        user = self.context['request'].user
        permissions = []
        
        if user.has_perm("file_versions.view_fileversion", obj):
            permissions.append("view")
        
        if user.has_perm("file_versions.change_fileversion", obj):
            permissions.append("edit")
            
        return permissions


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    name = serializers.CharField()
    virtual_path = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        file_obj = data["file"]
        hasher = hashlib.sha256()
        for chunk in file_obj.chunks():
            hasher.update(chunk)
        data["checksum"] = hasher.hexdigest()
        return data

    def validate_virtual_path(self, value):
        """
        Check if user has permission to upload to this virtual path
        """
        user = self.context["request"].user
        
        # Check if file exists at this virtual path
        existing_file = (
            FileVersion.objects
            .filter(virtual_path=value, previous_version__isnull=True)
            .first()
        )
        
        if existing_file:
            # If file exists and user is not the owner, check change permission
            if existing_file.uploader != user:
                if not user.has_perm("file_versions.change_fileversion", existing_file):
                    raise serializers.ValidationError(
                        "You don't have permission to upload new versions to this file path."
                    )
        
        return value

    def assign_fileversion_permissions(self, user):
        """Ensure the user has all required FileVersion permissions."""
        for codename in ["add_fileversion", "change_fileversion", "delete_fileversion", "view_fileversion"]:
            perm = Permission.objects.get(codename=codename)
            if not user.user_permissions.filter(pk=perm.pk).exists():
                user.user_permissions.add(perm)

    def create(self, validated_data):
        user = self.context["request"].user
        file_obj = validated_data["file"]
        file_name = validated_data["name"]
        virtual_path = validated_data["virtual_path"]
        notes = validated_data.get("notes", "")
        checksum = validated_data["checksum"]

        # Find root file by virtual_path (across all users for shared files)
        root_file = (
            FileVersion.objects
            .filter(virtual_path=virtual_path, previous_version__isnull=True)
            .first()
        )

        if root_file:
            # Check if user owns the file or has change permission
            if root_file.uploader != user and not user.has_perm("file_versions.change_fileversion", root_file):
                raise serializers.ValidationError({"detail": "You don't have permission to upload to this file."})
                
            if FileVersion.objects.filter(root_file=root_file, checksum=checksum).exists():
                raise serializers.ValidationError({"detail": "Identical file already uploaded"})

            previous_version = FileVersion.objects.filter(root_file=root_file).order_by("-version_number").first()
            next_version = previous_version.version_number + 1
            # Keep the original uploader for the root file reference
            uploader = root_file.uploader
        else:
            previous_version = None
            next_version = 1
            uploader = user

        file_version = FileVersion.objects.create(
            file_name=file_name,
            version_number=next_version,
            file_path=file_obj,
            uploader=uploader,  # Use original uploader for consistency
            virtual_path=virtual_path,
            mime_type=getattr(file_obj, "content_type", "application/octet-stream"),
            file_size=getattr(file_obj, "size", -1),
            checksum=checksum,
            notes=notes,
            previous_version=previous_version,
            root_file=root_file or None,
        )

        if file_version.root_file is None:
            file_version.root_file = file_version
            file_version.save(update_fields=["root_file"])

        self.assign_fileversion_permissions(user)
        return file_version