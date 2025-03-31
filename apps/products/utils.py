from drf_yasg.utils import swagger_auto_schema
from .pagination import PAGINATION_PARAMS

def swagger_helper(tags, model, type):
    if type == "list":
        return @swagger_auto_schema(manual_parameters=PAGINATION_PARAMS, operation_id=f"list {model}", operation_description="fretrieve a list of {model}", tags=[tags])
    if type == "retrieve":
        return @swagger_auto_schema(operation_id=f"retrieve {model}", operation_desciption=f"Retrieves details of a specific {model}", tags=[tags])
    if type == "create":
        return @swagger_auto_schema(operation_id=f"create {model}", operation_desciption=f"Create a new {model}", tags=[tags])
    if type == "partial_update":
        return @swagger_auto_schema(operation_id=f"update {model}", operation_description=f"update a {model}", tags=[tags])
    if type == "destroy":
        return @swagger_auto_schema(operation_id=f"delete {model}", operation_description=f"delete a {model}", tags=[tags])
    return @swagger_auto_schema(operation_id=f"{model}", operation_description=f"{model}", tags=[tags])
