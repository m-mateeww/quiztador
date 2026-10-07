from rest_framework.views import exception_handler


def _as_list(value):
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def api_exception_handler(exc, context):
    """Wraps every DRF error in one format: {"errors": {field: [messages]}}."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(data, dict):
        errors = {field: _as_list(messages) for field, messages in data.items()}
    else:
        errors = {"non_field_errors": _as_list(data)}

    response.data = {"errors": errors}
    return response
