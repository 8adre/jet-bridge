from jet_bridge_base import settings
from jet_bridge_base.configuration import configuration
from jet_bridge_base.responses.json import JSONResponse
from jet_bridge_base.views.base.api import APIView


class ApiView(APIView):

    def get(self, *args, **kwargs):
        media_url_base = settings.MEDIA_BASE_URL + '{}' if settings.MEDIA_BASE_URL \
            else self.build_absolute_uri('/media/{}')
        return JSONResponse({
            'version': configuration.get_version(),
            'type': settings.BRIDGE_TYPE,
            'media_url_template': media_url_base
        })
