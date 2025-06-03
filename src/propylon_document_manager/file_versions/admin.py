from django.contrib import admin
from .models import FileVersion, User

@admin.register(FileVersion)
class FileVersionAdmin(admin.ModelAdmin):
    list_display = (
        'file_name', 'version_number', 'uploader',
        'created_at', 'previous_version', 'root_file'
    )
    search_fields = ('file_name', 'uploader__email')
    list_filter = ('uploader', 'created_at')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name')
    search_fields = ('email', 'name')
    list_filter = ('is_active', 'is_staff')
    ordering = ('email',)