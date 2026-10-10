"""
Serializers - Sérialisation Python ↔ JSON
Responsable: Équipe (utilisé par tous)

Rôle:
- Convertir objets Python en JSON
- Convertir JSON en objets Python
- Gérer dates, enums, etc.
"""

import json
from datetime import datetime, date, timezone
from enum import Enum
from typing import Any, Optional
from decimal import Decimal


class JSONSerializer:
    """
    Sérialiseur JSON avec support types Python.
    """
    
    @staticmethod
    def _default_handler(obj: Any) -> Any:
        """
        Gestionnaire par défaut pour types non-standards.
        
        Args:
            obj: Objet à convertir
            
        Returns:
            Objet sérialisable
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    @staticmethod
    def serialize(obj: Any, indent: Optional[int] = None) -> str:
        """
        Sérialiser objet Python en JSON.
        
        Args:
            obj: Objet à sérialiser
            indent: Indentation (None = compact, 2/4 = formaté)
            
        Returns:
            String JSON
        """
        return json.dumps(
            obj,
            default=JSONSerializer._default_handler,
            indent=indent,
            ensure_ascii=False
        )
    
    @staticmethod
    def deserialize(json_str: str) -> Any:
        """
        Désérialiser JSON en objet Python.
        
        Args:
            json_str: String JSON
            
        Returns:
            Objet Python
        """
        return json.loads(json_str)
    
    @staticmethod
    def to_dict(obj: Any) -> Any:
        """
        Convertir objet Python en dictionnaire.
        
        Args:
            obj: Objet à convertir
            
        Returns:
            Dictionnaire (ou list/str selon le type d'entrée)
        """
        if isinstance(obj, dict):
            return obj
        elif hasattr(obj, '__dict__'):
            return {
                key: JSONSerializer.to_dict(value)
                for key, value in obj.__dict__.items()
                if not key.startswith('_')
            }
        elif isinstance(obj, (list, tuple)):
            return [JSONSerializer.to_dict(item) for item in obj]
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        else:
            return obj
    
    @staticmethod
    def from_dict(data: dict, target_class: Optional[type] = None) -> Any:
        """
        Créer objet depuis dictionnaire.
        
        Args:
            data: Dictionnaire source
            target_class: Classe cible (optionnel)
            
        Returns:
            Instance de la classe ou dict
        """
        if target_class is None:
            return data
        
        try:
            return target_class(**data)
        except TypeError:
            # Fallback si la classe n'accepte pas **kwargs
            instance = target_class()
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            return instance
