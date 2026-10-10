"""
MQTT Client - Communication ESP32
Responsable: montassar
Priorité: 🟢 MOYENNE
Temps estimé: 12h

INPUT JSON (Publier):
{
  "operation": "publish",
  "topic": "esp32/command/lamp_001",
  "message": {...},
  "qos": 1,
  "retain": false
}

INPUT JSON (S'abonner):
{
  "operation": "subscribe",
  "topic": "esp32/status/#",
  "qos": 1
}

OUTPUT JSON (Publish):
{
  "status": "published",
  "topic": "esp32/command/lamp_001",
  "message_id": "mqtt_msg_001",
  "published_at": "2026-01-20T10:30:20Z"
}

OUTPUT JSON (Message reçu - Callback):
{
  "topic": "esp32/status/lamp_001",
  "message": {...},
  "received_at": "2026-01-20T10:30:21Z"
}

Broker recommandé: Mosquitto
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Callable
import paho.mqtt.client as mqtt  # type: ignore
import uuid

# Import validation
from backend.utils.validators import JSONValidator
from backend.utils.exceptions import ValidationError
from backend.config import Config

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    Client MQTT pour communication ESP32.
    Publie commandes et reçoit statuts.
    """
    
    def __init__(
        self,
        broker: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialiser le client MQTT.
        
        Args:
            broker: Adresse broker MQTT
            port: Port broker
            username: Nom d'utilisateur MQTT
            password: Mot de passe MQTT
        """
        self.broker = broker or Config.MQTT_BROKER
        self.port = port or Config.MQTT_PORT
        self.username = username or Config.MQTT_USERNAME
        self.password = password or Config.MQTT_PASSWORD
        self.enabled = Config.ENABLE_MQTT_INTEGRATION
        
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.message_callback: Optional[Callable] = None
        
        if not self.enabled:
            logger.warning("MQTT integration is disabled")
        else:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialiser le client MQTT."""
        try:
            client_id = f"backend_python_{uuid.uuid4().hex[:8]}"
            client = mqtt.Client(client_id=client_id)
            
            # Configuration authentification
            if self.username and self.password:
                client.username_pw_set(self.username, self.password)
            
            # Callbacks
            client.on_connect = self._on_connect
            client.on_disconnect = self._on_disconnect
            client.on_message = self._on_message
            
            # Connexion
            logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}")
            client.connect(self.broker, self.port, keepalive=60)
            client.loop_start()
            
            # Assigner le client après configuration réussie
            self.client = client
            
        except Exception as e:
            logger.error(f"Error initializing MQTT client: {e}", exc_info=True)
            self.connected = False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback de connexion."""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            self.connected = True
        else:
            logger.error(f"Failed to connect to MQTT broker: code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback de déconnexion."""
        logger.warning(f"Disconnected from MQTT broker: code {rc}")
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        """Callback de réception de message."""
        try:
            payload = json.loads(msg.payload.decode())
            
            message_data = {
                "topic": msg.topic,
                "message": payload,
                "received_at": datetime.now(timezone.utc).isoformat(),
                "qos": msg.qos
            }
            
            logger.info(f"MQTT message received on {msg.topic}")
            
            # Appeler callback personnalisé si défini
            if self.message_callback:
                self.message_callback(message_data)
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in MQTT message: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}", exc_info=True)
    
    def publish(self, topic: str, message: Dict, qos: int = 1, retain: bool = False) -> Dict:
        """
        Publier un message MQTT.
        
        Args:
            topic: Topic MQTT
            message: Message à publier (dict)
            qos: Quality of Service (0, 1, 2)
            retain: Conserver le message
        
        Returns:
            Résultat de la publication
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "MQTT integration disabled"
            }
        
        if not self.connected:
            return {
                "status": "error",
                "message": "Not connected to MQTT broker"
            }
        
        try:
            message_json = json.dumps(message)
            message_id = f"mqtt_{uuid.uuid4().hex[:8]}"
            
            if self.client is None:
                raise RuntimeError("MQTT client not initialized")
            
            result = self.client.publish(
                topic,
                message_json,
                qos=qos,
                retain=retain
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published message to {topic}")
                return {
                    "status": "published",
                    "topic": topic,
                    "message_id": message_id,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "qos": qos
                }
            else:
                logger.error(f"Failed to publish to {topic}: {result.rc}")
                return {
                    "status": "failed",
                    "error": f"MQTT error code {result.rc}"
                }
        
        except Exception as e:
            logger.error(f"Error publishing MQTT message: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def subscribe(self, topic: str, qos: int = 1) -> Dict:
        """
        S'abonner à un topic MQTT.
        
        Args:
            topic: Topic MQTT (peut contenir wildcards # et +)
            qos: Quality of Service
        
        Returns:
            Résultat de l'abonnement
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "MQTT integration disabled"
            }
        
        if not self.connected:
            return {
                "status": "error",
                "message": "Not connected to MQTT broker"
            }
        
        try:
            if self.client is None:
                raise RuntimeError("MQTT client not initialized")
            
            result = self.client.subscribe(topic, qos=qos)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to {topic}")
                return {
                    "status": "subscribed",
                    "topic": topic,
                    "qos": qos,
                    "subscribed_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                logger.error(f"Failed to subscribe to {topic}: {result[0]}")
                return {
                    "status": "failed",
                    "error": f"MQTT error code {result[0]}"
                }
        
        except Exception as e:
            logger.error(f"Error subscribing to MQTT topic: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def execute(self, input_data: dict) -> dict:
        """
        Exécuter opération MQTT (publish/subscribe).
        
        Args:
            input_data: Dict avec operation, topic, message, qos
            
        Returns:
            Dict avec status, message_id, published_at
        """
        # ✅ VALIDATION: Valider input MQTT
        try:
            if not isinstance(input_data, dict):
                raise ValidationError("MQTT input must be a dictionary")
            
            # Valider champs requis selon operation
            operation = input_data.get("operation", "publish")
            
            if operation == "publish":
                required = ["topic", "message"]
            elif operation == "subscribe":
                required = ["topic"]
            else:
                raise ValidationError(f"Invalid operation: {operation}")
            
            for field in required:
                if field not in input_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            logger.info(f"✅ MQTT input validé: {operation} sur {input_data.get('topic')}")
        
        except ValidationError as e:
            logger.error(f"❌ MQTT input invalide: {e}")
            return {
                "status": "validation_error",
                "error": str(e)
            }
        
        operation = input_data.get("operation", "publish")
        
        if operation == "publish":
            topic = input_data.get("topic")
            if not topic:
                return {"status": "error", "error": "Missing topic"}
            
            return self.publish(
                topic=topic,
                message=input_data.get("message", {}),
                qos=input_data.get("qos", 1),
                retain=input_data.get("retain", False)
            )
        
        elif operation == "subscribe":
            topic = input_data.get("topic")
            if not topic:
                return {"status": "error", "error": "Missing topic"}
            
            return self.subscribe(
                topic=topic,
                qos=input_data.get("qos", 1)
            )
        
        else:
            return {
                "status": "error",
                "error": f"Unknown operation: {operation}"
            }
    
    def set_callback(self, callback: Callable):
        """
        Définir callback pour messages reçus.
        
        Args:
            callback: Fonction appelée à réception message
        """
        self.message_callback = callback
        logger.info("MQTT message callback set")
    
    def is_connected(self) -> bool:
        """Vérifier si connecté au broker."""
        return self.connected and self.enabled
    
    def disconnect(self):
        """Déconnecter du broker MQTT."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
    
    # ============================================================
    # MÉTHODES AUDIO & DEVICE (Phase 1 - MQTT Pipeline)
    # ============================================================
    
    def publish_audio(self, audio_base64: str, user_id: Optional[str] = None) -> Dict:
        """
        Publier audio vers device (Fake ESP32 ou ESP32 réel).
        
        Pipeline: TTS → Audio base64 → MQTT → Device → Play audio
        
        Args:
            audio_base64: Audio encodé en base64
            user_id: ID utilisateur (pour logs)
            
        Returns:
            Dict avec status, topic, published_at
        """
        if not self.enabled or not self.connected:
            logger.warning("⚠️ MQTT not available, audio not sent to device")
            return {
                "status": "disabled",
                "message": "MQTT not available"
            }
        
        topic = Config.MQTT_TOPIC_AUDIO_OUT
        
        try:
            if self.client is None:
                raise RuntimeError("MQTT client not initialized")
            
            # Publier audio base64 brut
            result = self.client.publish(topic, audio_base64, qos=Config.MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"🎵 Audio publié vers device (topic: {topic}, user: {user_id})")
                return {
                    "status": "published",
                    "topic": topic,
                    "user_id": user_id,
                    "published_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                logger.error(f"❌ Erreur publish audio: MQTT error code {result.rc}")
                return {
                    "status": "failed",
                    "error": f"MQTT error code {result.rc}"
                }
                
        except Exception as e:
            logger.error(f"❌ Exception publish audio: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def publish_robot_state(self, payload: Dict) -> Dict:
        """
        Publish UX robot state for servo animation pipeline (Phase 2).

        Args:
            payload: JSON payload following gob/robot/state contract

        Returns:
            Publish result dict
        """
        topic = Config.MQTT_TOPIC_ROBOT_STATE_OUT
        return self.publish(
            topic=topic,
            message=payload,
            qos=Config.MQTT_QOS,
            retain=False
        )
    
    def setup_status_listener(self):
        """
        Configurer l'écoute des status devices.
        
        Écoute le topic device/status pour recevoir:
        - online/offline status
        - audio playing status
        - erreurs devices
        """
        if not self.enabled or not self.client:
            logger.warning("⚠️ MQTT disabled, status listener not configured")
            return
        
        status_topic = Config.MQTT_TOPIC_STATUS_IN
        
        try:
            # S'abonner au topic status
            result = self.client.subscribe(status_topic, qos=Config.MQTT_QOS)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"👂 Écoute status devices configurée (topic: {status_topic})")
            else:
                logger.error(f"❌ Erreur subscribe status: {result[0]}")
                
        except Exception as e:
            logger.error(f"❌ Exception setup status listener: {e}", exc_info=True)
    
    def _on_device_status(self, client, userdata, msg):
        """
        Callback interne pour messages status devices.
        
        Args:
            client: Client MQTT
            userdata: User data
            msg: Message reçu
        """
        try:
            payload = msg.payload.decode()
            status_data = json.loads(payload)
            
            device_id = status_data.get("device_id", "unknown")
            status = status_data.get("status", "unknown")
            message = status_data.get("message", "")
            timestamp = status_data.get("timestamp", "")
            
            logger.info(f"📱 Device {device_id}: {status} - {message}")
            
            # Possibilité de stocker dans DB ou cache pour monitoring
            # TODO: Implémenter storage si nécessaire
            
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Status message invalide (not JSON): {msg.payload}")
        except Exception as e:
            logger.error(f"❌ Erreur parsing status device: {e}", exc_info=True)
