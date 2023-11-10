from datetime import datetime

from cnl2asp.exception.cnl2asp_exceptions import EntityNotFound, DuplicatedTypedEntity
from cnl2asp.proposition.attribute_component import ValueComponent
from cnl2asp.proposition.entity_component import EntityComponent, EntityType


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
    def get_signature(signature_identifier: str) -> EntityComponent:
        for signature in SignatureManager.signatures:
            if signature.get_entity_identifier() == signature_identifier:
                return signature.copy()
        raise EntityNotFound(f'Entity "{signature_identifier}" not declared before its usage.')

    @staticmethod
    def remove_signature(signature_identifier: str) -> EntityComponent:
        for signature in SignatureManager.signatures:
            if signature.get_entity_identifier() == signature_identifier:
                SignatureManager.signatures.remove(signature)
                return signature

    @staticmethod
    def is_temporal_entity(name: str) -> bool:
        try:
            entity = SignatureManager.get_signature(name)
            if entity.entity_type == EntityType.DATE or entity.entity_type == EntityType.TIME or entity.entity_type == EntityType.STEP:
                return True
        except EntityNotFound:
            pass
        return False

    @staticmethod
    def get_signature_from_type(entity_type: str) -> EntityComponent:
        """
        Return the first entity matching the entity type
        :param entity_type:
        :return:
        """
        for entity in SignatureManager.signatures:
            if entity.entity_type == entity_type:
                return entity.copy()
        raise EntityNotFound(f"Typed entity with type {entity_type} not defined.")

    @staticmethod
    def get_entity_from_value(value: ValueComponent):
        """
        Parse the value and return the first entity that match the same type
        :param value: a date, time or number
        :return:
        """
        entity_type = EntityType.STEP
        try:
            datetime.strptime(str(value), '%I:%M %p')
            entity_type = EntityType.TIME
        except:
            pass
        try:
            datetime.strptime(str(value), '%d/%m/%Y')
            entity_type = EntityType.DATE
        except:
            pass
        for entity in SignatureManager.signatures:
            if entity.entity_type == entity_type:
                return entity
        raise EntityNotFound(f"No entity found with same type of {value}")
