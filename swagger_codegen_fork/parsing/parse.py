from typing import Generator, Type

from schemathesis.schemas import BaseSchema

from swagger_codegen_fork.parsing.endpoint import EndpointDescription


def endpoints_from_base_schema(
    schema: BaseSchema, endpoint_class: Type[EndpointDescription]
) -> Generator[EndpointDescription, None, None]:
    for v in schema.endpoints.values():
        for endpoint in v.values():
            yield endpoint_class(endpoint=endpoint)
