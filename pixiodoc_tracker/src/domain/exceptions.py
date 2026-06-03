class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    def __init__(self, entity: str, entity_id):
        super().__init__(f'{entity} no encontrado: {entity_id}')


class ValidationError(DomainError):
    pass



