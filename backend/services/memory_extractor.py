"""
Memory Extractor - Extraction automatique d'entités et métadonnées
Date: 13 Février 2026
Responsable: Montassar

Rôle:
- Extraire entités (nourriture, appareils, personnes, lieux) des conversations
- Détecter émotions utilisateur (happy, frustrated, neutral)
- Identifier intentions (order_food, control_device, ask_info)
- Fournir métadonnées pour l'interface React (affichage images, contexte)

Architecture:
- Utilise LLM (via LLMClient) pour analyse intelligente
- Format JSON structuré pour parsing facile
- Cache optionnel pour réduire appels API
- Intégration avec MemoryService pour persistance

Exemple extraction:
User: "J'ai envie de pizza ce soir"
→ {
    "entities": [{"type": "food", "name": "pizza", "confidence": 0.95}],
    "emotion": "neutral",
    "intent": "order_food"
}
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, UTC


class MemoryExtractor:
    """
    Extracteur d'entités et métadonnées depuis conversations.
    Utilise LLM pour analyse contextuelle intelligente.
    """
    
    def __init__(self, llm_client, memory_service=None, enable_cache: bool = True):
        """
        Initialiser le Memory Extractor.
        
        Args:
            llm_client: Client LLM pour extraction (LLMClient instance)
            memory_service: Service mémoire pour persistance (optionnel)
            enable_cache: Activer le cache pour réduire appels API
        """
        self.llm_client = llm_client
        self.memory_service = memory_service
        self.enable_cache = enable_cache
        
        # Cache des extractions récentes (user_id → dernière extraction)
        self._extraction_cache: Dict[str, Dict] = {}
        
        # Prompt système pour extraction structurée
        self.extraction_prompt = """Tu es un assistant spécialisé dans l'extraction d'informations depuis conversations.

Analyse le message utilisateur et extrais:
1. **Entités** - objets, nourriture, appareils, personnes, lieux mentionnés
2. **Émotion** - état émotionnel de l'utilisateur (happy/satisfied/neutral/frustrated/angry)
3. **Intention** - but principal du message

Réponds UNIQUEMENT en JSON valide, sans texte additionnel.

Format JSON attendu:
{
  "entities": [
    {"type": "food|device|person|location|object", "name": "nom", "confidence": 0.0-1.0}
  ],
  "emotion": "happy|satisfied|neutral|frustrated|angry",
  "intent": "order_food|control_device|ask_info|general_chat|complaint|request_help",
  "summary": "résumé en 1-2 mots des entités trouvées"
}

Types d'entités:
- food: nourriture, boissons, plats (pizza, café, burger)
- device: appareils, équipements (lampe, télé, climatisation)
- person: personnes mentionnées (noms, rôles)
- location: lieux (salon, cuisine, bureau, ville)
- object: autres objets matériels

Règles importantes:
- Si aucune entité détectée → tableau vide []
- Confiance entre 0.0 (incertain) et 1.0 (certain)
- Emotion "neutral" par défaut si ambiguë
- Intent "general_chat" par défaut si unclear

Exemples:

Message: "J'ai envie de pizza ce soir"
→ {"entities": [{"type": "food", "name": "pizza", "confidence": 0.95}], "emotion": "neutral", "intent": "order_food", "summary": "pizza"}

Message: "Allume la lampe du salon"
→ {"entities": [{"type": "device", "name": "lampe", "confidence": 1.0}, {"type": "location", "name": "salon", "confidence": 1.0}], "emotion": "neutral", "intent": "control_device", "summary": "lampe salon"}

Message: "Merci beaucoup, c'est parfait!"
→ {"entities": [], "emotion": "happy", "intent": "general_chat", "summary": ""}

Message: "Ça ne marche pas du tout, je suis énervé"
→ {"entities": [], "emotion": "angry", "intent": "complaint", "summary": ""}

Message: "Est-ce qu'il y a un café près d'ici?"
→ {"entities": [{"type": "food", "name": "café", "confidence": 0.8}, {"type": "location", "name": "près d'ici", "confidence": 0.6}], "emotion": "neutral", "intent": "ask_info", "summary": "café"}

Message: "Peux-tu m'aider avec la télé?"
→ {"entities": [{"type": "device", "name": "télé", "confidence": 1.0}], "emotion": "neutral", "intent": "request_help", "summary": "télé"}

Maintenant analyse ce message:"""

        print("[MemoryExtractor] Initialized successfully")
    
    async def extract_from_conversation(
        self,
        user_message: str,
        user_id: str,
        assistant_response: Optional[str] = None,
        store_results: bool = True
    ) -> Dict:
        """
        Extraire métadonnées depuis un échange conversation.
        
        Args:
            user_message: Message de l'utilisateur
            user_id: ID utilisateur (pour cache et stockage)
            assistant_response: Réponse de l'assistant (optionnel, pour contexte)
            store_results: Stocker dans MemoryService si True
            
        Returns:
            {
                "entities": [{"type": str, "name": str, "confidence": float}],
                "emotion": str,
                "intent": str,
                "summary": str,
                "extracted_at": str (ISO timestamp)
            }
        """
        # Vérifier cache si activé
        cache_key = f"{user_id}:{user_message[:50]}"
        if self.enable_cache and cache_key in self._extraction_cache:
            cached = self._extraction_cache[cache_key]
            print(f"[MemoryExtractor] Using cached extraction for user {user_id}")
            return cached
        
        try:
            # Construire le contexte pour l'analyse
            if assistant_response:
                analysis_context = f"User: {user_message}\nAssistant: {assistant_response}"
            else:
                analysis_context = f"User: {user_message}"
            
            # Appel LLM pour extraction
            print(f"[MemoryExtractor] Extracting from: '{user_message[:60]}...'")
            
            llm_response = await self.llm_client.generate(
                prompt=f"{self.extraction_prompt}\n\n{analysis_context}",
                temperature=0.1,  # Très bas pour extraction cohérente
                max_tokens=300
            )
            
            # Parser la réponse JSON
            extracted_data = self._parse_llm_response(llm_response)
            
            # Ajouter timestamp
            extracted_data["extracted_at"] = datetime.now(UTC).isoformat()
            
            # Mettre en cache
            if self.enable_cache:
                self._extraction_cache[cache_key] = extracted_data
            
            # Stocker dans MemoryService si demandé
            if store_results and self.memory_service:
                await self._store_extraction(user_id, user_message, extracted_data)
            
            print(f"[MemoryExtractor] Extracted: {len(extracted_data.get('entities', []))} entities, "
                  f"emotion={extracted_data.get('emotion')}, intent={extracted_data.get('intent')}")
            
            return extracted_data
            
        except Exception as e:
            print(f"[MemoryExtractor] Error during extraction: {e}")
            # Retourner extraction vide en cas d'erreur
            return {
                "entities": [],
                "emotion": "neutral",
                "intent": "general_chat",
                "summary": "",
                "extracted_at": datetime.now(UTC).isoformat(),
                "error": str(e)
            }
    
    def _parse_llm_response(self, llm_response: str) -> Dict:
        """
        Parser la réponse JSON du LLM.
        
        Args:
            llm_response: Réponse brute du LLM
            
        Returns:
            Dictionnaire avec entities, emotion, intent, summary
        """
        try:
            # Nettoyer la réponse (retirer markdown, espaces)
            cleaned = llm_response.strip()
            
            # Retirer les balises markdown si présentes
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # Parser JSON
            parsed = json.loads(cleaned)
            
            # Validation basique des champs obligatoires
            if "entities" not in parsed:
                parsed["entities"] = []
            if "emotion" not in parsed:
                parsed["emotion"] = "neutral"
            if "intent" not in parsed:
                parsed["intent"] = "general_chat"
            if "summary" not in parsed:
                parsed["summary"] = ""
            
            # Valider le format des entités
            valid_entities = []
            for entity in parsed.get("entities", []):
                if isinstance(entity, dict) and "type" in entity and "name" in entity:
                    # Ajouter confidence si manquant
                    if "confidence" not in entity:
                        entity["confidence"] = 0.8
                    valid_entities.append(entity)
            
            parsed["entities"] = valid_entities
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"[MemoryExtractor] JSON parse error: {e}")
            print(f"[MemoryExtractor] Raw response: {llm_response[:200]}")
            
            # Extraction par défaut
            return {
                "entities": [],
                "emotion": "neutral",
                "intent": "general_chat",
                "summary": ""
            }
        except Exception as e:
            print(f"[MemoryExtractor] Unexpected error parsing response: {e}")
            return {
                "entities": [],
                "emotion": "neutral",
                "intent": "general_chat",
                "summary": ""
            }
    
    async def _store_extraction(self, user_id: str, message: str, extracted_data: Dict):
        """
        Stocker extraction dans MemoryService pour persistance.
        
        Args:
            user_id: ID utilisateur
            message: Message original
            extracted_data: Données extraites
        """
        try:
            # Stocker les entités comme faits utilisateur
            for entity in extracted_data.get("entities", []):
                fact_key = f"{entity['type']}_{entity['name']}"
                fact_value = json.dumps({
                    "name": entity["name"],
                    "confidence": entity.get("confidence", 0.8),
                    "first_mentioned": extracted_data["extracted_at"]
                })
                
                self.memory_service.add_fact(
                    user_id=user_id,
                    fact_type=entity["type"],
                    fact_key=fact_key,
                    fact_value=fact_value,
                    confidence=entity.get("confidence", 0.8)
                )
            
            # Stocker l'émotion et intention comme metadata
            if extracted_data.get("emotion") != "neutral":
                self.memory_service.add_fact(
                    user_id=user_id,
                    fact_type="emotion_history",
                    fact_key=f"emotion_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
                    fact_value=json.dumps({
                        "emotion": extracted_data["emotion"],
                        "message": message[:100],
                        "timestamp": extracted_data["extracted_at"]
                    }),
                    confidence=1.0
                )
            
            print(f"[MemoryExtractor] Stored {len(extracted_data.get('entities', []))} entities for user {user_id}")
            
        except Exception as e:
            print(f"[MemoryExtractor] Error storing extraction: {e}")
    
    def get_user_entities(self, user_id: str, entity_type: Optional[str] = None) -> List[Dict]:
        """
        Récupérer les entités stockées pour un utilisateur.
        
        Args:
            user_id: ID utilisateur
            entity_type: Filtrer par type (food, device, etc.) - optionnel
            
        Returns:
            Liste d'entités [{"type": str, "name": str, "confidence": float}]
        """
        if not self.memory_service:
            return []
        
        try:
            # Récupérer tous les faits du type demandé
            if entity_type:
                facts = self.memory_service.get_facts(user_id, fact_type=entity_type)
            else:
                # Récupérer tous les types d'entités
                all_facts = []
                for etype in ["food", "device", "person", "location", "object"]:
                    facts = self.memory_service.get_facts(user_id, fact_type=etype)
                    all_facts.extend(facts)
                facts = all_facts
            
            # Parser et retourner entités
            entities = []
            for fact in facts:
                try:
                    entity_data = json.loads(fact["fact_value"])
                    entities.append({
                        "type": fact["fact_type"],
                        "name": entity_data.get("name"),
                        "confidence": entity_data.get("confidence", 0.8)
                    })
                except:
                    continue
            
            return entities
            
        except Exception as e:
            print(f"[MemoryExtractor] Error retrieving entities: {e}")
            return []
    
    def clear_cache(self, user_id: Optional[str] = None):
        """
        Nettoyer le cache d'extraction.
        
        Args:
            user_id: Si spécifié, nettoie seulement pour cet user, sinon tout le cache
        """
        if user_id:
            # Nettoyer cache pour un utilisateur spécifique
            keys_to_remove = [k for k in self._extraction_cache.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self._extraction_cache[key]
            print(f"[MemoryExtractor] Cleared cache for user {user_id}")
        else:
            # Nettoyer tout le cache
            self._extraction_cache.clear()
            print("[MemoryExtractor] Cleared entire extraction cache")
