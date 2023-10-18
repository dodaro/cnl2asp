from cnl2asp.exception.cnl2asp_exceptions import EntityNotDefined
from cnl2asp.proposition.entity_component import EntityComponent


class SignatureManager:
    signatures: list[EntityComponent] = []

    def __init__(self):
        pass

    @staticmethod
    def add_signature(entity: EntityComponent):
        # Update previous declared signatures
        for signature in SignatureManager.signatures:
            try:
                attributes = signature.get_attributes_by_name(entity.name)
                for attribute in attributes:
                    signature.attributes.remove(attribute)
                signature.attributes += entity.get_keys()
                signature.attributes.sort(key=lambda x: x.name)
            except:
                pass
        SignatureManager.signatures.append(entity)

    @staticmethod
    def get_signature(name: str) -> EntityComponent:
        for signature in SignatureManager.signatures:
            if signature.name == name:
                return signature.copy()
        raise EntityNotDefined(f'Entity {name} not declared before its usage.')
