"""
Agent Core - Orchestrateur principal
Responsable: Montassar
Priorité: 🔴 CRITIQUE
Temps estimé: 30h

INPUT JSON (Commande texte):
{
  "command_type": "text",
  "user_id": "user_001",
  "text": "Allume la lampe du salon",
  "language": "fr",
  "source": "text"
}

INPUT JSON (Commande audio):
{
  "command_type": "audio",
  "user_id": "user_001",
  "audio_data": "UklGRiQAAABXQVZFZm10...",
  "audio_format": "wav",
  "language": "fr",
  "source": "voice"
}

OUTPUT JSON:
{
  "request_id": "req_abc123",
  "user_id": "user_001",
  "classification": "action",
  "response": {
    "type": "action",
    "action_id": "act_abc123xyz",
    "state": "PENDING_CONFIRMATION",
    "message": "Voulez-vous vraiment allumer la lampe du salon ?",
    "audio_response": "..."
  },
  "processing_time_ms": 2345
}

Rôle: Orchestre TOUS les autres composants
"""

import uuid
import time
import re
from typing import Dict, Optional
from datetime import datetime, UTC
from backend.agent.logger import Logger
from backend.agent.state_manager import StateManager, ActionState
from backend.services.memory_extractor import MemoryExtractor  # 🔥 NEW: Memory extraction
from backend.config import Config
from backend.utils.exceptions import ValidationError
import httpx

class AgentCore:
    """
    Cerveau central de l'agent intelligent.
    Orchestre tous les composants Backend pour traiter les commandes utilisateur.
    
    Pipeline Conversation:
    1. Réception texte/audio
    2. STT (si audio)
    3. Classification → Conversation
    4. LLM génère réponse
    5. TTS génère audio
    6. Retour immédiat
    
    Pipeline Action:
    1. Réception texte/audio
    2. STT (si audio)
    3. Classification → Action
    4. LLM analyse intention
    5. ActionBuilder construit JSON
    6. StateManager crée action (DRAFT)
    7. ConfirmationHandler génère message
    8. Retour pour confirmation
    9. [Utilisateur confirme]
    10. SecurityManager signe action
    11. StateManager → CONFIRMED → EXECUTING
    12. N8N exécute
    13. StateManager → COMPLETED/FAILED
    """
    
    def __init__(
        self,
        stt_engine=None,
        tts_engine=None,
        llm_client=None,
        classifier=None,
        action_builder=None,
        confirmation_handler=None,
        n8n_client=None,
        mqtt_client=None,
        security_manager=None,
        memory_service=None  # 🔥 NEW: Persistent memory service
    ):
        """
        Initialiser Agent Core avec tous ses composants.
        
        Args:
            stt_engine: Moteur Speech-to-Text (Omar)
            tts_engine: Moteur Text-to-Speech (Omar)
            llm_client: Client LLM (Amine)
            classifier: Classificateur intentions (Amine)
            action_builder: Constructeur d'actions (Amine)
            confirmation_handler: Gestionnaire confirmations (Amine)
            n8n_client: Client n8n (Omar)
            mqtt_client: Client MQTT (Omar)
            security_manager: Gestionnaire sécurité (Montassar)
            memory_service: Service mémoire persistante (Montassar)
        """
        # Composants déjà implémentés
        self.logger = Logger(log_file="logs/agent_core.log")
        self.state_manager = StateManager()
        
        # Composants à implémenter par les autres (injection de dépendances)
        self.stt_engine = stt_engine
        self.tts_engine = tts_engine
        self.llm_client = llm_client
        self.classifier = classifier
        self.action_builder = action_builder
        self.confirmation_handler = confirmation_handler
        self.n8n_client = n8n_client
        self.mqtt_client = mqtt_client
        self.memory_service = memory_service  # 🔥 NEW: Persistent memory
        
        # 🔥 NEW: Memory Extractor (auto-initialized if LLM available)
        self.memory_extractor = None
        if llm_client and memory_service:
            self.memory_extractor = MemoryExtractor(
                llm_client=llm_client,
                memory_service=memory_service,
                enable_cache=True
            )
            self.logger.info("✨ Memory Extractor initialized")
        
        # Security Manager (si fourni, sinon on importe le nôtre)
        if security_manager:
            self.security_manager = security_manager
        else:
            from backend.agent.security_manager import SecurityManager
            self.security_manager = SecurityManager()
        
        # Configuration
        self.classifier_threshold = 0.7  # Seuil de confiance minimum
        self.max_retries = 3
        
        self.logger.info("AgentCore initialized successfully")
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Point d'entrée principal pour traiter une commande utilisateur.
        
        Args:
            input_data: {
                "command_type": "text" ou "audio",
                "user_id": str,
                "text": str (si text),
                "audio_data": str (si audio, base64),
                "audio_format": str (si audio),
                "language": str (défaut: "fr"),
                "source": str (optionnel)
            }
            
        Returns:
            {
                "request_id": str,
                "user_id": str,
                "classification": "conversation" ou "action",
                "response": {...},
                "processing_time_ms": int
            }
        """
        start_time = time.time()
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        self.logger.info(
            f"Processing request {request_id}",
            extra={"request_id": request_id, "user_id": input_data.get("user_id")}
        )
        
        try:
            # Validation input
            if "command_type" not in input_data:
                raise ValueError("Missing required field: command_type")
            if "user_id" not in input_data:
                raise ValueError("Missing required field: user_id")
            
            command_type = input_data["command_type"]
            user_id = input_data["user_id"]
            language = (input_data.get("language") or Config.DEFAULT_LANGUAGE).lower()
            if language not in {"fr", "en", "ar"}:
                language = Config.DEFAULT_LANGUAGE
            
            # 1. Obtenir le texte (directement ou via STT)
            if command_type == "text":
                text = input_data.get("text")
                if not text:
                    raise ValueError("Missing required field: text")
                transcription = None
            
            elif command_type == "audio":
                audio_data = input_data.get("audio_data")
                audio_format = input_data.get("audio_format", "wav")
                
                if not audio_data:
                    raise ValueError("Missing required field: audio_data")
                
                # Appel STT
                if not self.stt_engine:
                    raise RuntimeError("STT Engine not configured")
                
                transcription = await self._call_stt(audio_data, audio_format, language)
                text = transcription
                
                if not text or not text.strip():
                    empty_transcription_messages = {
                        "en": "I didn't catch that. Could you please repeat?",
                        "fr": "Je n'ai pas compris, pouvez-vous répéter ?",
                        "ar": "لم أفهم. هل يمكنك التكرار من فضلك؟"
                    }
                    return {
                        "request_id": request_id,
                        "status": "error",
                        "error": "empty_transcription",
                        "response": empty_transcription_messages.get(language, empty_transcription_messages[Config.DEFAULT_LANGUAGE]),
                        "processing_time_ms": int((time.time() - start_time) * 1000)
                    }
            
            else:
                raise ValueError(f"Invalid command_type: {command_type}")
            
            self.logger.log_conversation(
                user_id=user_id,
                input_text=text,
                response_text="",
                request_id=request_id
            )
            
            # 🔥 PRIORITY 1: Check for pending action BEFORE classification
            # This preserves action context for confirmation responses
            pending_action = self.state_manager.get_pending_action(user_id)
            
            if pending_action:
                self.logger.info(
                    f"⚡ Pending action detected for user {user_id}, bypassing NLP",
                    extra={"request_id": request_id, "action_id": pending_action["action_id"]}
                )
                
                # Route directly to confirmation handler (no classification needed)
                result = await self._handle_pending_confirmation(
                    text=text,
                    user_id=user_id,
                    language=language,
                    pending_action=pending_action,
                    request_id=request_id
                )
                
                # Update processing time and return
                result["request_id"] = request_id
                result["processing_time_ms"] = int((time.time() - start_time) * 1000)
                if transcription is not None:
                    result["transcription"] = transcription
                
                return result
            
            # 2. Classification Conversation vs Action (only if NO pending action)
            classification = await self._classify_intent(text, language)
            
            self.logger.info(
                f"Classification: {classification['type']} (confidence: {classification.get('confidence', 0)})",
                extra={"request_id": request_id, "classification": classification}
            )
            
            # 🔥 FIX #5: Confidence-based clarification (Safe AI)
            confidence = classification.get("confidence", 1.0)
            
            # Zone 1: Very Low Confidence (<0.50) → Reject & Ask to Repeat
            if confidence < Config.CLARIFICATION_CONFIDENCE_MIN:
                self.logger.warning(
                    f"⚠️ Very low confidence ({confidence:.2f}), asking user to repeat",
                    extra={"request_id": request_id, "confidence": confidence}
                )
                clarification_messages = {
                    "en": "I'm sorry, I didn't catch that clearly. Could you please repeat?",
                    "fr": "Excusez-moi, je n'ai pas bien compris. Pouvez-vous répéter s'il vous plaît?",
                    "ar": "عذراً، لم أسمعك بوضوح. هل يمكنك الإعادة من فضلك؟"
                }
                result = {
                    "status": "low_confidence_rejection",
                    "response": clarification_messages.get(language, clarification_messages["en"]),
                    "needs_clarification": True,
                    "confidence": confidence,
                    "classification": classification["type"]
                }
                result["request_id"] = request_id
                result["user_id"] = user_id
                result["processing_time_ms"] = int((time.time() - start_time) * 1000)
                if transcription:
                    result["transcription"] = transcription
                return result
            
            # Zone 2: Medium Confidence (0.50-0.75) → Ask Clarification Question
            elif confidence < Config.CLARIFICATION_CONFIDENCE_MAX:
                self.logger.info(
                    f"🤔 Medium confidence ({confidence:.2f}), asking clarification",
                    extra={"request_id": request_id, "confidence": confidence}
                )
                clarification_questions = {
                    "en": f"I'm not entirely sure I understood correctly (confidence: {confidence:.0%}). Do you want to:\n1️⃣ Control a smart device (action)\n2️⃣ Have a conversation\n\nPlease clarify your intent.",
                    "fr": f"Je ne suis pas totalement sûr d'avoir bien compris (confiance: {confidence:.0%}). Voulez-vous:\n1️⃣ Contrôler un appareil intelligent (action)\n2️⃣ Avoir une conversation\n\nVeuillez clarifier votre intention.",
                    "ar": f"لست متأكدًا تمامًا من فهمي (الثقة: {confidence:.0%}). هل تريد:\n1️⃣ التحكم في جهاز ذكي (إجراء)\n2️⃣ إجراء محادثة\n\nمن فضلك وضح نيتك."
                }
                result = {
                    "status": "needs_clarification",
                    "response": clarification_questions.get(language, clarification_questions["en"]),
                    "needs_clarification": True,
                    "confidence": confidence,
                    "classification": classification["type"],
                    "suggested_type": classification["type"]  # Agent's best guess
                }
                result["request_id"] = request_id
                result["user_id"] = user_id
                result["processing_time_ms"] = int((time.time() - start_time) * 1000)
                if transcription:
                    result["transcription"] = transcription
                return result
            
            # Zone 3: High Confidence (≥0.75) → Proceed Normally
            self.logger.info(
                f"✅ High confidence ({confidence:.2f}), proceeding with {classification['type']}",
                extra={"request_id": request_id, "confidence": confidence}
            )
            
            # 3. Routage selon le type
            if classification["type"] == "conversation":
                result = await self._handle_conversation(
                    text=text,
                    user_id=user_id,
                    language=language,
                    request_id=request_id
                )
            else:  # action
                result = await self._handle_action(
                    text=text,
                    user_id=user_id,
                    language=language,
                    classification=classification,
                    request_id=request_id
                )
            
            # Ajout transcription si audio
            if transcription:
                result["transcription"] = transcription
            
            # Ajout métadonnées
            result["request_id"] = request_id
            result["user_id"] = user_id
            result["classification"] = classification["type"]
            result["processing_time_ms"] = int((time.time() - start_time) * 1000)
            
            self.logger.info(
                f"Request {request_id} completed successfully",
                extra={"request_id": request_id, "processing_time_ms": result["processing_time_ms"]}
            )
            
            return result
        
        except Exception as e:
            self.logger.error(
                f"Error processing request {request_id}: {str(e)}",
                extra={"request_id": request_id, "error": str(e), "error_type": type(e).__name__}
            )
            
            return {
                "request_id": request_id,
                "user_id": input_data.get("user_id", "unknown"),
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "response": "Désolé, une erreur s'est produite lors du traitement de votre demande.",
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    async def _dispatch_reminder_to_n8n(self, action_json: Dict) -> Dict:
        """
        Dispatch reminder to the dedicated n8n reminder workflow.
        
        Args:
            action_json: The full ActionJSON with reminder payload
            
        Returns:
            n8n response dict
        """
        payload = action_json.get("payload", {})
        title = payload.get("title", "Rappel")
        reminder_time = payload.get("reminder_time", payload.get("time"))
        user_id = action_json.get("user_id", "unknown")
        action_id = action_json.get("action_id", "unknown")
        language = action_json.get("context", {}).get("language", "fr")
        
        # N8N reminder webhook URL
        n8n_reminder_url = getattr(Config, 'N8N_WEBHOOK_REMINDER_URL', None) or \
                        "http://localhost:5678/webhook/reminder"
        
        if not reminder_time:
            raise ValueError("Reminder time is required for set_reminder intent")
        
        self.logger.info(
            f"📅 Dispatching reminder to n8n: '{title}' at {reminder_time}",
            extra={"action_id": action_id, "n8n_url": n8n_reminder_url}
        )
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    n8n_reminder_url,
                    json={
                        "title": title,
                        "reminder_datetime": reminder_time,
                        "user_id": user_id,
                        "action_id": action_id,
                        "language": language,
                        "callback_url": f"http://localhost:8000/callback/n8n",
                        "description": payload.get("description", "")
                    },
                    headers={
                        "Content-Type": "application/json",
                        "X-GOB-Source": "agent-core",
                        "X-Action-ID": action_id
                    }
                )
                
                if response.status_code in (200, 201):
                    result = response.json()
                    self.logger.info(
                        f"✅ Reminder dispatched successfully: {result.get('action_id')}",
                        extra={"action_id": action_id}
                    )
                    return {
                        "status": "success",
                        "message": result.get("message", "Rappel programmé"),
                        "ics_download_url": result.get("ics_download_url"),
                        "calendar_page_url": result.get("calendar_page_url"),
                        "n8n_action_id": result.get("action_id")
                    }
                else:
                    raise RuntimeError(f"n8n returned {response.status_code}: {response.text[:200]}")
        
        except httpx.TimeoutException:
            raise RuntimeError(f"n8n reminder webhook timed out")
        except httpx.ConnectError as e:
            raise RuntimeError(f"Cannot connect to n8n at {n8n_reminder_url}: {e}")

    async def _call_stt(self, audio_data: str, audio_format: str, language: str) -> str:
        """
        Appeler le moteur STT pour transcription.
        
        Args:
            audio_data: Audio encodé en base64
            audio_format: Format audio
            language: Langue
            
        Returns:
            Texte transcrit
        """
        if not self.stt_engine:
            raise RuntimeError("STT Engine not configured")
        
        try:
            result = await self.stt_engine.transcribe(audio_data, audio_format, language)
            
            if isinstance(result, dict):
                transcription = result.get("transcription", "")
            else:
                transcription = str(result)

            if transcription is None:
                return ""

            normalized = str(transcription).strip()
            if normalized.lower() in {"none", "null", "undefined"}:
                return ""

            return normalized
        
        except Exception as e:
            self.logger.error(f"STT error: {e}")
            raise RuntimeError(f"Speech-to-Text failed: {e}")
    
    async def _classify_intent(self, text: str, language: str) -> Dict:
        """
        Classifier l'intention (Conversation vs Action).
        
        Args:
            text: Texte à classifier
            language: Langue
            
        Returns:
            {"type": "conversation/action", "confidence": float, "intent": str}
        """
        # Si classifier pas configuré, classification par défaut basique
        if not self.classifier:
            # Règles simples par mots-clés
            action_keywords = ["allume", "éteins", "ouvre", "ferme", "lance", "démarre", "arrête", "mets", "active", "désactive"]
            text_lower = text.lower()
            
            is_action = any(keyword in text_lower for keyword in action_keywords)
            
            return {
                "type": "action" if is_action else "conversation",
                "confidence": 0.8 if is_action else 0.6,
                "intent": "control_iot" if is_action else "conversation",
                "method": "rules_fallback"
            }
        
        try:
            result = await self.classifier.classify(text)
            
            # Normaliser le résultat
            if isinstance(result, dict):
                return {
                    "type": result.get("classification", result.get("type", "conversation")),
                    "confidence": result.get("confidence", 0.7),
                    "intent": result.get("intent", "unknown"),
                    "method": result.get("method", "classifier")
                }
            
            return {"type": "conversation", "confidence": 0.5, "intent": "unknown"}
        
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return {"type": "conversation", "confidence": 0.5, "intent": "error"}
    
    def _validate_action_entities(self, llm_analysis: Dict, language: str) -> Dict:
        """
        Valider que l'action a toutes les entités requises.
        Si entités manquantes, retourner une question de clarification.
        
        Args:
            llm_analysis: Analyse LLM avec intent et entities
            language: Langue pour la question
            
        Returns:
            {
                "valid": bool,
                "missing_info": list,
                "clarification_question": str
            }
        """
        intent = llm_analysis.get("primary_intent", "unknown")
        entities = llm_analysis.get("entities", {})
        
        # Définir les entités requises par intent
        required_entities = {
            "control_iot": ["device", "action"],
            "send_email": ["recipient"],  # Au moins le nom du destinataire
            "set_reminder": ["time"],  # Au moins le temps
            "web_search": ["query"]
        }
        
        # Questions de clarification bilingues
        clarification_templates = {
            "send_email": {
                "en": "Who would you like to send an email to?",
                "fr": "À qui souhaitez-vous envoyer un email ?"
            },
            "control_iot": {
                "en": "Which device would you like to control?",
                "fr": "Quel appareil souhaitez-vous contrôler ?"
            },
            "set_reminder": {
                "en": "When would you like to be reminded?",
                "fr": "Quand voulez-vous être rappelé ?"
            },
            "web_search": {
                "en": "What would you like to search for?",
                "fr": "Que souhaitez-vous rechercher ?"
            }
        }
        
        # Vérifier si l'intent nécessite validation
        if intent not in required_entities:
            return {"valid": True, "missing_info": [], "clarification_question": ""}
        
        # Vérifier présence des entités requises
        missing = []
        for required_entity in required_entities[intent]:
            if required_entity not in entities or not entities[required_entity]:
                missing.append(required_entity)
        
        # Si entités manquantes
        if missing:
            question_template = clarification_templates.get(intent, {})
            question = question_template.get(language, question_template.get("en", "Could you provide more details?"))
            
            return {
                "valid": False,
                "missing_info": missing,
                "clarification_question": question
            }
        
        return {"valid": True, "missing_info": [], "clarification_question": ""}

    @staticmethod
    def _sanitize_name_candidate(candidate: str) -> Optional[str]:
        """Nettoyer et normaliser un nom utilisateur extrait depuis du texte libre."""
        if not candidate:
            return None

        cleaned = candidate.strip(" \t\n\r\"'.,;:!?()[]{}")
        cleaned = re.split(r"\b(?:if|and|but|please|save|remember|say|si|et|mais|svp)\b", cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
        parts = re.findall(r"[A-Za-zÀ-ÿ\u0600-\u06FF][A-Za-zÀ-ÿ\u0600-\u06FF'\-]*", cleaned)

        if not parts:
            return None

        blocked = {"user", "utilisateur", "name", "nom", "me", "moi"}
        filtered = [p for p in parts[:3] if p.lower() not in blocked]
        if not filtered:
            return None

        normalized = " ".join(filtered)
        if len(normalized) < 2:
            return None

        return normalized

    def _extract_explicit_name_statement(self, text: str) -> Optional[str]:
        """Détecter les formulations explicites où l'utilisateur donne son nom."""
        if not text:
            return None

        patterns = [
            r"\b(?:my\s+name\s+is|name\s+is|call\s+me)\s+([^\n\.!\?]{1,60})",
            r"\b(?:je\s+m['’]appelle|mon\s+nom\s+est|appelle[-\s]?moi)\s+([^\n\.!\?]{1,60})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue

            name = self._sanitize_name_candidate(match.group(1))
            if name:
                return name

        return None

    @staticmethod
    def _is_name_question(text: str) -> bool:
        """Détecter les questions de rappel de nom utilisateur."""
        if not text:
            return False

        normalized = re.sub(r"\s+", " ", text.lower()).strip()
        queries = [
            "what is my name",
            "what's my name",
            "who am i",
            "quel est mon nom",
            "c'est quoi mon nom",
            "c est quoi mon nom",
            "ما اسمي",
            "شنو اسمي",
        ]
        return any(q in normalized for q in queries)

    def _save_user_name_fact(self, user_id: str, name: str) -> bool:
        """Persister le nom utilisateur dans la mémoire structurée."""
        if not self.memory_service:
            return False

        try:
            stored_primary = self.memory_service.add_fact(
                user_id=user_id,
                fact_type="name",
                fact_key="preferred_name",
                fact_value=name,
                confidence=1.0,
            )

            first_name = name.split()[0]
            self.memory_service.add_fact(
                user_id=user_id,
                fact_type="name",
                fact_key="first_name",
                fact_value=first_name,
                confidence=1.0,
            )

            return bool(stored_primary)
        except Exception as e:
            self.logger.warning(f"Failed to save user name fact: {e}")
            return False

    def _get_saved_user_name(self, user_id: str) -> Optional[str]:
        """Récupérer le nom utilisateur depuis la mémoire structurée."""
        if not self.memory_service:
            return None

        try:
            preferred = self.memory_service.get_fact(user_id, "name", "preferred_name")
            cleaned_preferred = self._sanitize_name_candidate(preferred or "")
            if cleaned_preferred:
                return cleaned_preferred

            first_name = self.memory_service.get_fact(user_id, "name", "first_name")
            cleaned_first_name = self._sanitize_name_candidate(first_name or "")
            if cleaned_first_name:
                return cleaned_first_name
        except Exception as e:
            self.logger.warning(f"Failed to read user name fact: {e}")

        return None

    @staticmethod
    def _name_saved_response(name: str, language: str, saved: bool) -> str:
        """Construire la réponse de confirmation après sauvegarde du nom."""
        if language == "fr":
            return (
                f"D'accord, j'ai bien enregistré votre nom: {name}."
                if saved
                else f"J'ai compris que votre nom est {name}, mais je n'ai pas pu l'enregistrer maintenant."
            )
        if language == "ar":
            return (
                f"حسنا، تم حفظ اسمك: {name}."
                if saved
                else f"فهمت أن اسمك {name} لكن لم أتمكن من حفظه الآن."
            )
        return (
            f"Got it. I saved your name as {name}."
            if saved
            else f"I understood your name is {name}, but I could not save it right now."
        )

    @staticmethod
    def _name_query_response(name: Optional[str], language: str) -> str:
        """Construire la réponse déterministe pour les questions de nom."""
        if name:
            if language == "fr":
                return f"Votre nom est {name}."
            if language == "ar":
                return f"اسمك هو {name}."
            return f"Your name is {name}."

        if language == "fr":
            return "Je ne connais pas encore votre nom. Dites-moi: mon nom est ..."
        if language == "ar":
            return "لا أعرف اسمك بعد. قل لي: اسمي هو ..."
        return "I do not know your name yet. Tell me: my name is ..."
    
    async def _handle_conversation(
        self,
        text: str,
        user_id: str,
        language: str,
        request_id: str
    ) -> Dict:
        """
        Gérer une interaction de type Conversation.
        Pipeline: LLM → TTS → Réponse immédiate
        
        Args:
            text: Texte de la conversation
            user_id: ID utilisateur
            language: Langue
            request_id: ID de la requête
            
        Returns:
            {"type": "conversation", "response": str, "audio": str}
        """
        self.logger.info(f"Handling conversation: '{text}'", extra={"request_id": request_id})

        deterministic_response = None
        deterministic_model_used = None

        explicit_name = self._extract_explicit_name_statement(text)
        if explicit_name:
            saved = self._save_user_name_fact(user_id, explicit_name)
            deterministic_response = self._name_saved_response(explicit_name, language, saved)
            deterministic_model_used = "deterministic_name_save"
        elif self._is_name_question(text):
            saved_name = self._get_saved_user_name(user_id)
            deterministic_response = self._name_query_response(saved_name, language)
            deterministic_model_used = "deterministic_name_query"
        
        # 🔥 STEP 1: Get memory context before LLM call
        memory_context = ""
        if self.memory_service:
            try:
                # Use only structured user facts for prompt memory context.
                # Do not inject raw conversation transcript here to avoid
                # anchoring LLM replies to stale/irrelevant past topics.
                memory_context = self.memory_service.build_memory_context(user_id, max_facts=10)
                
                if memory_context:
                    self.logger.info(f"📚 Memory context loaded: {len(memory_context)} chars")
            except Exception as e:
                self.logger.warning(f"Failed to load memory context: {e}")
                memory_context = ""
        
        try:
            # 2. Génération réponse par LLM with graceful degradation
            if deterministic_response is not None:
                response_text = deterministic_response
                model_used = deterministic_model_used or "deterministic"

            elif self.llm_client:
                try:
                    llm_response = await self.llm_client.generate_conversation_response(
                        user_input=text,
                        user_id=user_id,
                        language=language,
                        memory_context=memory_context  # 🔥 Inject memory context
                    )
                    response_text = llm_response.get("response", "Je n'ai pas de réponse pour le moment.")
                    response_text = self._strip_trailing_translation(response_text, language)
                    model_used = llm_response.get("model_used", "unknown")
                
                except Exception as e:
                    # 🔥 GRACEFUL DEGRADATION: LLM failed, use fallback
                    self.logger.error(f"LLM failed: {e}, using fallback response")
                    
                    fallback_responses = {
                        "en": "I'm experiencing a temporary connection issue, but I'm still operational. Could you please repeat?",
                        "fr": "Je rencontre un problème de connexion temporaire, mais je reste opérationnel. Pouvez-vous répéter ?",
                        "ar": "أواجه مشكلة اتصال مؤقتة، لكنني لا أزال أعمل. هل يمكنك تكرار ذلك؟"
                    }
                    response_text = fallback_responses.get(language, fallback_responses["en"])
                    model_used = "fallback"
            else:
                # Fallback si pas de LLM configuré
                response_text = f"Vous avez dit : {text}. Je suis un agent en cours de développement."
                model_used = "none"
            
            # 🔥 STEP 2: Store conversation in memory
            if self.memory_service:
                try:
                    self.memory_service.add_conversation_turn(user_id, "user", text)
                    self.memory_service.add_conversation_turn(user_id, "assistant", response_text)
                    self.logger.info(f"💾 Conversation stored in memory")
                except Exception as e:
                    self.logger.warning(f"Failed to store conversation: {e}")
            
            # 🔥 NEW: Extract metadata (entities, emotions, intent) from conversation
            extracted_metadata = None
            if self.memory_extractor:
                try:
                    extracted_metadata = await self.memory_extractor.extract_from_conversation(
                        user_message=text,
                        user_id=user_id,
                        assistant_response=response_text,
                        store_results=True  # Auto-store in MemoryService
                    )
                    self.logger.info(
                        f"✨ Extracted: {len(extracted_metadata.get('entities', []))} entities, "
                        f"emotion={extracted_metadata.get('emotion')}, intent={extracted_metadata.get('intent')}"
                    )
                except Exception as e:
                    self.logger.warning(f"Memory extraction failed (non-blocking): {e}")
            
            # 3. Génération audio (TTS)
            audio_response = None
            if self.tts_engine:
                try:
                    audio_response = await self.tts_engine.synthesize(response_text, language)
                except Exception as e:
                    self.logger.warning(f"TTS failed: {e}")
            
            # 2.1 Auto-publish audio to MQTT (ESP32/Device)
            if audio_response and self.mqtt_client:
                if Config.AUTO_PUBLISH_AUDIO_TO_MQTT and self.mqtt_client.is_connected():
                    try:
                        mqtt_result = self.mqtt_client.publish_audio(
                            audio_response["audio_data"],
                            user_id=user_id
                        )
                        self.logger.info(f"✅ Audio auto-published to device: {mqtt_result['status']}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Auto-publish audio failed (non-blocking): {e}")
            
            # 3. Journalisation
            self.logger.log_conversation(
                user_id=user_id,
                input_text=text,
                response_text=response_text,
                request_id=request_id
            )
            
            # 🔥 Build response with metadata
            result = {
                "type": "conversation",
                "response": response_text,
                "audio": audio_response,
                "status": "completed"
            }
            
            # Add extracted metadata if available (for React UI)
            if extracted_metadata:
                result["metadata"] = {
                    "entities": extracted_metadata.get("entities", []),
                    "emotion": extracted_metadata.get("emotion", "neutral"),
                    "intent": extracted_metadata.get("intent", "general_chat"),
                    "summary": extracted_metadata.get("summary", ""),
                    "extracted_at": extracted_metadata.get("extracted_at")
                }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error handling conversation: {e}", extra={"request_id": request_id})
            return {
                "type": "conversation",
                "response": "Désolé, je n'ai pas pu traiter votre message.",
                "status": "error",
                "error": str(e)
            }

    def _strip_trailing_translation(self, text: str, language: str) -> str:
        """Remove trailing parenthetical translation when a single language is expected."""
        if not text:
            return text

        match = re.search(r"\s*\(([^()]*)\)\s*$", text)
        if not match:
            return text

        content = match.group(1).strip()
        if not content:
            return text

        forced_lang = Config.FORCE_LLM_RESPONSE_LANGUAGE or language
        forced_lang = (forced_lang or "").lower()

        if forced_lang in {"fr", "ar"}:
            has_latin = re.search(r"[A-Za-z]", content) is not None
            has_french_accent = re.search(r"[àâçéèêëîïôûùüÿœæ]", content, re.IGNORECASE) is not None
            has_arabic = re.search(r"[\u0600-\u06FF]", content) is not None

            if forced_lang == "fr" and has_latin and not has_french_accent and not has_arabic:
                return text[:match.start()].rstrip()

            if forced_lang == "ar" and has_latin and not has_arabic:
                return text[:match.start()].rstrip()

        return text
    
    async def _handle_action(
        self,
        text: str,
        user_id: str,
        language: str,
        classification: Dict,
        request_id: str
    ) -> Dict:
        """
        Gérer une interaction de type Action.
        Pipeline: LLM → ActionBuilder → DRAFT → Confirmation
        
        Args:
            text: Texte de l'action
            user_id: ID utilisateur
            language: Langue
            classification: Résultat classification
            request_id: ID requête
            
        Returns:
            {"type": "action", "action_id": str, "status": "awaiting_confirmation", ...}
        """
        self.logger.info(f"Handling action: '{text}'", extra={"request_id": request_id})
        
        try:
            # 1. Analyse linguistique par LLM with graceful degradation
            if self.llm_client:
                try:
                    llm_analysis = await self.llm_client.analyze_intent(
                        user_input=text,
                        language=language
                    )
                except Exception as e:
                    # 🔥 GRACEFUL DEGRADATION: LLM intent analysis failed
                    self.logger.error(f"LLM analysis failed: {e}, converting to conversation with fallback")
                    
                    # Convert to conversation with fallback message
                    fallback_messages = {
                        "en": "I'm having trouble understanding right now. Could you please try again?",
                        "fr": "J'ai du mal à comprendre en ce moment. Pouvez-vous réessayer ?",
                        "ar": "أواجه صعوبة في الفهم الآن. هل يمكنك المحاولة مرة أخرى؟"
                    }
                    
                    return {
                        "type": "conversation",
                        "status": "llm_fallback",
                        "response": fallback_messages.get(language, fallback_messages["en"]),
                        "error": "llm_unavailable"
                    }
                
                confidence = llm_analysis.get("confidence", 0)
                intent = llm_analysis.get("primary_intent", "conversation")
                
                # Check if LLM classified as non-actionable intent
                if intent in ["conversation", "query_status"]:
                    if classification.get("type") == "action":
                        self.logger.info(
                            f"LLM reclassified as {intent}, keeping action due to classifier",
                            extra={"request_id": request_id, "classifier": classification}
                        )
                        llm_analysis["primary_intent"] = classification.get("intent", "control_iot")
                        llm_analysis["confidence"] = max(confidence, classification.get("confidence", 0.0))
                    else:
                        self.logger.info(f"LLM reclassified as {intent}, converting to conversation")
                        # Convert to conversation response
                        return await self._handle_conversation(
                            text=text,
                            user_id=user_id,
                            language=language,
                            request_id=request_id
                        )
                
                if confidence < self.classifier_threshold:
                    low_confidence_messages = {
                        "en": "I'm not sure I understood. Could you rephrase?",
                        "fr": "Je ne suis pas sûr d'avoir bien compris. Pouvez-vous reformuler ?",
                        "ar": "لست متأكدا من أنني فهمت جيدا. هل يمكنك إعادة الصياغة؟"
                    }
                    default_lang = Config.DEFAULT_LANGUAGE if Config.DEFAULT_LANGUAGE in low_confidence_messages else "en"
                    return {
                        "type": "action",
                        "status": "low_confidence",
                        "response": low_confidence_messages.get(language, low_confidence_messages[default_lang]),
                        "confidence": confidence
                    }
                
                # 1.5 Validation des entités requises
                try:
                    validation_result = self._validate_action_entities(llm_analysis, language)
                except Exception as e:
                    self.logger.error(f"Entity validation failed: {e}")
                    raise RuntimeError(f"Entity validation failed: {e}")
                    
                if not validation_result["valid"]:
                    # Entités manquantes → convertir en conversation avec demande de clarification
                    self.logger.info(f"Action incomplete, asking for clarification: {validation_result['missing_info']}")
                    
                    clarification_text = validation_result["clarification_question"]
                    
                    # Générer audio TTS pour la question
                    audio_response = None
                    if self.tts_engine:
                        try:
                            audio_response = await self.tts_engine.synthesize(clarification_text, language)
                        except Exception as e:
                            self.logger.warning(f"TTS clarification failed: {e}")
                    
                    # Auto-publish audio to MQTT
                    if audio_response and self.mqtt_client:
                        if Config.AUTO_PUBLISH_AUDIO_TO_MQTT and self.mqtt_client.is_connected():
                            try:
                                mqtt_result = self.mqtt_client.publish_audio(
                                    audio_response["audio_data"],
                                    user_id=user_id
                                )
                                self.logger.info(f"✅ Clarification audio auto-published: {mqtt_result['status']}")
                            except Exception as e:
                                self.logger.warning(f"⚠️ Auto-publish clarification failed: {e}")
                    
                    return {
                        "type": "conversation",
                        "status": "incomplete_action",
                        "response": clarification_text,
                        "audio": audio_response,
                        "missing_entities": validation_result["missing_info"]
                    }
            else:
                # Fallback : extraction basique
                llm_analysis = {
                    "intent": classification.get("intent", "control_iot"),
                    "entities": {"action": "turn_on", "device": "lamp"},
                    "confidence": 0.8
                }
            
            # 2. Construction ActionJSON
            action_json = None
            if self.action_builder:
                try:
                    action_json = await self.action_builder.build_action(
                        llm_analysis=llm_analysis,
                        user_id=user_id,
                        original_text=text,
                        language=language
                    )
                except ValidationError as e:
                    self.logger.error(f"ActionBuilder validation failed: {e}")

                    error_msg = e.message if hasattr(e, "message") else str(e)
                    audio_response = await self._synthesize_action_audio(error_msg, language, user_id)

                    return {
                        "type": "action",
                        "status": "error",
                        "error": str(e),
                        "error_code": e.code,
                        "response": error_msg,
                        "audio": audio_response,
                        "details": e.details
                    }
                except Exception as e:
                    self.logger.error(f"ActionBuilder.build_action failed: {e}")
                    raise RuntimeError(f"ActionBuilder failed: {e}")
            else:
                # Fallback : ActionJSON basique
                action_json = {
                    "action_id": f"act_{uuid.uuid4().hex[:12]}",
                    "user_id": user_id,
                    "intent": llm_analysis["intent"],
                    "entities": llm_analysis.get("entities", {}),
                    "original_text": text,
                    "language": language,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            
            action_id = action_json["action_id"]
            
            # 3. Enregistrement action en état DRAFT
            self.state_manager.create_action(
                action_id=action_id,
                action_json=action_json,
                initial_state="DRAFT"
            )
            
            self.logger.log_action_created(
                action_id=action_id,
                action_json=action_json,
                user_id=user_id
            )
            
            # 4. Transition vers PENDING_CONFIRMATION
            self.state_manager.update_state(
                action_id=action_id,
                new_state="PENDING_CONFIRMATION",
                reason="Action created and awaiting user confirmation"
            )
            
            # 5. Génération message de confirmation
            if self.confirmation_handler:
                try:
                    confirmation_text = await self.confirmation_handler.generate_confirmation(action_json)
                except Exception as e:
                    self.logger.error(f"ConfirmationHandler.generate_confirmation failed: {e}")
                    raise RuntimeError(f"ConfirmationHandler failed: {e}")
            else:
                # Fallback
                confirmation_text = f"Voulez-vous vraiment exécuter cette action : {text} ?"
            
            # 6. TTS pour audio de confirmation
            confirmation_audio = None
            if self.tts_engine:
                try:
                    confirmation_audio = await self.tts_engine.synthesize(confirmation_text, language)
                except Exception as e:
                    self.logger.warning(f"TTS confirmation failed: {e}")
            
            # 6.1 Auto-publish audio to MQTT (ESP32/Device)
            if confirmation_audio and self.mqtt_client:
                if Config.AUTO_PUBLISH_AUDIO_TO_MQTT and self.mqtt_client.is_connected():
                    try:
                        mqtt_result = self.mqtt_client.publish_audio(
                            confirmation_audio["audio_data"],
                            user_id=user_id
                        )
                        self.logger.info(f"✅ Confirmation audio auto-published to device: {mqtt_result['status']}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Auto-publish confirmation audio failed (non-blocking): {e}")
            
            self.logger.info(
                f"Action {action_id} created and awaiting confirmation",
                extra={"request_id": request_id, "action_id": action_id}
            )
            
            return {
                "type": "action",
                "action_id": action_id,
                "status": "awaiting_confirmation",
                "state": "PENDING_CONFIRMATION",
                "response": confirmation_text,
                "message": confirmation_text,
                "audio": confirmation_audio,
                "audio_response": confirmation_audio,
                "action_details": action_json
            }
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            self.logger.error(f"Error handling action: {e}\n{error_trace}", extra={"request_id": request_id})
            
            # Bilingual error message
            error_msg = "Error processing action." if language == "en" else "Erreur lors du traitement de l'action."
            audio_response = await self._synthesize_action_audio(error_msg, language, user_id)
            
            return {
                "type": "action",
                "status": "error",
                "error": str(e),
                "response": error_msg,
                "audio": audio_response,
                "error_detail": str(e)  # Include specific error for debugging
            }
    
    async def _handle_pending_confirmation(
        self,
        text: str,
        user_id: str,
        language: str,
        pending_action: Dict,
        request_id: str
    ) -> Dict:
        """
        Handle user response when an action is awaiting confirmation.
        Routes directly without NLP - preserves action context.
        
        Args:
            text: User's response text
            user_id: User ID
            language: Language code
            pending_action: The action awaiting confirmation
            request_id: Request ID
            
        Returns:
            Confirmation result dict
        """
        action_id = pending_action["action_id"]
        text_lower = text.lower().strip()

        # If STT failed or returned UI fallback text, keep action pending and ask again.
        if not text_lower or text_lower in {
            "could not transcribe",
            "impossible de transcrire",
            "تعذر التفريغ",
            "none",
            "null",
            "undefined"
        }:
            reprompt_messages = {
                "en": "I did not catch your confirmation. Please say yes to send, or no to cancel.",
                "fr": "Je n'ai pas compris votre confirmation. Dites oui pour envoyer, ou non pour annuler.",
                "ar": "لم أفهم التأكيد. قل نعم للإرسال أو لا للإلغاء."
            }
            response_text = reprompt_messages.get(language, reprompt_messages["en"])
            audio_response = await self._synthesize_action_audio(response_text, language, user_id)

            return {
                "status": "awaiting_confirmation",
                "action_id": action_id,
                "response": response_text,
                "audio": audio_response,
                "audio_response": audio_response
            }
        
        # 🔥 Detect confirmation keywords (multilingual)
        confirmation_words = [
            "yes", "oui", "ok", "okay", "confirm", "confirme", 
            "d'accord", "go", "alright", "sure", "yep", "yeah"
        ]
        cancel_words = [
            "no", "non", "cancel", "annuler", "annule", 
            "stop", "abort", "nevermind", "forget it"
        ]

        def has_keyword(text_value: str, keywords: list[str]) -> bool:
            for keyword in keywords:
                pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
                if re.search(pattern, text_value):
                    return True
            return False
        
        # Check for confirmation
        if has_keyword(text_lower, confirmation_words):
            self.logger.info(f"✅ User confirmed action {action_id}")
            return await self.confirm_action(action_id, "confirm")
        
        # Check for cancellation
        elif has_keyword(text_lower, cancel_words):
            self.logger.info(f"❌ User canceled action {action_id}")
            return await self.confirm_action(action_id, "cancel")
        
        # Ambiguous response - treat as modification/clarification
        else:
            self.logger.info(f"🔄 Ambiguous response for action {action_id}, asking confirmation again")

            reprompt_messages = {
                "en": "Please say yes to confirm sending the email, or no to cancel.",
                "fr": "Dites oui pour confirmer l'envoi de l'email, ou non pour annuler.",
                "ar": "قل نعم لتأكيد إرسال البريد، أو لا للإلغاء."
            }
            response_text = reprompt_messages.get(language, reprompt_messages["en"])
            audio_response = await self._synthesize_action_audio(response_text, language, user_id)

            return {
                "status": "awaiting_confirmation",
                "action_id": action_id,
                "response": response_text,
                "audio": audio_response,
                "audio_response": audio_response
            }

    async def _synthesize_action_audio(self, text: str, language: str, user_id: str = None):
        audio_response = None
        if self.tts_engine:
            try:
                audio_response = await self.tts_engine.synthesize(text, language)
            except Exception as e:
                self.logger.warning(f"TTS action response failed: {e}")

        if audio_response and self.mqtt_client:
            if Config.AUTO_PUBLISH_AUDIO_TO_MQTT and self.mqtt_client.is_connected():
                try:
                    mqtt_result = self.mqtt_client.publish_audio(
                        audio_response["audio_data"],
                        user_id=user_id
                    )
                    self.logger.info(f"✅ Action response audio auto-published: {mqtt_result['status']}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Auto-publish action response failed: {e}")

        return audio_response
    
    async def confirm_action(self, action_id: str, user_response: str) -> Dict:
        """
        Traiter la confirmation/annulation d'une action par l'utilisateur.
        
        Args:
            action_id: ID de l'action
            user_response: Réponse utilisateur ("oui", "non", texte de correction)
            
        Returns:
            {"status": "confirmed/canceled/correction", "response": str, ...}
        """
        self.logger.info(f"Confirming action {action_id}: '{user_response}'")
        
        try:
            # 1. Récupération de l'action
            action = self.state_manager.get_action(action_id)
            action_json = action.get("action_json", action)
            language = action_json.get("language") or action_json.get("context", {}).get("language", "fr")
            user_id = action_json.get("user_id")
            
            # 2. Analyse de la réponse
            if self.confirmation_handler:
                parse_result = self.confirmation_handler.parse_response({
                    "action_id": action_id,
                    "user_response": user_response,
                    "user_id": "unknown"  # TODO: passer user_id si disponible
                })
                # Extraire l'intent du résultat
                response_type = parse_result.get("parsed_response", {}).get("intent", "unknown")
            else:
                # Fallback : analyse basique
                user_lower = user_response.lower().strip()
                if user_lower in ["oui", "ok", "valider", "confirmer", "go", "yes"]:
                    response_type = "confirm"
                elif user_lower in ["non", "annuler", "stop", "no", "cancel"]:
                    response_type = "cancel"
                else:
                    response_type = "correction"
            
            # 3. Traitement selon le type de réponse
            if response_type == "confirm":
                # ✅ Extraire l'ActionJSON réelle de l'objet StateManager
                return await self._execute_confirmed_action(action_id, action_json)
            
            elif response_type == "cancel":
                self.state_manager.update_state(
                    action_id=action_id,
                    new_state="CANCELED",
                    reason="User canceled action"
                )
                
                self.logger.log_action_state_change(
                    action_id=action_id,
                    old_state="PENDING_CONFIRMATION",
                    new_state="CANCELED",
                    reason="User canceled"
                )
                
                cancel_messages = {
                    "en": "Action successfully cancelled",
                    "fr": "Action annulée avec succès",
                    "ar": "تم إلغاء الإجراء بنجاح"
                }
                response_text = cancel_messages.get(language, cancel_messages["en"])
                audio_response = await self._synthesize_action_audio(response_text, language, user_id)

                return {
                    "status": "canceled",
                    "action_id": action_id,
                    "response": response_text,
                    "audio": audio_response,
                    "audio_response": audio_response
                }
            
            elif response_type == "correction":
                # Retour à DRAFT pour permettre modification
                self.state_manager.update_state(
                    action_id=action_id,
                    new_state="DRAFT",
                    reason="User requested correction"
                )

                response_text = "Quelle correction souhaitez-vous apporter ?"
                audio_response = await self._synthesize_action_audio(response_text, language, user_id)

                return {
                    "status": "correction_needed",
                    "action_id": action_id,
                    "response": response_text,
                    "audio": audio_response,
                    "audio_response": audio_response,
                    "current_action": action
                }
        
        except ValueError as e:
            self.logger.error(f"Action not found: {action_id}")
            response_text = "Cette action n'existe pas ou a expiré."
            audio_response = await self._synthesize_action_audio(response_text, "fr", None)
            return {
                "status": "error",
                "error": "action_not_found",
                "response": response_text,
                "audio": audio_response,
                "audio_response": audio_response
            }
        
        except Exception as e:
            self.logger.error(f"Error confirming action: {e}")
            response_text = "Erreur lors de la confirmation."
            audio_response = await self._synthesize_action_audio(response_text, "fr", None)
            return {
                "status": "error",
                "error": str(e),
                "response": response_text,
                "audio": audio_response,
                "audio_response": audio_response
            }
        
        # Fallback (ne devrait jamais arriver)
        return {
            "status": "error",
            "error": "unknown_response_type",
            "response": "Type de réponse non reconnu."
        }
    
    async def _execute_confirmed_action(self, action_id: str, action_json: Dict) -> Dict:
        """
        Exécuter une action confirmée via n8n OU en mode démo.
        Pipeline: SecurityManager → CONFIRMED → n8n/DEMO → EXECUTING
        
        Args:
            action_id: ID de l'action
            action_json: JSON de l'action
            
        Returns:
            {"status": "executing", "action_id": str, ...}
        """
        self.logger.info(f"Executing confirmed action {action_id}")
        
        try:
            execution_language = (
                action_json.get("language")
                or action_json.get("context", {}).get("language")
                or Config.DEFAULT_LANGUAGE
            )
            execution_language = str(execution_language).lower()
            if execution_language not in {"fr", "en", "ar"}:
                execution_language = Config.DEFAULT_LANGUAGE

            # 🔥 FIX #4: DEMO MODE - Simulate execution for soutenance stability
            if Config.DEMO_MODE:
                return await self._simulate_action_execution(action_id, action_json)
            
            # REAL MODE - Continue with n8n execution
            # 1. Signature de l'action (sécurité)
            # SecurityManager.sign_action() est synchrone, pas async
            signed_action = self.security_manager.sign_action(action_json)
            
            self.logger.log_security_event(
                event="action_signed",
                user_id=action_json.get("user_id"),
                action_id=action_id,
                details={"signature": signed_action.get("signature")}
            )
            
            # 2. Mise à jour état → CONFIRMED
            self.state_manager.update_state(
                action_id=action_id,
                new_state="CONFIRMED",
                reason="User confirmed and action signed"
            )
            
            self.logger.log_action_state_change(
                action_id=action_id,
                old_state="PENDING_CONFIRMATION",
                new_state="CONFIRMED",
                reason="User confirmed"
            )

            # 3. Mise à jour état → EXECUTING avant l'appel n8n
            self.state_manager.update_state(
                action_id=action_id,
                new_state="EXECUTING",
                reason="Action dispatched to n8n"
            )
            
            # 4. Envoi vers n8n pour exécution
            n8n_response = None
            intent = action_json.get("intent", "")

            # 🔥 SPECIAL HANDLING: Reminder goes to dedicated workflow
            if intent == "set_reminder":
                n8n_response = await self._dispatch_reminder_to_n8n(action_json)
            elif self.n8n_client:
                # Other actions go to general n8n client
                action_json_signed = signed_action.get("action_json_signed", signed_action)
                n8n_response = await self.n8n_client.send_action(action_json_signed)
            else:
                self.logger.warning("n8n client not configured - action not sent")
                n8n_response = {"status": "mock", "message": "n8n not configured"}
            
            self.logger.log_action_executed(
                action_id=action_id,
                success=True,
                result={"n8n_response": n8n_response}
            )
            
            self.logger.info(f"Action {action_id} sent to n8n successfully")
            
            executing_messages = {
                "en": "Action is being executed...",
                "fr": "Action en cours d'exécution...",
                "ar": "الإجراء قيد التنفيذ..."
            }
            response_text = executing_messages.get(execution_language, executing_messages["en"])
            audio_response = await self._synthesize_action_audio(
                response_text,
                execution_language,
                action_json.get("user_id")
            )

            return {
                "status": "executing",
                "action_id": action_id,
                "state": "EXECUTING",
                "response": response_text,
                "audio": audio_response,
                "audio_response": audio_response,
                "n8n_response": n8n_response
            }
        
        except Exception as e:
            self.logger.error(f"Error executing action {action_id}: {e}")
            
            # Mise à jour état → FAILED
            self.state_manager.update_state(
                action_id=action_id,
                new_state="FAILED",
                reason=f"Execution error: {str(e)}"
            )
            
            self.logger.log_action_executed(
                action_id=action_id,
                success=False,
                result={"error": str(e)}
            )
            
            error_messages = {
                "en": "Error while executing the action.",
                "fr": "Erreur lors de l'exécution de l'action.",
                "ar": "حدث خطأ أثناء تنفيذ الإجراء."
            }
            response_text = error_messages.get(execution_language, error_messages["en"])
            audio_response = await self._synthesize_action_audio(
                response_text,
                execution_language,
                action_json.get("user_id")
            )

            return {
                "status": "failed",
                "action_id": action_id,
                "state": "FAILED",
                "error": str(e),
                "response": response_text,
                "audio": audio_response,
                "audio_response": audio_response
            }
    
    async def _simulate_action_execution(self, action_id: str, action_data: Dict) -> Dict:
        """
        🎭 DEMO MODE: Simulate action execution for soutenance reliability.
        Zero external dependencies - Perfect for demo stability.
        
        Args:
            action_id: ID de l'action
            action_data: Data from StateManager including action_json nested inside
            
        Returns:
            Simulated success response
        """
        import asyncio
        
        # Extract the actual action JSON from the StateManager wrapper
        action_json = action_data.get("action_json", {})
        intent = action_json.get("intent", "unknown")
        payload = action_json.get("payload", {})
        language = action_json.get("context", {}).get("language", "en")
        
        self.logger.info(f"🎭 DEMO MODE: Simulating execution for {intent}")
        
        # ✅ Step 1: PENDING_CONFIRMATION → CONFIRMED
        self.state_manager.update_state(
            action_id=action_id,
            new_state="CONFIRMED",
            reason="User confirmed (demo mode)"
        )
        
        self.logger.log_action_state_change(
            action_id=action_id,
            old_state="PENDING_CONFIRMATION",
            new_state="CONFIRMED",
            reason="User confirmed (demo mode)"
        )
        
        # ✅ Step 2: CONFIRMED → EXECUTING (simulate sending to n8n)
        self.state_manager.update_state(
            action_id=action_id,
            new_state="EXECUTING",
            reason="Simulated execution started (demo mode)"
        )
        
        # Simulate network/processing delay (realistic UX)
        await asyncio.sleep(0.8)
        
        date_val = payload.get('date', "aujourd'hui")

        # 🎭 Simulated responses per intent type
        demo_responses = {
            "control_iot": {
                "en": f"✅ {payload.get('device_type', 'Device')} {payload.get('action', 'controlled')} successfully!",
                "fr": f"✅ {payload.get('device_type', 'Appareil')} {payload.get('action', 'contrôlé')} avec succès !",
                "ar": f"✅ تم {payload.get('action', 'التحكم')} {payload.get('device_type', 'الجهاز')} بنجاح!"
            },
            "send_email": {
                "en": f"✅ Email sent to {payload.get('recipient', 'recipient')} successfully! Subject: {payload.get('subject', 'No subject')}",
                "fr": f"✅ Email envoyé à {payload.get('recipient', 'destinataire')} avec succès ! Sujet: {payload.get('subject', 'Pas de sujet')}",
                "ar": f"✅ تم إرسال البريد إلى {payload.get('recipient', 'المستلم')} بنجاح!"
            },
            "set_reminder": {
                "en": f"✅ Reminder '{payload.get('title', 'task')}' created for {payload.get('date', 'today')}",
                "fr": f"✅ Rappel '{payload.get('title', 'tâche')}' créé pour {date_val}",
                "ar": f"✅ تم إنشاء تذكير '{payload.get('title', 'مهمة')}'"
            },
            "web_search": {
                "en": f"✅ Search completed for '{payload.get('query', 'query')}' - Found 42 results",
                "fr": f"✅ Recherche effectuée pour '{payload.get('query', 'requête')}' - 42 résultats trouvés",
                "ar": f"✅ تم البحث عن '{payload.get('query', 'استعلام')}' - 42 نتيجة"
            },
            "open_application": {
                "en": f"✅ {payload.get('app_name', 'Application')} opened successfully!",
                "fr": f"✅ {payload.get('app_name', 'Application')} ouverte avec succès !",
                "ar": f"✅ تم فتح {payload.get('app_name', 'التطبيق')} بنجاح!"
            }
        }
        
        # Get response or fallback
        responses = demo_responses.get(intent, {
            "en": "✅ Action completed successfully!",
            "fr": "✅ Action effectuée avec succès !",
            "ar": "✅ تم تنفيذ الإجراء بنجاح!"
        })
        
        response_text = responses.get(language, responses.get("en", "✅ Action completed!"))
        
        # ✅ Step 3: EXECUTING → COMPLETED (simulate success callback from n8n)
        self.state_manager.update_state(
            action_id=action_id,
            new_state="COMPLETED",
            reason="Simulated execution successful (demo mode)"
        )
        
        self.logger.log_action_executed(
            action_id=action_id,
            success=True,
            result={
                "mode": "simulation",
                "intent": intent,
                "payload": payload,
                "simulated": True
            }
        )
        
        self.logger.info(f"🎭 DEMO MODE: Action {action_id} simulated successfully")
        
        audio_response = await self._synthesize_action_audio(
            response_text,
            language,
            action_json.get("user_id")
        )

        return {
            "status": "completed",
            "action_id": action_id,
            "state": "COMPLETED",
            "response": response_text,
            "audio": audio_response,
            "audio_response": audio_response,
            "execution_mode": "simulation",
            "simulated": True,
            "demo_mode": True
        }
    
    async def handle_execution_result(self, result_data: Dict) -> Dict:
        """
        Gérer le résultat d'exécution venant de n8n (callback webhook).
        
        Args:
            result_data: {
                "action_id": str,
                "status": "success" ou "failed",
                "result": {...},
                "error": str (si échec)
            }
            
        Returns:
            {"status": "completed/failed", "action_id": str}
        """
        action_id = result_data.get("action_id")
        execution_status = result_data.get("status")
        
        # Validation de action_id
        if not action_id:
            return {"status": "error", "error": "Missing action_id"}
        
        self.logger.info(
            f"Handling execution result for action {action_id}: {execution_status}",
            extra={"action_id": action_id, "execution_status": execution_status}
        )
        
        try:
            action = self.state_manager.get_action(action_id)
            current_state = action.get("current_state")

            if current_state in ["COMPLETED", "FAILED", "CANCELED"]:
                self.logger.warning(
                    f"Ignoring callback for action {action_id} in terminal state: {current_state}"
                )
                return {
                    "status": "ignored",
                    "action_id": action_id,
                    "reason": f"Terminal state: {current_state}"
                }

            if current_state == "CONFIRMED":
                self.state_manager.update_state(
                    action_id=action_id,
                    new_state="EXECUTING",
                    reason="Execution callback received"
                )

            if execution_status == "success":
                # Transition EXECUTING → COMPLETED
                self.state_manager.update_state(
                    action_id=action_id,
                    new_state="COMPLETED",
                    reason="Action executed successfully by n8n"
                )
                
                self.logger.log_action_state_change(
                    action_id=action_id,
                    old_state="EXECUTING",
                    new_state="COMPLETED",
                    reason="Execution completed"
                )
                
                return {
                    "status": "completed",
                    "action_id": action_id,
                    "result": result_data.get("result")
                }
            
            else:  # failed
                # Transition EXECUTING → FAILED
                self.state_manager.update_state(
                    action_id=action_id,
                    new_state="FAILED",
                    reason=f"Execution failed: {result_data.get('error', 'unknown error')}"
                )
                
                self.logger.log_action_state_change(
                    action_id=action_id,
                    old_state="EXECUTING",
                    new_state="FAILED",
                    reason="Execution failed"
                )
                
                return {
                    "status": "failed",
                    "action_id": action_id,
                    "error": result_data.get("error")
                }
        
        except Exception as e:
            self.logger.error(f"Error handling execution result: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_action_status(self, action_id: str) -> Dict:
        """
        Obtenir le statut actuel d'une action.
        
        Args:
            action_id: ID de l'action
            
        Returns:
            Action complète avec état et historique
        """
        try:
            action = self.state_manager.get_action(action_id)
            return {
                "status": "found",
                "action": action
            }
        except ValueError:
            return {
                "status": "not_found",
                "error": "Action not found"
            }
