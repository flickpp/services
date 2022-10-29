from .doolally import (
    validate as validate_json,
    ValidationError,
)

class JSONValidator:
    def __init__(self, schema):
        self._schema = schema

    def __call__(self, err, data):
        try:
            validate_json(data, self._schema)
        except ValidationError as exc:
            raise err(str(exc))
