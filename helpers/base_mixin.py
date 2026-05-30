from typing import Any
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "status": False,
            "message": _extract_message(response.data),
            "data": response.data,
        }
    return response


def _extract_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        for value in data.values():
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, str):
                return value
    if isinstance(data, list) and data:
        return str(data[0])
    return "Xatolik yuz berdi"


class BaseViewSetMixin(object):
    action_serializer_class = {}
    action_permission_classes = {}

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 204:
            return super().finalize_response(request, response, *args, **kwargs)

        # custom_exception_handler already wrapped error responses.
        # To'liq wrapper shaklini tekshiramiz, chunki serializer'da ham "status"
        # maydoni bo'lishi mumkin (masalan, Order.status) — faqat "status" ga
        # qarab bo'lmaydi.
        if isinstance(response.data, dict) and {"status", "message", "data"} <= set(response.data.keys()):
            return super().finalize_response(request, response, *args, **kwargs)

        if response.status_code >= 400:
            response.data = {
                "status": False,
                "message": _extract_message(response.data),
                "data": response.data,
            }
        else:
            response.data = {
                "status": True,
                "message": "OK",
                "data": response.data,
            }

        return super().finalize_response(request, response, *args, **kwargs)

    def get_serializer_class(self) -> Any:
        return self.action_serializer_class.get(self.action, self.serializer_class)

    def get_permissions(self) -> Any:
        return [
            permission() for permission in self.action_permission_classes.get(
                self.action, self.permission_classes)
        ]
