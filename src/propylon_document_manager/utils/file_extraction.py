import mimetypes
import mammoth
import zipfile
import pypdf


SUPPORTED_MIME_TYPES = {
    'text/plain',
    'text/markdown',
    'text/html',
    'application/xml',
    'text/xml',
    'application/json',
    'text/csv',
    'application/javascript',
    'text/javascript',
    'text/x-python',
    'text/x-ini',
    'text/x-config',
    'text/x-rst',
    'application/x-tex',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
    'application/vnd.oasis.opendocument.text',  # ODT
    'application/pdf'
}

def extract_text(fv):
    mime = fv.mime_type or mimetypes.guess_type(fv.file_path.name)[0]
    if mime not in SUPPORTED_MIME_TYPES:
        return f"Unsupported MIME type: {mime}"

    file_path = fv.file_path.path

    if mime == "application/pdf":
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            return "\n".join([page.extract_text() or "" for page in reader.pages])


    elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        with open(file_path, "rb") as f:
            result = mammoth.convert_to_markdown(f)
            return result.value

    elif mime == "application/vnd.oasis.opendocument.text":
        with zipfile.ZipFile(file_path, "r") as z:
            with z.open("content.xml") as f:
                return f.read().decode("utf-8")

    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
