from datetime import datetime
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

import json


class SlackSlashCommandView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        if settings.DEBUG:
            print("*** INCOMING SLASH COMMAND START ***")
            print(json.dumps(request.data, indent=4))
            print("*** INCOMING SLASH COMMAND END ***")

        return Response({
                "text": datetime.utcnow().strftime(
                    "%B %m, %Y %H:%M %p")
            },
            status=status.HTTP_200_OK
        )
