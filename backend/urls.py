from pathlib import Path
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import FileResponse, Http404
from django.conf import settings


def spa_view(request, path=''):
    """Serve Vue SPA index.html for all non-API, non-static routes."""
    index_html = Path(settings.BASE_DIR) / 'frontend' / 'dist' / 'index.html'
    if not index_html.exists():
        raise Http404(
            "Frontend not built. Run: bash scripts/build.sh"
        )
    return FileResponse(open(index_html, 'rb'), content_type='text/html; charset=utf-8')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    # SPA catch-all — must be last
    path('', spa_view),
    re_path(r'^(?!api/|admin/|static/).*$', spa_view),
]
