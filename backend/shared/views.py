import os

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_media(request, path):
    """
    Serve media files only to authenticated users.

    SECURITY: Media files (student photos, QR codes) must not be publicly
    accessible. This view enforces JWT authentication before serving any
    file from MEDIA_ROOT.
    """
    file_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, path))
    # Prevent directory traversal attacks
    if not file_path.startswith(str(settings.MEDIA_ROOT)):
        raise Http404
    if not os.path.exists(file_path):
        raise Http404
    return FileResponse(open(file_path, "rb"))
