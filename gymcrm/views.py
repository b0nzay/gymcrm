from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse


def spa_index(request, rest=None):
    index = Path(settings.FRONTEND_DIR) / 'index.html'
    if not index.is_file():
        return HttpResponse(
            'Фронт не собран. В папке gymcrm-web выполните: npm run build',
            status=503,
            content_type='text/plain; charset=utf-8',
        )
    return FileResponse(index.open('rb'), content_type='text/html; charset=utf-8')
