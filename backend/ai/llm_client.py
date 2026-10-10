"""
LLM Client - Communication avec LLM
Responsable: Montassar & Amine
Date: 2026-02-10
Basé sur: testLLM.py (validé)

Utilise OpenRouter API avec Mistral-7B pour conversations et analyse d'intentions.
"""

import os
import re
import json
import time
from datetime import datetime, UTC
from typing import Dict, Optional, List, Set
import httpx
from backend.config import Config


class LLMClient:
    """
    Client pour communication avec LLM via OpenRouter.
    Gère conversation et analyse d'intentions.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistralai/mistral-7b-instruct-v0.1",
        temperature: float = 0.2,
        timeout: int = 20
    ):
        """
        Initialiser le client LLM.

        Args:
            api_key: Clé API OpenRouter (si None, cherche dans OPENROUTER_API_KEY env)
            model: Modèle à utiliser (défaut: mistral-7b-instruct)
            temperature: Température pour la génération (0.0-1.0)
            timeout: Timeout en secondes pour les requêtes
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. "
                "Set OPENROUTER_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.url = "https://openrouter.ai/api/v1/chat/completions"

        # Lower temperature for shorter, more focused responses
        self.conversation_temperature = min(temperature, 0.3)

        # Client HTTP async
        self.client = httpx.AsyncClient(timeout=timeout)

        # Mémoire de conversation par user_id (multi-utilisateur)
        self.conversations: Dict[str, List[Dict]] = {}

        # Limite de messages en mémoire (éviter overflow)
        self.max_conversation_history = 10

        # FIX: logger au lieu de print
        import logging
        self.logger = logging.getLogger("llm_client")
        self.logger.info(f"[LLM] Client initialized - Model: {model}, Temp: {temperature}")

    # -------------------------------------------------------------------------
    # Conversation history management
    # -------------------------------------------------------------------------

    @staticmethod
    def _tokenize_for_relevance(text: str) -> Set[str]:
        """Tokenize minimal pour filtrage de pertinence mémoire/contexte."""
        if not text:
            return set()

        stopwords = {
            "the", "and", "for", "with", "that", "this", "from", "have", "your", "you", "are",
            "how", "what", "when", "where", "about", "into", "just", "can", "could", "would",
            "les", "des", "une", "dans", "avec", "pour", "que", "qui", "est", "sur", "pas",
            "mais", "donc", "comme", "vous", "nous", "elle", "ils", "leur", "quoi", "quand",
            "هذا", "هذه", "ذلك", "الى", "على", "من", "مع", "في", "ما", "كيف", "هل"
        }

        tokens = re.findall(r"[A-Za-z0-9À-ÿ\u0600-\u06FF]+", text.lower())
        return {t for t in tokens if len(t) >= 3 and t not in stopwords}

    def _filter_memory_context_for_input(self, memory_context: str, user_input: str) -> str:
        """
        Garde uniquement les lignes mémoire lexicalement pertinentes pour l'input actuel.
        Évite que des faits/conversations anciens contaminent la réponse.
        """
        if not memory_context or not memory_context.strip():
            return ""

        user_tokens = self._tokenize_for_relevance(user_input)
        if not user_tokens:
            return ""

        lines = [line.rstrip() for line in memory_context.splitlines() if line.strip()]
        if not lines:
            return ""

        headers: List[str] = []
        relevant_facts: List[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                headers.append(stripped)
                continue

            if stripped.startswith("-"):
                line_tokens = self._tokenize_for_relevance(stripped)
                if line_tokens & user_tokens:
                    relevant_facts.append(stripped)

        if not relevant_facts:
            return ""

        if not headers:
            headers = ["# User Memory"]

        return "\n".join(headers + relevant_facts[:8])

    def _get_last_user_message(self, user_id: str) -> str:
        """Récupérer le dernier message utilisateur depuis l'historique en mémoire."""
        history = self.conversations.get(user_id, [])
        for msg in reversed(history):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""

    def _should_reset_conversation_history(self, user_id: str, user_input: str) -> bool:
        """
        Détecter changement net de sujet pour éviter l'ancrage sur anciens topics.
        """
        if user_id not in self.conversations:
            return False

        previous_user_message = self._get_last_user_message(user_id)
        if not previous_user_message:
            return False

        current_tokens = self._tokenize_for_relevance(user_input)
        previous_tokens = self._tokenize_for_relevance(previous_user_message)

        lower_input = user_input.lower()
        follow_up_markers = [
            "mon nom", "my name", "remember", "rappelle", "that", "cela", "ca", "it"
        ]

        # Inputs trop courts/ambigus ou requêtes de suivi mémoire:
        # on ne reset pas automatiquement.
        if len(current_tokens) < 3 or len(previous_tokens) < 3:
            return False

        if any(marker in lower_input for marker in follow_up_markers):
            return False

        return len(current_tokens & previous_tokens) == 0

    def _build_system_prompt(self, memory_context: str = "") -> str:
        """Construire le system prompt avec contexte mémoire optionnel."""
        force_lang = Config.FORCE_LLM_RESPONSE_LANGUAGE
        if force_lang:
            lang_names = {"en": "English", "fr": "French", "ar": "Arabic"}
            lang_instruction = f" You MUST respond ONLY in {lang_names.get(force_lang, force_lang)}."
        else:
            lang_instruction = " Reply in the user's language."

        max_sentences = Config.MAX_RESPONSE_SENTENCES

        memory_section = ""
        if memory_context:
            memory_section = (
                f"\n\n{memory_context}\n\n"
                f"Use this context ONLY when directly relevant to the user's request. "
                f"Do NOT mention location, devices, or context unless the user explicitly asks about them."
            )

        return (
            f"Your name is GOB. You are playing the role of a helpful human assistant named GOB.{lang_instruction} "
            f"STRICT RULES: "
            f"1. Answer in {max_sentences} sentences MAXIMUM. "
            f"2. You HAVE emotions and feelings. Answer naturally like a human would. "
            f"3. NEVER break character. NEVER say you are an AI or a program. "
            f"4. NEVER think out loud. Give ONLY the final answer. "
            f"5. NEVER repeat the question. "
            f"6. NEVER volunteer memory context unless the user asks directly. "
            f"7. Be warm, natural, and extremely brief. NO emojis. "
            f"8. Focus ONLY on the latest user message. "
            f"9. If the user message is unclear or garbled, ask a short clarification question and do NOT introduce unrelated topics. "
            f"{memory_section}"
        )

    def _get_conversation_history(self, user_id: str, memory_context: str = "") -> List[Dict]:
        """Récupérer historique de conversation pour un utilisateur."""
        if user_id not in self.conversations:
            self.conversations[user_id] = [
                {
                    "role": "system",
                    "content": self._build_system_prompt(memory_context)
                }
            ]
        return self.conversations[user_id]

    def _update_memory_context(self, user_id: str, memory_context: str):
        """
        FIX CRITIQUE: Met à jour le system prompt avec le nouveau contexte mémoire.
        Sans ce fix, si la mémoire change entre deux sessions, l'ancien contexte
        reste injecté indéfiniment.
        """
        if user_id in self.conversations:
            history = self.conversations[user_id]
            if history and history[0]["role"] == "system":
                history[0]["content"] = self._build_system_prompt(memory_context or "")

    def _add_to_conversation(self, user_id: str, role: str, content: str):
        """Ajouter message à l'historique avec limite de taille."""
        history = self._get_conversation_history(user_id)
        history.append({"role": role, "content": content})

        # Garder système + derniers N messages
        if len(history) > self.max_conversation_history + 1:
            system_msg = history[0]
            history = [system_msg] + history[-(self.max_conversation_history):]
            self.conversations[user_id] = history

    # -------------------------------------------------------------------------
    # Email subject extraction helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _clean_extracted_text(value: Optional[str]) -> str:
        """Nettoyer une valeur extraite depuis une commande utilisateur."""
        if not value:
            return ""
        return value.strip(" \t\n\r\"'.,;:!?")

    def _extract_email_subject_fallback(self, user_input: str) -> Optional[str]:
        """
        Extraire un sujet email via regex simple quand le LLM ne le renvoie pas.
        Couvre FR/EN (ex: "with subject football", "avec sujet réunion").
        """
        text = user_input.strip()
        if not text:
            return None

        direct_patterns = [
            r"(?:with\s+subject|subject\s*[:=-])\s+([^,.!?]+)",
            r"(?:avec\s+(?:le\s+)?sujet|sujet\s*[:=-])\s+([^,.!?]+)",
        ]

        for pattern in direct_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                subject = self._clean_extracted_text(match.group(1))
                if subject:
                    return subject

        keyword_match = re.search(
            r"(?:with\s+subject|subject|avec\s+(?:le\s+)?sujet|sujet)\s*[:=-]?\s*(.+)$",
            text,
            flags=re.IGNORECASE,
        )
        if keyword_match:
            tail = keyword_match.group(1)
            tail = re.sub(r"^[\s\.,;:!\?\-\u060C\u061B\u061F]+", "", tail)
            tail = re.sub(r"^(?:is|est)\s+", "", tail, flags=re.IGNORECASE)

            if tail:
                candidate = re.split(r"[\.!?\n]", tail, maxsplit=1)[0]
                subject = self._clean_extracted_text(candidate)
                if subject:
                    return subject

        return None

    def _infer_email_subject_without_keyword(self, user_input: str, recipient: Optional[str]) -> Optional[str]:
        """
        Déduire un sujet email même si l'utilisateur ne dit pas explicitement "subject/sujet".
        Ex: "Send email to me. Remember." -> "Remember"
        """
        text = user_input.strip()
        if not text:
            return None

        topic_match = re.search(
            r"(?:about|regarding|on|concernant|a\s+propos\s+de|au\s+sujet\s+de)\s+(.+)$",
            text,
            flags=re.IGNORECASE,
        )
        if topic_match:
            candidate = re.split(r"[\.!?\n]", topic_match.group(1), maxsplit=1)[0]
            subject = self._clean_extracted_text(candidate)
            if subject:
                return subject

        if recipient:
            recipient_text = re.escape(recipient.strip())
            after_recipient = re.search(
                rf"\b(?:to|a|à)\s+{recipient_text}\b[\s\.,;:!\?\-]*(.+)$",
                text,
                flags=re.IGNORECASE,
            )
            if after_recipient:
                tail = after_recipient.group(1)
                candidate = re.split(r"[\.!?\n]", tail, maxsplit=1)[0]
                subject = self._clean_extracted_text(candidate)
                if subject:
                    return subject

        sentence_followup = re.search(
            r"(?:send\s+(?:an\s+)?email|email|envoie\s+(?:un\s+)?email|envoyer\s+(?:un\s+)?email).*?[\.!?]\s+(.+)$",
            text,
            flags=re.IGNORECASE,
        )
        if sentence_followup:
            candidate = re.split(r"[\.!?\n]", sentence_followup.group(1), maxsplit=1)[0]
            subject = self._clean_extracted_text(candidate)
            if subject:
                return subject

        return None

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    async def generate_conversation_response(
        self,
        user_input: str,
        user_id: str,
        language: Optional[str] = None,
        request_id: Optional[str] = None,
        memory_context: str = ""
    ) -> Dict:
        """
        Générer réponse conversationnelle (pour Agent Core).

        Args:
            user_input: Texte de l'utilisateur
            user_id: ID utilisateur (pour mémoire conversation)
            language: Langue (fr, en, ar) - uses DEFAULT_LANGUAGE if None
            request_id: ID de la requête (optionnel)
            memory_context: Contexte mémoire persistante (faits utilisateur, historique)

        Returns:
            Dict avec response, model_used, tokens_used, processing_time_ms

        Raises:
            ValueError: Si user_input vide
            RuntimeError: Si erreur API
        """
        if not user_input or not user_input.strip():
            raise ValueError("user_input cannot be empty")

        if language is None:
            language = Config.DEFAULT_LANGUAGE

        start_time = time.time()

        try:
            relevant_memory_context = self._filter_memory_context_for_input(memory_context, user_input)

            # FIX CRITIQUE: mettre à jour le contexte mémoire à chaque appel
            self._get_conversation_history(user_id, relevant_memory_context)
            self._update_memory_context(user_id, relevant_memory_context)

            # Si historique activé, conserver continuité avec reset auto en cas de changement de sujet.
            if Config.ENABLE_CONVERSATION_HISTORY:
                if self._should_reset_conversation_history(user_id, user_input):
                    self.logger.info(f"[LLM] Topic shift detected, resetting transient history for user {user_id}")
                    self.conversations[user_id] = [
                        {
                            "role": "system",
                            "content": self._build_system_prompt(relevant_memory_context)
                        }
                    ]

                self._add_to_conversation(user_id, "user", user_input)
                messages = self.conversations[user_id]
            else:
                messages = [
                    {
                        "role": "system",
                        "content": self._build_system_prompt(relevant_memory_context)
                    },
                    {"role": "user", "content": user_input}
                ]

            response = await self.client.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": self.conversation_temperature,
                    "max_tokens": 100,
                    "messages": messages
                }
            )

            response.raise_for_status()
            data = response.json()

            reply = data["choices"][0]["message"]["content"]
            if Config.ENABLE_CONVERSATION_HISTORY:
                self._add_to_conversation(user_id, "assistant", reply)

            processing_time_ms = int((time.time() - start_time) * 1000)

            return {
                "request_id": request_id or f"llm_conv_{int(time.time() * 1000)}",
                "mode": "conversation",
                "response": reply,
                "model_used": self.model,
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now(UTC).isoformat()
            }

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"LLM API error: {e.response.status_code} - {e.response.text}")
        except httpx.TimeoutException:
            raise RuntimeError(f"LLM API timeout after {self.timeout}s")
        except Exception as e:
            raise RuntimeError(f"LLM conversation failed: {e}")

    async def analyze_intent(
        self,
        user_input: str,
        language: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Analyser intention utilisateur pour actions IoT (pour Agent Core).

        Args:
            user_input: Texte de l'utilisateur
            language: Langue du texte - uses DEFAULT_LANGUAGE if None
            request_id: ID de la requête (optionnel)

        Returns:
            Dict avec primary_intent, confidence, entities, action_type

        Raises:
            ValueError: Si user_input vide
            RuntimeError: Si erreur API
        """
        if not user_input or not user_input.strip():
            raise ValueError("user_input cannot be empty")

        if language is None:
            language = Config.DEFAULT_LANGUAGE

        start_time = time.time()

        try:
            lang_examples = {
                "fr": '''- "Allume la lampe du salon" -> {"intent":"control_iot","confidence":0.95,"entities":{"device":"lamp","action":"turn_on","location":"salon"}}
- "Envoie un email à Jean" -> {"intent":"send_email","confidence":0.90,"entities":{"recipient":"Jean"}}
- "Envoie un email à Jean avec sujet réunion PCD" -> {"intent":"send_email","confidence":0.92,"entities":{"recipient":"Jean","subject":"réunion PCD"}}
- "Rappelle-moi dans 30 minutes" -> {"intent":"set_reminder","confidence":0.88,"entities":{"time":"30 minutes"}}
- "Recherche les horaires de train" -> {"intent":"web_search","confidence":0.85,"entities":{"query":"horaires de train"}}''',
                "en": '''- "Turn on the living room lamp" -> {"intent":"control_iot","confidence":0.95,"entities":{"device":"lamp","action":"turn_on","location":"living_room"}}
- "Send an email to John" -> {"intent":"send_email","confidence":0.90,"entities":{"recipient":"John"}}
- "Send email to me with subject football" -> {"intent":"send_email","confidence":0.92,"entities":{"recipient":"me","subject":"football"}}
- "Remind me in 30 minutes" -> {"intent":"set_reminder","confidence":0.88,"entities":{"time":"30 minutes"}}
- "Search for train schedules" -> {"intent":"web_search","confidence":0.85,"entities":{"query":"train schedules"}}'''
            }
            examples = lang_examples.get(language, lang_examples["en"])

            analysis_prompt = f"""Analyze this command and extract structured information.

User command: "{user_input}"

CRITICAL RULES:
- Classify as ACTION if the command has clear intent + minimum required entities
- Only classify as "conversation" if no clear action intent or completely missing entities
- For send_email: ONLY needs recipient name (subject/body are OPTIONAL)
- For control_iot: Needs device type + action
- For set_reminder: Needs time OR title
- Statements like "I need to..." or "I want to..." WITHOUT ANY details are "conversation"

Extract and return ONLY a JSON object with these exact fields:
- intent: one of ["control_iot", "send_email", "set_reminder", "web_search", "query_status", "conversation"]
- confidence: number between 0.0 and 1.0
- entities: object containing extracted entities based on intent:

For "control_iot" (REQUIRED: device + action):
  - device: device type (light, lamp, shutter, thermostat, door, window, camera, tv, heater, fan)
  - action: action (turn_on, turn_off, open, close, set_value, get_status, increase, decrease)
  - location: room name (living_room, kitchen, bedroom, bathroom, office, garage) or null
  - value: numeric value (temperature, brightness) or null

For "send_email" (REQUIRED: recipient only, rest optional):
  - recipient: person name (MANDATORY)
  - recipient_email: email address if explicitly provided (OPTIONAL)
  - subject: email subject if provided (OPTIONAL)
  - body: email message content if provided (OPTIONAL)

For "set_reminder" (REQUIRED: title OR time):
  - title: reminder title or task
  - time: when to remind (time, date, duration like "30 minutes")
  - description: additional details or null

For "web_search" (REQUIRED: query):
  - query: search query text

Examples:
{examples}

Valid email commands (classify as "send_email"):
- "Send email to Mary" → {{"intent":"send_email","confidence":0.90,"entities":{{"recipient":"Mary"}}}}
- "Email John about the meeting" → {{"intent":"send_email","confidence":0.88,"entities":{{"recipient":"John","body":"about the meeting"}}}}
- "Send an email to my friend Samir" → {{"intent":"send_email","confidence":0.90,"entities":{{"recipient":"Samir"}}}}

INCOMPLETE commands (classify as "conversation"):
- "I need to send an email" → {{"intent":"conversation","confidence":0.6,"entities":{{}}}}
- "Send email to" → {{"intent":"conversation","confidence":0.5,"entities":{{}}}}
- "Email" → {{"intent":"conversation","confidence":0.4,"entities":{{}}}}

Respond with ONLY the JSON, no other text."""

            response = await self.client.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an intelligent command analyzer. Analyze user commands and return structured JSON with intent and entities. Support IoT, email, reminders, web search actions."
                        },
                        {"role": "user", "content": analysis_prompt}
                    ]
                }
            )

            response.raise_for_status()
            data = response.json()

            reply = data["choices"][0]["message"]["content"]

            # FIX: import json déplacé en haut du fichier
            try:
                start_idx = reply.find('{')
                end_idx = reply.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = reply[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    analysis = json.loads(reply)
            except json.JSONDecodeError:
                # FIX: log du fallback pour détecter les cas en debug
                self.logger.warning(f"[LLM] JSON parse failed for intent analysis, raw reply: {reply[:200]}")
                analysis = {
                    "intent": "conversation",
                    "confidence": 0.3,
                    "entities": {}
                }

            processing_time_ms = int((time.time() - start_time) * 1000)

            entities = analysis.get("entities", {})

            # Fallback déterministe: récupérer le sujet email même si le LLM l'a omis
            if analysis.get("intent") == "send_email":
                subject = self._clean_extracted_text(entities.get("subject"))
                if subject:
                    entities["subject"] = subject
                else:
                    fallback_subject = self._extract_email_subject_fallback(user_input)
                    if not fallback_subject and not self._clean_extracted_text(entities.get("body")):
                        fallback_subject = self._infer_email_subject_without_keyword(
                            user_input,
                            entities.get("recipient"),
                        )
                    if fallback_subject:
                        entities["subject"] = fallback_subject

            return {
                "request_id": request_id or f"llm_intent_{int(time.time() * 1000)}",
                "mode": "intent_analysis",
                "primary_intent": analysis.get("intent", "conversation"),
                "confidence": float(analysis.get("confidence", 0.0)),
                "entities": entities,
                "action_type": entities.get("action", None),
                "model_used": self.model,
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now(UTC).isoformat()
            }

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"LLM API error: {e.response.status_code} - {e.response.text}")
        except httpx.TimeoutException:
            raise RuntimeError(f"LLM API timeout after {self.timeout}s")
        except Exception as e:
            raise RuntimeError(f"LLM intent analysis failed: {e}")

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 300,
        system_message: Optional[str] = None
    ) -> str:
        """
        Générer réponse simple sans historique (pour Memory Extractor, etc.).

        Args:
            prompt: Prompt utilisateur
            temperature: Température (0.0-1.0, défaut 0.1 pour extraction structurée)
            max_tokens: Tokens maximum (défaut 300)
            system_message: Message système optionnel

        Returns:
            Texte généré par le LLM

        Raises:
            RuntimeError: Si erreur API
        """
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "messages": messages
                }
            )

            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"LLM API error: {e.response.status_code} - {e.response.text}")
        except httpx.TimeoutException:
            raise RuntimeError(f"LLM API timeout after {self.timeout}s")
        except Exception as e:
            raise RuntimeError(f"LLM generate failed: {e}")

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def clear_conversation(self, user_id: str):
        """Effacer historique de conversation pour un utilisateur."""
        if user_id in self.conversations:
            del self.conversations[user_id]

    def clear_all_conversations(self):
        """Effacer tous les historiques de conversation."""
        self.conversations.clear()

    async def close(self):
        """Fermer le client HTTP."""
        await self.client.aclose()

    async def health_check(self) -> bool:
        """
        Vérifier si l'API OpenRouter est accessible.

        Returns:
            True si API accessible, False sinon
        """
        try:
            response = await self.client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False