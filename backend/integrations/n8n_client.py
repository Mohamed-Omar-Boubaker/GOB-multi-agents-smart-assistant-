"""
n8n Client - Communication avec n8n
Responsable: OMAR & Montassar
Priorité: 🟢 MOYENNE
Temps estimé: 8h

INPUT JSON:
{
  "action_json": {...},  # ActionJSON CONFIRMED + signé
  "webhook_url": "http://localhost:5678/webhook/action",
  "timeout_seconds": 60
}

OUTPUT JSON:
{
  "action_id": "act_abc123xyz",
  "status": "sent",
  "n8n_response": {
    "execution_id": "n8n_exec_001",
    "status": "accepted"
  },
  "sent_at": "2026-01-20T10:30:19Z",
  "response_time_ms": 345
}

Statuts: "sent", "failed", "timeout"
"""

import httpx  # type: ignore
import time
from datetime import datetime, timezone
from typing import Dict, Optional
import logging

# Import validation
from backend.utils.validators import JSONValidator
from backend.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class N8NClient:
    """
    Client pour communication avec n8n.
    Envoie ActionJSON vers webhook n8n.
    """
    
    def __init__(self, webhook_url: Optional[str] = None, timeout: int = 60):
        """
        Initialiser le client n8n.
        
        Args:
            webhook_url: URL webhook n8n
            timeout: Timeout en secondes (défaut: 60)
        """
        from backend.config import Config
        
        self.webhook_url = webhook_url or Config.N8N_WEBHOOK_URL
        self.timeout = timeout
        self.enabled = Config.ENABLE_N8N_INTEGRATION
        
        if not self.enabled:
            logger.warning("n8n integration is disabled")
        elif not self.webhook_url:
            logger.warning("n8n webhook URL not configured")
    
    async def send_action(self, action_json: Dict) -> Dict:
        """
        Envoyer ActionJSON confirmée vers n8n.
        
        Args:
            action_json: ActionJSON complète et signée
        
        Returns:
            Résultat de l'envoi
        """
        if not self.enabled:
            return {
                "action_id": action_json.get("action_id"),
                "status": "mock",
                "message": "n8n not configured",
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
        
        if not self.webhook_url:
            raise ValueError("n8n webhook URL not configured")
        
        action_id = action_json.get("action_id", "unknown")
        
        # ✅ VALIDATION: Valider ActionJSON avant envoi vers n8n
        try:
            JSONValidator.validate_action_json_complete(action_json)
            logger.info(f"✅ ActionJSON validé pour n8n: {action_id}")
        except ValidationError as e:
            logger.error(f"❌ ActionJSON invalide pour n8n {action_id}: {e}")
            return {
                "action_id": action_id,
                "status": "failed",
                "error": f"Validation failed: {str(e)}",
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
        
        try:
            start_time = time.time()
            
            logger.info(f"Sending action {action_id} to n8n: {self.webhook_url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=action_json,
                    headers={
                        "Content-Type": "application/json",
                        "X-Agent-Source": "python-backend"
                    }
                )
                
                response.raise_for_status()
                
                response_time_ms = int((time.time() - start_time) * 1000)
                
                result = {
                    "action_id": action_id,
                    "status": "sent",
                    "n8n_response": response.json() if response.text else {},
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "response_time_ms": response_time_ms,
                    "http_status": response.status_code
                }
                
                logger.info(f"Action {action_id} sent successfully to n8n (${response_time_ms}ms)")
                
                return result
        
        except httpx.TimeoutException:
            logger.error(f"Timeout sending action {action_id} to n8n")
            return {
                "action_id": action_id,
                "status": "timeout",
                "error": "n8n webhook timeout",
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending action {action_id} to n8n: {e.response.status_code}")
            return {
                "action_id": action_id,
                "status": "failed",
                "error": f"HTTP {e.response.status_code}",
                "details": e.response.text,
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error sending action {action_id} to n8n: {e}", exc_info=True)
            return {
                "action_id": action_id,
                "status": "failed",
                "error": str(e),
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def check_health(self) -> bool:
        """
        Vérifier la disponibilité de n8n.
        
        Returns:
            True si n8n est accessible
        """
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    self.webhook_url.replace("/webhook/", "/healthz"),
                    follow_redirects=True
                )
                return response.status_code == 200
        except:
            return False
    
    def send(self, input_data: dict) -> dict:
        """
        Envoyer ActionJSON vers n8n (méthode synchrone pour compatibilité).
        
        Args:
            input_data: Dict avec action_json, webhook_url, timeout
            
        Returns:
            Dict avec status, n8n_response, response_time_ms
        """
        import asyncio
        
        action_json = input_data.get("action_json", {})
        
        # Utiliser l'event loop pour exécuter la méthode async
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_action(action_json))
