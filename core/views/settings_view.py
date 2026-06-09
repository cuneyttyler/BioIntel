from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import AppSettings


def _mask(key: str) -> str:
    if not key:
        return ''
    if len(key) <= 12:
        return '••••'
    return key[:6] + '•' * (len(key) - 10) + key[-4:]


class AppSettingsView(APIView):
    def get(self, request):
        s = AppSettings.get_instance()
        return Response({
            'provider': s.provider,
            'model': s.model,
            'anthropic_api_key': _mask(s.anthropic_api_key),
            'openai_api_key': _mask(s.openai_api_key),
            'mistral_api_key': _mask(s.mistral_api_key),
            'custom_endpoint': s.custom_endpoint,
            'custom_api_key': _mask(s.custom_api_key),
        })

    def put(self, request):
        s = AppSettings.get_instance()
        data = request.data

        if 'provider' in data:
            s.provider = data['provider']
        if 'model' in data:
            s.model = data['model']
        if 'custom_endpoint' in data:
            s.custom_endpoint = data['custom_endpoint']

        # Only overwrite key fields when a real (non-masked) value is submitted
        for field in ('anthropic_api_key', 'openai_api_key', 'mistral_api_key', 'custom_api_key'):
            val = data.get(field, '')
            if val and '•' not in val:
                setattr(s, field, val)

        s.save()
        return Response({'status': 'ok'})
