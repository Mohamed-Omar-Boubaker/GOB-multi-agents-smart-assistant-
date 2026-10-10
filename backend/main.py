"""
Point d'entrée principal - API FastAPI
Responsable: Montassar (Lead Backend)

Rôle:
- Initialiser l'application FastAPI
- Définir les routes API REST
- Gérer le cycle de vie du serveur
- Coordonner Agent Core avec tous les composants

Routes implémentées:
- POST /command/text : Commande textuelle
- POST /command/audio : Commande vocale
- POST /action/confirm/{action_id} : Confirmation action
- GET /action/status/{action_id} : Status action
- POST /callback/n8n : Callback résultat n8n
- GET /health : Health check système
- GET /stats : Statistiques système
"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import uvicorn
import logging

# Imports des composants backend
from backend.config import Config
from backend.agent.agent_core import AgentCore
from backend.ai.stt_engine import STTEngine
from backend.ai.tts_engine import TTSEngine
from backend.ai.llm_client import LLMClient
from backend.classifier.intent_classifier import IntentClassifier
from backend.actions.action_builder import ActionBuilder
from backend.actions.confirmation_handler import ConfirmationHandler
from backend.agent.state_manager import StateManager
from backend.agent.security_manager import SecurityManager
from backend.agent.logger import Logger
from backend.services.memory_service import MemoryService  # 🔥 NEW: Persistent memory
from backend.utils.contact_manager import contact_manager
from backend.utils.device_manager import device_manager

# Import validation framework (utilisé par tous les modules)
from backend.utils.validators import JSONValidator
from backend.utils.exceptions import ValidationError

# Initialisation optionnelle des intégrations
try:
    from backend.integrations.n8n_client import N8NClient
    n8n_available = True
except ImportError:
    n8n_available = False
    N8NClient = None

try:
    from backend.integrations.mqtt_client import MQTTClient
    mqtt_available = True
except ImportError:
    mqtt_available = False
    MQTTClient = None

# ============================================================
# MODÈLES PYDANTIC (VALIDATION INPUT/OUTPUT)
# ============================================================

class TextCommandRequest(BaseModel):
    """Requête pour commande textuelle."""
    text: str = Field(..., max_length=Config.MAX_TEXT_LENGTH, description="Texte de la commande")
    user_id: str = Field(..., description="Identifiant utilisateur")
    language: str = Field(default=Config.DEFAULT_LANGUAGE, description="Langue de la commande (fr/en)")
    source: Optional[str] = Field(default="api", description="Source de la commande")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Allume la lampe du salon",
                "user_id": "user_001",
                "language": "fr",
                "source": "mobile_app"
            }
        }


class AudioCommandRequest(BaseModel):
    """Requête pour commande vocale."""
    audio_data: str = Field(..., description="Audio encodé en base64")
    audio_format: str = Field(default="wav", description="Format audio (wav/mp3/ogg)")
    user_id: str = Field(..., description="Identifiant utilisateur")
    language: str = Field(default=Config.DEFAULT_LANGUAGE, description="Langue de la commande")
    source: Optional[str] = Field(default="esp32", description="Source de la commande")
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_data": "UklGRiQAAABXQVZFZm10...",
                "audio_format": "wav",
                "user_id": "user_001",
                "language": "fr",
                "source": "esp32"
            }
        }


class ConfirmActionRequest(BaseModel):
    """Requête pour confirmer une action."""
    response: str = Field(..., description="Réponse utilisateur (oui/non/modifier)")
    user_id: str = Field(..., description="Identifiant utilisateur")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "oui",
                "user_id": "user_001"
            }
        }


class N8NCallbackRequest(BaseModel):
    """Requête de callback depuis n8n."""
    action_id: str = Field(..., description="ID de l'action")
    status: str = Field(..., description="Status d'exécution (success/failed)")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Résultat d'exécution")
    error: Optional[str] = Field(default=None, description="Message d'erreur si échec")
    execution_time_ms: Optional[int] = Field(default=None, description="Temps d'exécution")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_id": "act_abc123xyz",
                "status": "success",
                "result": {"device_status": "on", "power": 100},
                "execution_time_ms": 1234
            }
        }


class RobotStateRequest(BaseModel):
    """Requete relay UX -> MQTT pour animation robot (Phase 2)."""
    request_id: Optional[str] = Field(default=None, description="ID de requete")
    user_id: str = Field(..., description="Identifiant utilisateur")
    state: str = Field(..., description="Etat robot cible")
    lang: str = Field(default=Config.DEFAULT_LANGUAGE, description="Langue utilisateur")
    source: str = Field(default="agent_ui", description="Source de l'evenement")
    ts: Optional[int] = Field(default=None, description="Timestamp Unix secondes")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_abc123",
                "user_id": "web_user_001",
                "state": "listening",
                "lang": "fr",
                "source": "agent_ui",
                "ts": 1711112000
            }
        }


class DeviceItem(BaseModel):
    device_type: str = Field(..., description="Type de device (light, shutter, etc.)")
    location: str = Field(..., description="Nom de la location (libre)")
    device_id: str = Field(..., description="Identifiant device")


class DeviceAliasItem(BaseModel):
    alias: str = Field(..., description="Alias libre (ex: salon2, myroom)")
    location: str = Field(..., description="Location cible")


class ContactItem(BaseModel):
    name: str = Field(..., description="Nom complet")
    email: str = Field(..., description="Email")
    phone: Optional[str] = Field(default="", description="Téléphone")
    tags: List[str] = Field(default_factory=list, description="Tags")


class ContactUpdateItem(BaseModel):
    name: Optional[str] = Field(default=None, description="Nom complet")
    email: Optional[str] = Field(default=None, description="Email")
    phone: Optional[str] = Field(default=None, description="Téléphone")
    tags: Optional[List[str]] = Field(default=None, description="Tags")


class ContactAliasItem(BaseModel):
    alias: str = Field(..., description="Alias libre")
    contact_name: str = Field(..., description="Contact cible (nom)")


# ============================================================
# INITIALISATION APPLICATION FASTAPI
# ============================================================

app = FastAPI(
    title="PCD - Agent Intelligent Embarqué API",
    description="Backend Python orchestrateur pour agent vocal intelligent avec classification Conversation/Action",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=Config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger système
logger = Logger(log_file=Config.LOG_FILE)

# Variables globales pour Agent Core (initialisées au startup)
agent_core: Optional[AgentCore] = None


# ============================================================
# ÉVÉNEMENTS LIFECYCLE
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage du serveur."""
    global agent_core
    
    logger.info("=" * 60)
    logger.info("🚀 DÉMARRAGE BACKEND PYTHON - AGENT INTELLIGENT")
    logger.info("=" * 60)
    logger.info(f"Environment: {Config.ENVIRONMENT}")
    logger.info(f"Host: {Config.HOST}:{Config.PORT}")
    logger.info(f"LLM: {Config.LLM_API_URL}")
    logger.info(f"STT Engine: {Config.STT_ENGINE}")
    logger.info(f"TTS Engine: {Config.TTS_ENGINE}")
    logger.info(f"Classifier: {Config.CLASSIFIER_METHOD}")
    
    # Initialisation des composants
    try:
        logger.info("Initialisation des composants...")
        
        # Composants critiques (toujours requis)
        stt_engine = STTEngine() if Config.ENABLE_AUDIO_PROCESSING else None
        tts_engine = TTSEngine() if Config.ENABLE_AUDIO_PROCESSING else None
        llm_client = LLMClient()
        classifier_llm = llm_client if Config.CLASSIFIER_USE_LLM_FALLBACK else None
        classifier = IntentClassifier(
            method=Config.CLASSIFIER_METHOD,
            llm_client=classifier_llm,
            threshold=Config.CLASSIFIER_THRESHOLD
        )
        action_builder = ActionBuilder()
        confirmation_handler = ConfirmationHandler()
        state_manager = StateManager()
        security_manager = SecurityManager()
        memory_service = MemoryService(db_path="data/agent_memory.db")  # 🔥 NEW: Persistent memory
        
        logger.info("✅ Composants critiques initialisés")
        
        # Composants optionnels (selon configuration)
        n8n_client = None
        if Config.ENABLE_N8N_INTEGRATION and n8n_available and N8NClient is not None:
            try:
                n8n_client = N8NClient()
                logger.info("✅ n8n Client initialisé")
            except Exception as e:
                logger.warning(f"⚠️  n8n Client non disponible: {e}")
        
        mqtt_client = None
        if Config.ENABLE_MQTT_INTEGRATION and mqtt_available and MQTTClient is not None:
            try:
                mqtt_client = MQTTClient()
                logger.info("✅ MQTT Client initialisé")
            except Exception as e:
                logger.warning(f"⚠️  MQTT Client non disponible: {e}")
        
        # Initialisation Agent Core avec tous les composants
        agent_core = AgentCore(
            stt_engine=stt_engine,
            tts_engine=tts_engine,
            llm_client=llm_client,
            classifier=classifier,
            action_builder=action_builder,
            confirmation_handler=confirmation_handler,
            n8n_client=n8n_client,
            mqtt_client=mqtt_client,
            security_manager=security_manager,
            memory_service=memory_service  # 🔥 NEW: Persistent memory
        )
        
        logger.info("=" * 60)
        logger.info("✅ AGENT CORE INITIALISÉ ET PRÊT")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage à l'arrêt du serveur."""
    logger.info("=" * 60)
    logger.info("🛑 ARRÊT BACKEND PYTHON")
    logger.info("=" * 60)
    
    # Cleanup des ressources si nécessaire
    if agent_core:
        # TODO: Fermer connexions MQTT, bases de données, etc.
        pass
    
    logger.info("✅ Arrêt propre terminé")


# ============================================================
# GESTIONNAIRE D'EXCEPTIONS
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Gestionnaire global des exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================
# ROUTES API - COMMANDES
# ============================================================

@app.post("/command/text", 
          summary="Traiter commande textuelle",
          response_description="Résultat du traitement (conversation ou action)",
          tags=["Commandes"])
async def process_text_command(request: TextCommandRequest):
    """
    Traite une commande utilisateur textuelle.
    
    ** Pipeline:**
    1. Classification Conversation/Action
    2. Si Conversation: LLM → TTS → Réponse immédiate
    3. Si Action: LLM → ActionBuilder → DRAFT → Confirmation
    
    **Retourne:**
    - Conversation: Réponse textuelle + audio
    - Action: action_id + message de confirmation
    """
    if not agent_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Core not initialized"
        )
    
    logger.info(f"📝 Text command from user {request.user_id}: '{request.text}'")
    
    try:
        result = await agent_core.process({
            "command_type": "text",
            "text": request.text,
            "user_id": request.user_id,
            "language": request.language,
            "source": request.source
        })
        
        logger.info(f"✅ Command processed successfully: {result.get('classification')}")
        return result
    
    except Exception as e:
        logger.error(f"❌ Error processing text command: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/command/audio",
          summary="Traiter commande vocale",
          response_description="Résultat du traitement avec transcription",
          tags=["Commandes"])
async def process_audio_command(request: AudioCommandRequest):
    """
    Traite une commande utilisateur vocale.
    
    **Pipeline:**
    1. STT (Speech-to-Text): Audio → Texte
    2. Classification Conversation/Action
    3. Suite identique à /command/text
    
    **Retourne:**
    - transcription: Texte reconnu
    - + même structure que /command/text
    """
    if not agent_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Core not initialized"
        )
    
    if not Config.ENABLE_AUDIO_PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Audio processing is disabled"
        )
    
    logger.info(f"🎤 Audio command from user {request.user_id} ({request.audio_format})")
    
    try:
        result = await agent_core.process({
            "command_type": "audio",
            "audio_data": request.audio_data,
            "audio_format": request.audio_format,
            "user_id": request.user_id,
            "language": request.language,
            "source": request.source
        })
        
        logger.info(f"✅ Audio processed: transcription='{result.get('transcription')}'")
        return result
    
    except Exception as e:
        logger.error(f"❌ Error processing audio command: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================
# ROUTES API - ACTIONS
# ============================================================

@app.post("/action/confirm/{action_id}",
          summary="Confirmer ou annuler une action",
          response_description="Résultat de la confirmation",
          tags=["Actions"])
async def confirm_action(action_id: str, request: ConfirmActionRequest):
    """
    Traite la réponse utilisateur pour confirmer/annuler une action.
    
    **Réponses acceptées:**
    - "oui", "ok", "valider" → CONFIRMED → Envoi vers n8n
    - "non", "annuler" → CANCELED
    - "modifier", "changer" → Retour DRAFT
    
    **Pipeline CONFIRMED:**
    1. SecurityManager: Signature HMAC
    2. StateManager: DRAFT → CONFIRMED → EXECUTING
    3. n8n Client: Envoi ActionJSON signé
    4. Retour: status "executing"
    """
    if not agent_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Core not initialized"
        )
    
    logger.info(f"✅ Confirmation request for action {action_id}: '{request.response}'")
    
    try:
        result = await agent_core.confirm_action(
            action_id=action_id,
            user_response=request.response
        )
        
        logger.info(f"✅ Action {action_id} confirmation result: {result.get('status')}")
        return result
    
    except ValueError as e:
        logger.error(f"❌ Action {action_id} not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Error confirming action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/action/status/{action_id}",
         summary="Obtenir le statut d'une action",
         response_description="État actuel et historique",
         tags=["Actions"])
async def get_action_status(action_id: str):
    """
    Récupère le statut actuel et l'historique d'une action.
    
    **États possibles:**
    - DRAFT: En cours de création
    - PENDING_CONFIRMATION: En attente de confirmation
    - CONFIRMED: Confirmée par utilisateur
    - EXECUTING: En cours d'exécution par n8n
    - COMPLETED: Exécutée avec succès
    - CANCELED: Annulée par utilisateur
    - FAILED: Échec d'exécution
    
    **Retourne:**
    - action_id
    - current_state
    - state_history (transitions)
    - action_json complet
    """
    if not agent_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Core not initialized"
        )
    
    logger.info(f"📊 Status request for action {action_id}")
    
    try:
        result = agent_core.get_action_status(action_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found"
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting action status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/actions/{user_id}",
         summary="Lister les actions d'un utilisateur",
         response_description="Liste des actions avec leur état",
         tags=["Actions"])
async def get_user_actions(user_id: str, limit: int = 20):
    """
    Récupère toutes les actions d'un utilisateur, triées par date (plus récentes d'abord).
    
    **Paramètres:**
    - user_id: ID de l'utilisateur
    - limit: Nombre max d'actions à retourner (défaut: 20)
    
    **Retourne:**
    - user_id
    - total_actions: Nombre total d'actions
    - actions: Liste des actions avec leur état actuel
    """
    if not agent_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Core not initialized"
        )
    
    logger.info(f"📋 Listing actions for user {user_id}")
    
    try:
        # Récupérer toutes les actions de l'utilisateur
        actions = agent_core.state_manager.get_user_actions(user_id)
        
        # Trier par date (plus récente d'abord)
        actions.sort(key=lambda x: x["action_json"].get("timestamp", ""), reverse=True)
        
        # Limiter le nombre de résultats
        actions = actions[:limit]
        
        # Enrichir avec l'état actuel
        enriched_actions = []
        for action in actions:
            action_id = action["action_id"]
            enriched_actions.append({
                "action_id": action_id,
                "current_state": action["current_state"],
                "intent": action["action_json"].get("intent"),
                "original_text": action["action_json"].get("original_text"),
                "timestamp": action["action_json"].get("timestamp"),
                "entities": action["action_json"].get("entities", {}),
                "language": action["action_json"].get("language", "en")
            })
        
        return {
            "user_id": user_id,
            "total_actions": len(enriched_actions),
            "actions": enriched_actions
        }
    
    except Exception as e:
        logger.error(f"❌ Error listing user actions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================
# ROUTES API - CONFIGURATION DEVICES & CONTACTS
# ============================================================

@app.get("/config/devices",
         summary="Lister les devices configurés",
         response_description="Mapping devices et aliases",
         tags=["Config"])
async def get_devices_config():
    return {
        "device_mapping": device_manager.device_mapping,
        "aliases": device_manager.aliases
    }


@app.post("/config/devices",
          summary="Ajouter ou mettre à jour un device",
          response_description="Device enregistré",
          tags=["Config"])
async def upsert_device(item: DeviceItem):
    device_manager.set_device(item.device_type, item.location, item.device_id)
    return {
        "status": "ok",
        "device": {
            "device_type": item.device_type,
            "location": item.location,
            "device_id": item.device_id
        }
    }


@app.delete("/config/devices/{device_type}/{location}",
            summary="Supprimer un device",
            response_description="Statut suppression",
            tags=["Config"])
async def delete_device(device_type: str, location: str):
    try:
        device_manager.delete_device(device_type, location)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.post("/config/device-aliases",
          summary="Ajouter un alias de location",
          response_description="Alias ajouté",
          tags=["Config"])
async def add_device_alias(item: DeviceAliasItem):
    device_manager.add_alias(item.alias, item.location)
    return {"status": "ok", "alias": item.alias, "location": item.location}


@app.delete("/config/device-aliases/{alias}",
            summary="Supprimer un alias de location",
            response_description="Alias supprimé",
            tags=["Config"])
async def delete_device_alias(alias: str):
    try:
        device_manager.delete_alias(alias)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.get("/config/contacts",
         summary="Lister les contacts configurés",
         response_description="Contacts et aliases",
         tags=["Config"])
async def get_contacts_config():
    return {
        "contacts": contact_manager.contacts,
        "aliases": contact_manager.aliases
    }


@app.post("/config/contacts",
          summary="Ajouter un contact",
          response_description="Contact ajouté",
          tags=["Config"])
async def add_contact(item: ContactItem):
    contact_manager.add_contact(
        name=item.name,
        email=item.email,
        phone=item.phone,
        tags=item.tags
    )
    return {"status": "ok", "contact_name": item.name}


@app.put("/config/contacts/{contact_name}",
         summary="Mettre à jour un contact",
         response_description="Contact mis à jour",
         tags=["Config"])
async def update_contact(contact_name: str, item: ContactUpdateItem):
    try:
        contact_manager.update_contact(
            name_key=contact_name,
            name=item.name,
            email=item.email,
            phone=item.phone,
            tags=item.tags
        )
        return {"status": "ok", "contact_name": contact_name}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.delete("/config/contacts/{contact_name}",
            summary="Supprimer un contact",
            response_description="Contact supprimé",
            tags=["Config"])
async def delete_contact(contact_name: str):
    try:
        contact_manager.delete_contact(contact_name)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.post("/config/contact-aliases",
          summary="Ajouter un alias contact",
          response_description="Alias contact ajouté",
          tags=["Config"])
async def add_contact_alias(item: ContactAliasItem):
    try:
        contact_manager.add_alias(item.alias, item.contact_name)
        return {"status": "ok", "alias": item.alias, "contact_name": item.contact_name}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.delete("/config/contact-aliases/{alias}",
            summary="Supprimer un alias contact",
            response_description="Alias contact supprimé",
            tags=["Config"])
async def delete_contact_alias(alias: str):
    try:
        contact_manager.delete_alias(alias)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

# ============================================================
# ROUTES API - CALLBACKS
# ============================================================

@app.post("/robot/state",
          summary="Publier etat UX vers robot",
          response_description="Resultat publication MQTT",
          tags=["Robot"])
async def publish_robot_state(request: RobotStateRequest):
    """
    Relay backend (Option B) pour publier l'etat UX vers le robot servo.

    Topic cible: gob/robot/state
    """
    if not agent_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Core not initialized"
        )

    mqtt_client = getattr(agent_core, "mqtt_client", None)
    if not mqtt_client or not mqtt_client.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MQTT relay unavailable"
        )

    allowed_states = {
        "idle", "sleep", "listening", "thinking", "speaking", "happy", "error"
    }
    normalized_state = request.state.strip().lower()
    if normalized_state not in allowed_states:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid robot state: {request.state}"
        )

    lang = (request.lang or Config.DEFAULT_LANGUAGE).strip().lower()
    if lang not in {"fr", "en", "ar"}:
        lang = Config.DEFAULT_LANGUAGE

    payload = {
        "request_id": request.request_id or f"req_{uuid.uuid4().hex[:12]}",
        "user_id": request.user_id,
        "state": normalized_state,
        "lang": lang,
        "source": request.source or "agent_ui",
        "ts": request.ts if request.ts is not None else int(datetime.utcnow().timestamp())
    }

    mqtt_result = mqtt_client.publish_robot_state(payload)
    if mqtt_result.get("status") != "published":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "MQTT publish failed",
                "mqtt": mqtt_result
            }
        )

    return {
        "status": "published",
        "topic": Config.MQTT_TOPIC_ROBOT_STATE_OUT,
        "payload": payload,
        "mqtt": mqtt_result,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/callback/n8n",
          summary="Callback résultat n8n",
          response_description="Acknowledgment",
          tags=["Callbacks"])
async def n8n_callback(request: N8NCallbackRequest):
    """
    Reçoit le résultat d'exécution depuis n8n (webhook callback).
    
    **Pipeline:**
    1. Réception résultat (success/failed)
    2. StateManager: EXECUTING → COMPLETED ou FAILED
    3. Journalisation résultat
    4. TODO: Notification utilisateur
    
    **Workflow n8n:**
    - En fin de workflow, n8n fait POST vers cette route
    - Contient action_id + status + result
    """
    if not agent_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Core not initialized"
        )
    
    logger.info(f"📨 n8n callback for action {request.action_id}: {request.status}")
    
    try:
        await agent_core.handle_execution_result({
            "action_id": request.action_id,
            "status": request.status,
            "result": request.result,
            "error": request.error,
            "execution_time_ms": request.execution_time_ms
        })
        
        return {
            "status": "acknowledged",
            "action_id": request.action_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Error processing n8n callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================
# ROUTES API - MONITORING
# ============================================================

@app.get("/health",
         summary="Health check",
         response_description="État système",
         tags=["Monitoring"])
async def health_check():
    """
    Vérifie l'état de santé du système.
    
    **Retourne:**
    - status: ok/degraded/down
    - components: État de chaque composant
    - timestamp
    """
    components_status = {
        "agent_core": "ok" if agent_core else "down",
        "llm": "unknown",  # TODO: Ping LLM
        "n8n": "disabled" if not Config.ENABLE_N8N_INTEGRATION else "unknown",
        "mqtt": "disabled" if not Config.ENABLE_MQTT_INTEGRATION else "unknown",
        "stt": "ok" if Config.ENABLE_AUDIO_PROCESSING else "disabled",
        "tts": "ok" if Config.ENABLE_AUDIO_PROCESSING else "disabled",
    }
    
    # Déterminer le status global
    if components_status["agent_core"] == "down":
        overall_status = "down"
    elif "unknown" in components_status.values():
        overall_status = "degraded"
    else:
        overall_status = "ok"
    
    return {
        "status": overall_status,
        "version": "1.0.0",
        "environment": Config.ENVIRONMENT,
        "components": components_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/memory/{user_id}",
         summary="Get user memory",
         response_description="Facts stored about the user",
         tags=["Memory"])
async def get_user_memory(user_id: str):
    """
    Récupère tous les facts stockés pour un utilisateur.
    
    **Args:**
    - user_id: ID de l'utilisateur
    
    **Retourne:**
    - user_id: ID user
    - total_facts: Nombre total de facts
    - facts: Liste des facts avec type, clé, valeur, confidence
    - recent_emotions: Liste des émotions récentes
    """
    if not agent_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Core not initialized"
        )
    
    try:
        # Récupérer les facts depuis le MemoryService
        memory_service = agent_core.memory_service
        
        if memory_service is None:
            return JSONResponse(
                status_code=200,
                content={
                    "user_id": user_id,
                    "facts": [],
                    "recent_emotions": [],
                    "message": "Memory service not available"
                }
            )
        
        facts = memory_service.get_facts(user_id)  # ✅ get_facts au lieu de get_user_facts
        
        # Extraire les émotions récentes des conversations
        conversations = memory_service.get_conversation_history(user_id, limit=10)
        recent_emotions = []
        for conv in conversations:
            if conv.get('metadata') and conv['metadata'].get('emotion'):
                emotion = conv['metadata']['emotion']
                if emotion and emotion not in recent_emotions:
                    recent_emotions.append(emotion)
        
        # Construire les préférences
        preferences = {}
        for fact in facts:
            if fact['fact_type'] in ['food', 'drink', 'preference']:
                preferences[fact['fact_key']] = fact['fact_value']
        
        return {
            "user_id": user_id,
            "total_facts": len(facts),
            "facts": facts,
            "recent_emotions": recent_emotions[:5],  # Max 5
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error fetching memory for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch memory: {str(e)}"
        )


@app.get("/stats",
         summary="Statistiques système",
         response_description="Statistiques d'utilisation",
         tags=["Monitoring"])
async def get_stats():
    """
    Retourne des statistiques d'utilisation du système.
    
    **Retourne:**
    - total_requests: Nombre total de requêtes
    - conversations: Nombre de conversations
    - actions: Statistiques par état
    - uptime: Temps de fonctionnement
    """
    if not agent_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Core not initialized"
        )
    
    # TODO: Implémenter collecte statistiques réelles
    return {
        "total_requests": 0,
        "conversations": {
            "total": 0,
            "today": 0
        },
        "actions": {
            "draft": 0,
            "pending_confirmation": 0,
            "confirmed": 0,
            "executing": 0,
            "completed": 0,
            "canceled": 0,
            "failed": 0
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================
# ROUTE RACINE
# ============================================================

@app.get("/",
         summary="Informations API",
         response_description="Informations de base",
         tags=["Root"])
async def root():
    """Informations de base sur l'API."""
    return {
        "name": "PCD - Agent Intelligent Embarqué API",
        "version": "1.0.0",
        "description": "Backend Python orchestrateur pour agent vocal intelligent",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "commands": ["/command/text", "/command/audio"],
            "actions": ["/action/confirm/{action_id}", "/action/status/{action_id}"],
            "robot": ["/robot/state"],
            "callbacks": ["/callback/n8n"],
            "monitoring": ["/health", "/stats"]
        }
    }


# ============================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================

if __name__ == "__main__":
    """
    Démarrage du serveur en mode standalone.
    
    Usage:
        python backend/main.py
    
    Ou avec uvicorn:
        uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    """
    uvicorn.run(
        "backend.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower(),
        access_log=True
    )
