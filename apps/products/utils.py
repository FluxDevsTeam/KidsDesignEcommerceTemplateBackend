from drf_yasg.utils import swagger_auto_schema
from .pagination import PAGINATION_PARAMS


def swagger_helper(tags, model, type):
    configs = {
        "list": {
            "manual_parameters": PAGINATION_PARAMS,
            "operation_id": f"list {model}",
            "operation_description": f"Retrieve a list of {model}",
        },
        "retrieve": {
            "operation_id": f"retrieve {model}",
            "operation_description": f"Retrieves details of a specific {model}",
        },
        "create": {
            "operation_id": f"create {model}",
            "operation_description": f"Create a new {model}",
        },
        "partial_update": {
            "operation_id": f"update {model}",
            "operation_description": f"Update a {model}",
        },
        "destroy": {
            "operation_id": f"delete {model}",
            "operation_description": f"Delete a {model}",
        },
        "default": {
            "operation_id": f"{model}",
            "operation_description": f"{model}",
        }
    }

    config = configs.get(type, configs["default"])
    config["tags"] = [tags]

    def decorator(view_func):
        return swagger_auto_schema(**config)(view_func)

    return decorator
