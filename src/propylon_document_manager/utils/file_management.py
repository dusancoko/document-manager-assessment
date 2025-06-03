import os
import uuid
from datetime import datetime
from django.utils.text import slugify

def unique_file_upload_path(instance, filename):
    base, ext = os.path.splitext(filename)
    ext = ext.lower()
    slug = slugify(base)
    date = datetime.now().strftime("%Y%m%d")
    unique = uuid.uuid4().hex[:10]
    return f"{date}_{slug}_{unique}{ext}"
