import os
import mimetypes
from io import BytesIO
import requests
from django.core.files.storage import Storage
from django.core.files.base import File
from django.conf import settings
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseMediaStorage(Storage):
    """
    Custom Django Storage backend that handles media files directly
    via the Supabase Storage REST API.
    """

    def __init__(self, **kwargs):
        self.supabase_url = (
            kwargs.get('supabase_url')
            or getattr(settings, 'SUPABASE_URL', os.getenv('SUPABASE_URL', ''))
        ).rstrip('/')
        self.service_role_key = (
            kwargs.get('service_role_key')
            or getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''))
        )
        self.bucket_name = (
            kwargs.get('bucket_name')
            or getattr(settings, 'SUPABASE_STORAGE_BUCKET', os.getenv('SUPABASE_STORAGE_BUCKET', 'media'))
        )
        self.endpoint = f"{self.supabase_url}/storage/v1/object"
        self.public_endpoint = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}"

    def _get_headers(self, content_type=None):
        headers = {
            'apikey': self.service_role_key,
            'Authorization': f'Bearer {self.service_role_key}',
        }
        if content_type:
            headers['Content-Type'] = content_type
        return headers

    def _clean_name(self, name):
        return str(name).replace('\\', '/').lstrip('/')

    def _open(self, name, mode='rb'):
        clean_name = self._clean_name(name)
        url = self.url(clean_name)
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            file_obj = BytesIO(response.content)
            file_obj.name = clean_name
            file_obj.mode = mode
            return File(file_obj)
        raise FileNotFoundError(f"File '{name}' could not be fetched from Supabase Storage (Status: {response.status_code})")

    def _save(self, name, content):
        clean_name = self._clean_name(name)
        content_type, _ = mimetypes.guess_type(clean_name)
        if not content_type:
            content_type = 'application/octet-stream'

        headers = self._get_headers(content_type=content_type)
        headers['x-upsert'] = 'true'

        url = f"{self.endpoint}/{self.bucket_name}/{clean_name}"

        # Read file content safely
        if hasattr(content, 'chunks'):
            data = b''.join(chunk for chunk in content.chunks())
        elif hasattr(content, 'read'):
            content.seek(0)
            data = content.read()
        else:
            data = content

        response = requests.post(url, headers=headers, data=data, timeout=30)
        if response.status_code in (200, 201):
            return clean_name
        raise IOError(f"Failed to upload '{name}' to Supabase Storage: {response.status_code} - {response.text}")

    def delete(self, name):
        clean_name = self._clean_name(name)
        url = f"{self.endpoint}/{self.bucket_name}/{clean_name}"
        headers = self._get_headers()
        try:
            requests.delete(url, headers=headers, timeout=15)
        except Exception:
            pass

    def exists(self, name):
        clean_name = self._clean_name(name)
        url = f"{self.endpoint}/info/public/{self.bucket_name}/{clean_name}"
        headers = self._get_headers()
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def url(self, name):
        clean_name = self._clean_name(name)
        return f"{self.public_endpoint}/{clean_name}"

    def size(self, name):
        clean_name = self._clean_name(name)
        url = f"{self.endpoint}/info/public/{self.bucket_name}/{clean_name}"
        headers = self._get_headers()
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('size', 0)
        except Exception:
            pass
        return 0
