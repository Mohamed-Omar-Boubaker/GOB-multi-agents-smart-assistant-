"""
Intent Classifier - Classification Conversation vs Action
Responsable: OMAR
Date: 2026-02-10

Classification hybride en 3 niveaux :
1. Règles rapides (mots-clés français)
2. Détection verbes d'action
3. LLM fallback si incertain
"""

import re
from datetime import datetime, UTC
from typing import Dict, Optional, List
from backend.config import Config


class IntentClassifier:
    """
    Classifier hybride pour déterminer si une commande est:
    - Conversation (small talk): "Bonjour", "Qui es-tu?"
    - Action (exécution): "Allume la lampe", "Envoie un email"
    
    Utilise 3 niveaux de classification pour précision optimale.
    """
    
    def __init__(self, method: str = "hybrid", llm_client=None, threshold: float = 0.8):
        """
        Initialiser le classifier.
        
        Args:
            method: Méthode de classification ("rules", "hybrid", "llm")
            llm_client: Instance du LLMClient pour fallback LLM (optionnel)
            threshold: Seuil de confiance pour fallback LLM
        """
        self.method = method
        self.llm_client = llm_client
        self.threshold = threshold
        
        # Niveau 1: Mots-clés CONVERSATION (français + anglais)
        self.conversation_keywords = [
            # Salutations (FR + EN)
            "bonjour", "bonsoir", "salut", "coucou", "hello", "hi", "hey",
            "good morning", "good afternoon", "good evening", "greetings",
            # Questions identité (FR + EN)
            "qui es-tu", "qui êtes-vous", "c'est quoi ton nom", "comment tu t'appelles",
            "who are you", "what's your name", "what is your name", "tell me about yourself",
            # Questions état (FR + EN)
            "comment vas-tu", "comment allez-vous", "ça va", "ca va", "comment ça va",
            "how are you", "how's it going", "what's up", "how do you do",
            # Remerciements (FR + EN)
            "merci", "thanks", "thank you", "je te remercie", "appreciate",
            # Au revoir (FR + EN)
            "au revoir", "bye", "goodbye", "à bientôt", "à plus", "tchao", "ciao",
            "see you", "see ya", "farewell", "take care",
            # Questions générales (FR + EN)
            "raconte", "parle-moi", "dis-moi", "explique-moi",
            "tell me", "explain", "talk to me", "describe",
            # Temps/météo conversation (FR + EN)
            "quelle heure", "quel jour", "quelle date",
            "what time", "what day", "what date",
            # Politesse (FR + EN)
            "s'il te plaît", "s'il vous plaît", "excuse-moi", "pardon",
            "please", "excuse me", "sorry", "pardon me"
        ]
        
        # Niveau 1: Mots-clés ACTION (français + anglais)
        self.action_keywords = [
            # IoT Lumière (FR + EN)
            "allume", "éteins", "éteint", "allumer", "éteindre",
            "turn on", "turn off", "switch on", "switch off", "light",
            # IoT Général (FR + EN)
            "ouvre", "ferme", "ouvrir", "fermer", "active", "désactive",
            "activer", "désactiver", "contrôle", "contrôler",
            "open", "close", "activate", "deactivate", "enable", "disable", "control",
            # Communication (FR + EN)
            "envoie", "envoyer", "email", "mail", "message", "sms",
            "appelle", "appeler", "téléphone", "rappelle", "rappeler",
            "send", "email", "mail", "message", "call", "phone", "dial", "text",
            # Automatisation (FR + EN)
            "programme", "programmer", "planifie", "planifier",
            "rappelle-moi", "rappeler", "alarme", "réveil",
            "schedule", "program", "set", "remind", "reminder", "alarm", "timer",
            # Recherche (FR + EN)
            "cherche", "chercher", "recherche", "rechercher", "trouve", "trouver",
            "search", "find", "look for", "locate", "query",
            # Commandes système (FR + EN)
            "lance", "lancer", "démarre", "démarrer", "arrête", "arrêter", "stop",
            "start", "launch", "run", "execute", "stop", "quit", "kill"
        ]
        
        # Niveau 2: Verbes d'action (infinitifs français + anglais)
        self.action_verbs = [
            # IoT (FR + EN)
            "allumer", "éteindre", "ouvrir", "fermer", "activer", "désactiver",
            "turn", "switch", "open", "close", "activate", "deactivate",
            "régler", "ajuster", "monter", "descendre", "augmenter", "diminuer",
            "adjust", "set", "increase", "decrease", "raise", "lower",
            # Communication (FR + EN)
            "envoyer", "transmettre", "écrire", "rédiger", "appeler", "contacter",
            "send", "transmit", "write", "compose", "call", "contact", "dial",
            # Automatisation (FR + EN)
            "programmer", "planifier", "créer", "supprimer", "modifier",
            "schedule", "program", "create", "delete", "modify", "update",
            # Recherche (FR + EN)
            "chercher", "rechercher", "trouver", "localiser", "identifier",
            "search", "find", "locate", "identify", "discover",
            # Multimédia (FR + EN)
            "jouer", "lire", "écouter", "regarder", "afficher", "montrer",
            "play", "read", "listen", "watch", "display", "show"
        ]
        
        # Patterns de questions conversationnelles (FR + EN)
        self.conversation_patterns = [
            # Français
            r"^(qui|quoi|comment|pourquoi|où|quand|quel|quelle)\s",
            r"(es-tu|êtes-vous)",
            r"(peux-tu|pouvez-vous).+(me parler|m'expliquer|me dire)",
            r"(raconte|parle).+(de toi|sur toi)",
            # Anglais
            r"^(who|what|how|why|where|when|which)\s",
            r"(are you|do you)",
            r"(can you|could you).+(tell me|explain)",
            r"(tell me|talk).+(about yourself|about you)"
        ]
        
        print(f"[Classifier] Initialized - Method: {method}, Threshold: {threshold}")
    
    async def classify(self, text: str, request_id: Optional[str] = None) -> Dict:
        """
        Classifier une commande utilisateur (méthode principale pour Agent Core).
        
        Args:
            text: Texte de la commande
            request_id: ID de la requête (optionnel)
        
        Returns:
            {
                "classification": "conversation" | "action",
                "confidence": float,
                "method": str,
                "reasoning": dict,
                "timestamp": str
            }
        """
        if not text or not text.strip():
            return {
                "classification": "conversation",
                "confidence": 0.0,
                "method": "empty_input",
                "reasoning": {"reason": "Empty text"},
                "timestamp": datetime.now(UTC).isoformat()
            }
        
        text_lower = text.lower().strip()
        
        # Choix de la méthode
        if self.method == "rules":
            result = self._classify_by_rules(text_lower)
        elif self.method == "hybrid":
            result = await self._classify_hybrid(text_lower)
        elif self.method == "llm" and self.llm_client:
            result = await self._classify_by_llm(text_lower)
        else:
            # Fallback: règles
            result = self._classify_by_rules(text_lower)
        
        # Ajouter métadonnées
        result["request_id"] = request_id or f"clf_{int(datetime.now(UTC).timestamp() * 1000)}"
        result["timestamp"] = datetime.now(UTC).isoformat()
        
        return result
    
    def _classify_by_rules(self, text: str) -> Dict:
        """
        Niveau 1: Classification par règles de mots-clés.
        Rapide mais peut manquer de précision.
        """
        # Comptage mots-clés conversation
        conv_count = sum(1 for kw in self.conversation_keywords if kw in text)
        
        # Comptage mots-clés action
        action_count = sum(1 for kw in self.action_keywords if kw in text)
        
        # Vérifier patterns conversationnels
        pattern_match = any(re.search(pattern, text) for pattern in self.conversation_patterns)
        if pattern_match:
            conv_count += 2  # Boost pour patterns
        
        # Décision
        if action_count > conv_count:
            confidence = min(0.85, 0.65 + (action_count * 0.1))
            return {
                "classification": "action",
                "confidence": confidence,
                "method": "rules",
                "reasoning": {
                    "action_keywords": action_count,
                    "conversation_keywords": conv_count,
                    "decision": "More action keywords detected"
                }
            }
        else:
            confidence = 0.75 if conv_count > 0 else 0.60
            return {
                "classification": "conversation",
                "confidence": confidence,
                "method": "rules",
                "reasoning": {
                    "action_keywords": action_count,
                    "conversation_keywords": conv_count,
                    "pattern_match": pattern_match,
                    "decision": "More conversation indicators"
                }
            }
    
    def _detect_action_verbs(self, text: str) -> Dict:
        """
        Niveau 2: Détection de verbes d'action.
        Améliore la précision pour les commandes actionnables.
        """
        words = text.split()
        detected_verbs = [verb for verb in self.action_verbs if verb in words or verb in text]
        
        if detected_verbs:
            # Verbe d'action détecté → boost confidence
            confidence = min(0.95, 0.75 + len(detected_verbs) * 0.1)
            return {
                "has_action_verb": True,
                "verbs": detected_verbs,
                "confidence_boost": confidence
            }
        
        return {
            "has_action_verb": False,
            "verbs": [],
            "confidence_boost": 0.0
        }
    
    async def _classify_hybrid(self, text: str) -> Dict:
        """
        Niveau 3: Classification hybride (règles + verbes + LLM fallback).
        Méthode recommandée pour meilleure précision.
        """
        # 1. Classification par règles (base)
        result = self._classify_by_rules(text)
        
        # 2. Détection verbes d'action (amélioration)
        verb_analysis = self._detect_action_verbs(text)
        
        if verb_analysis["has_action_verb"]:
            # Verbe d'action trouvé → probablement une action
            result["classification"] = "action"
            result["confidence"] = verb_analysis["confidence_boost"]
            result["method"] = "hybrid_rules_verbs"
            result["reasoning"]["action_verbs"] = verb_analysis["verbs"]
        
        # 3. Si confiance < seuil ET LLM disponible → fallback LLM
        if result["confidence"] < self.threshold and self.llm_client:
            try:
                llm_result = await self._classify_by_llm(text)
                # Utiliser résultat LLM si plus confiant
                if llm_result["confidence"] > result["confidence"]:
                    result = llm_result
                    result["method"] = "hybrid_llm_fallback"
                    result["reasoning"]["fallback_reason"] = "Low confidence, used LLM"
            except Exception as e:
                # LLM échec → garder résultat règles
                result["reasoning"]["llm_fallback_error"] = str(e)
        
        return result
    
    async def _classify_by_llm(self, text: str) -> Dict:
        """
        Niveau 3 (alternatif): Classification via LLM.
        Plus précis mais plus lent et coûteux.
        """
        if not self.llm_client:
            raise RuntimeError("LLM client not available for classification")
        
        try:
            # Prompt simple pour classification binaire
            prompt = f"""Classify this user input as either "conversation" or "action".

Rules:
- "conversation": greetings, questions about you, small talk, general questions
- "action": commands to control devices, send messages, search, automate tasks

User input: "{text}"

Respond with ONLY ONE WORD: conversation OR action"""
            
            # Utiliser méthode conversation du LLM (pas d'historique)
            response = await self.llm_client.generate_conversation_response(
                user_input=prompt,
                user_id="classifier_temp",
                language=Config.DEFAULT_LANGUAGE
            )
            
            reply = response["response"].lower().strip()
            
            # Parser réponse
            if "action" in reply:
                classification = "action"
                confidence = 0.90
            elif "conversation" in reply:
                classification = "conversation"
                confidence = 0.90
            else:
                # Fallback si réponse ambiguë
                classification = "conversation"
                confidence = 0.60
            
            # Nettoyer conversation temporaire
            self.llm_client.clear_conversation("classifier_temp")
            
            return {
                "classification": classification,
                "confidence": confidence,
                "method": "llm",
                "reasoning": {
                    "llm_response": reply,
                    "model": self.llm_client.model
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"LLM classification failed: {e}")
    
    def get_stats(self) -> Dict:
        """Retourne statistiques du classifier."""
        return {
            "method": self.method,
            "threshold": self.threshold,
            "has_llm": self.llm_client is not None,
            "conversation_keywords_count": len(self.conversation_keywords),
            "action_keywords_count": len(self.action_keywords),
            "action_verbs_count": len(self.action_verbs)
        }
