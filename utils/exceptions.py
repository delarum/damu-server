from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "error":   True,
            "message": _extract_message(response.data),
            "details": response.data,
        }

    return response


def _extract_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        first_val = next(iter(data.values()), None)
        if isinstance(first_val, list):
            return str(first_val[0])
    if isinstance(data, list) and data:
        return str(data[0])
    return "An error occurred"
