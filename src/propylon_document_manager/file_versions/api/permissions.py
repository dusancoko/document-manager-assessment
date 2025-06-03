from rest_framework import permissions

class HasFileVersionPermission(permissions.BasePermission):
    """
    Custom permission to allow only users with explicit permission to access FileVersion instances.
    """

    def has_object_permission(self, request, view, obj):
        # Owner always has access
        if obj.uploader == request.user:
            return True

        # Check for specific permissions based on action
        if request.method in permissions.SAFE_METHODS:
            # For read operations, check view permission
            return request.user.has_perm("file_versions.view_fileversion")
        else:
            # For write operations, check change permission
            return request.user.has_perm("file_versions.change_fileversion")


class CanEditSharedFile(permissions.BasePermission):
    """
    Permission to check if user can edit a shared file
    """
    
    def has_object_permission(self, request, view, obj):
        # Owner can always edit
        if obj.uploader == request.user:
            return True
            
        # Check if user has change permission for shared files
        return request.user.has_perm("file_versions.change_fileversion")