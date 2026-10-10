"""
Contact Manager - Résolution des contacts utilisateur
Permet de mapper les noms/alias vers des emails réels
"""
import json
import os
from typing import Optional, Dict, List
from pathlib import Path


class ContactManager:
    """Gestionnaire de contacts pour résolution nom → email."""
    
    def __init__(self, contacts_file: str = "backend/data/contacts.json"):
        self.contacts_file = Path(contacts_file)
        self.contacts: Dict = {}
        self.aliases: Dict = {}
        self.load_contacts()
    
    def load_contacts(self):
        """Charge les contacts depuis le fichier JSON."""
        if not self.contacts_file.exists():
            print(f"⚠️ [Contacts] Fichier non trouvé: {self.contacts_file}")
            print(f"⚠️ [Contacts] Création du fichier par défaut...")
            self._create_default_contacts()
        
        try:
            with open(self.contacts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.contacts = data.get('contacts', {})
                self.aliases = data.get('aliases', {})
            
            print(f"✅ [Contacts] {len(self.contacts)} contacts chargés")
            print(f"✅ [Contacts] {len(self.aliases)} alias chargés")
        
        except Exception as e:
            print(f"❌ [Contacts] Erreur chargement: {e}")
            self.contacts = {}
            self.aliases = {}
    
    def _create_default_contacts(self):
        """Crée un fichier de contacts par défaut."""
        default_data = {
            "contacts": {
                "amine": {
                    "name": "Amine Ben Salem",
                    "email": "amine@ensi.tn",
                    "phone": "+216 20 123 456",
                    "tags": ["collègue", "projet"]
                },
                "jean": {
                    "name": "Jean Martin",
                    "email": "montassar.nawara@ensi-uma.tn",
                    "phone": "+33 6 12 34 56 78",
                    "tags": ["ami", "france"]
                },
                "mon ami": {
                    "name": "Montassar Nawara",
                    "email": "montassar.nawara@ensi-uma.tn",
                    "phone": "+216 XX XXX XXX",
                    "tags": ["moi", "dev"]
                }
            },
            "aliases": {
                "mon manager": "jean",
                "mon pote": "jean",
                "amin": "amine",
                "prof": "professeur"
            }
        }
        
        # Créer le dossier si nécessaire
        self.contacts_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.contacts_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ [Contacts] Fichier créé: {self.contacts_file}")
        self.contacts = default_data['contacts']
        self.aliases = default_data['aliases']
    
    def resolve_contact(self, name: str) -> Optional[Dict]:
        """
        Résout un nom ou alias vers les informations complètes du contact.
        
        Args:
            name: Nom, prénom, alias du contact
        
        Returns:
            Dict avec {name, email, phone, tags} ou None si non trouvé
        """
        if not name:
            return None
        
        # Normaliser le nom (minuscules, trim)
        normalized_name = name.strip().lower()
        
        # 1. Chercher dans les alias
        if normalized_name in self.aliases:
            contact_key = self.aliases[normalized_name]
            print(f"🔍 [Contacts] Alias trouvé: '{name}' → '{contact_key}'")
            normalized_name = contact_key
        
        # 2. Chercher dans les contacts
        if normalized_name in self.contacts:
            contact = self.contacts[normalized_name]
            print(f"✅ [Contacts] Contact trouvé: {contact['name']} ({contact['email']})")
            return contact
        
        # 3. Chercher par nom complet (case-insensitive)
        for key, contact in self.contacts.items():
            if contact['name'].lower() == normalized_name:
                print(f"✅ [Contacts] Contact trouvé par nom: {contact['name']}")
                return contact
        
        print(f"❌ [Contacts] Contact non trouvé: '{name}'")
        return None
    
    def get_email(self, name: str) -> Optional[str]:
        """
        Récupère l'email d'un contact par son nom/alias.
        
        Args:
            name: Nom ou alias du contact
        
        Returns:
            Email du contact ou None si non trouvé
        """
        contact = self.resolve_contact(name)
        return contact['email'] if contact else None
    
    def is_fake_email(self, email: str) -> bool:
        """
        Vérifie si un email est fictif (généré par le LLM).
        
        Args:
            email: Adresse email à vérifier
        
        Returns:
            True si l'email est fictif
        """
        if not email:
            return True
        
        fake_domains = [
            '@example.com',
            '@example.org',
            '@test.com',
            '@fake.com',
            '@domain.com',
            '@email.com'
        ]
        
        email_lower = email.lower()
        
        for domain in fake_domains:
            if domain in email_lower:
                print(f"🚫 [Contacts] Email fictif détecté: {email}")
                return True
        
        return False
    
    def list_contacts(self) -> List[Dict]:
        """Liste tous les contacts disponibles."""
        return [
            {
                'name': contact.get('name', key),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', ''),
                'tags': contact.get('tags', [])
            }
            for key, contact in self.contacts.items()
        ]
    
    def add_contact(self, name: str, email: str,
                   phone: Optional[str] = None, tags: Optional[List[str]] = None):
        """Ajoute un nouveau contact (clé basée sur le nom)."""
        contact_key = name.strip().lower()
        if not contact_key:
            raise ValueError("Contact name is required")

        self.contacts[contact_key] = {
            'name': name,
            'email': email,
            'phone': phone or '',
            'tags': tags or []
        }
        self._save_contacts()
        print(f"✅ [Contacts] Contact ajouté: {name} ({email})")

    def update_contact(self, name_key: str, name: Optional[str] = None,
                       email: Optional[str] = None, phone: Optional[str] = None,
                       tags: Optional[List[str]] = None):
        """Met à jour un contact existant (clé basée sur le nom)."""
        key = name_key.lower()
        if key not in self.contacts:
            raise ValueError("Contact not found")

        contact = self.contacts[key]
        if name is not None:
            contact['name'] = name
        if email is not None:
            contact['email'] = email
        if phone is not None:
            contact['phone'] = phone
        if tags is not None:
            contact['tags'] = tags

        if name is not None:
            new_key = name.strip().lower()
            if new_key and new_key != key:
                self.contacts[new_key] = contact
                self.contacts.pop(key, None)
                # Mettre a jour les alias qui pointent vers l'ancien nom
                for alias, target in list(self.aliases.items()):
                    if target == key:
                        self.aliases[alias] = new_key
                key = new_key

        self._save_contacts()
        print(f"✅ [Contacts] Contact mis à jour: {contact.get('name', key)}")

    def delete_contact(self, name_key: str):
        """Supprime un contact existant (clé basée sur le nom)."""
        key = name_key.lower()
        if key not in self.contacts:
            raise ValueError("Contact not found")

        deleted = self.contacts.pop(key)
        # Supprimer les alias associés
        aliases_to_remove = [alias for alias, target in self.aliases.items() if target == key]
        for alias in aliases_to_remove:
            self.aliases.pop(alias, None)

        self._save_contacts()
        print(f"✅ [Contacts] Contact supprimé: {deleted.get('name', key)}")

    def add_alias(self, alias: str, contact_name: str):
        """Ajoute un alias vers un contact existant (clé basée sur le nom)."""
        key = contact_name.strip().lower()

        # Autoriser nom d'affichage (case-insensitive)
        if key not in self.contacts:
            for contact_key, contact in self.contacts.items():
                if contact.get('name', '').strip().lower() == key:
                    key = contact_key
                    break

        if key not in self.contacts:
            raise ValueError("Contact not found")

        self.aliases[alias.strip().lower()] = key
        self._save_contacts()
        print(f"✅ [Contacts] Alias ajouté: {alias} -> {key}")

    def delete_alias(self, alias: str):
        """Supprime un alias existant."""
        key = alias.strip().lower()
        if key not in self.aliases:
            raise ValueError("Alias not found")

        self.aliases.pop(key)
        self._save_contacts()
        print(f"✅ [Contacts] Alias supprimé: {alias}")
    
    def _save_contacts(self):
        """Sauvegarde les contacts dans le fichier JSON."""
        data = {
            'contacts': self.contacts,
            'aliases': self.aliases
        }
        
        with open(self.contacts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Instance globale
contact_manager = ContactManager()
