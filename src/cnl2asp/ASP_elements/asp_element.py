from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from proposition.signaturemanager import SignatureManager


class ASPElement:
    @abstractmethod
    def to_string(self) -> str:
        """Return the ASP element to string"""

    def get_attributes_list(self, name):
        raise Exception("Looking for attribute in a non-ASPAtom element.")
