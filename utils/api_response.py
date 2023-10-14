from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import exception_handler
from rest_framework.serializers import ValidationError
from rest_framework.renderers import JSONRenderer

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if response.status_code >= 400:
            return APIFailure(
                status = response.status_code,
                message = exc.detail
            )
    return response


class APISuccess():
    def __new__(cls,  message = 'Success', data={}, status=HTTP_200_OK):
        return Response(
            {
                'status': True,
                'message': message,
                'data': data
            },
            status
        )

class APIFailure():
    def __new__(cls, message = 'Error', status=HTTP_400_BAD_REQUEST):
        return Response(
            {
                'status': False,
                'message': message
            },
            status
        )


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        data = {
            'status': renderer_context['response'].status_code < 400,
            'message': data.pop('message'),
            'data': data
        }
        return super(CustomJSONRenderer, self).render(data, accepted_media_type, renderer_context)