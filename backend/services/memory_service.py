"""
Memory Service - Persistent User Memory with SQLite
Date: 12 Février 2026
Responsable: Montassar

Rôle:
- Stocker faits utilisateurs (nom, préférences, devices)
- Stocker historique conversations
- Mémoire persistante (survit redémarrages)
- Zéro infrastructure externe (SQLite embedded)

Architecture:
- Table user_facts: Stocke faits extraits (name, preferences, etc.)
- Table conversations: Historique complet user/assistant
- Auto-création DB + tables au premier démarrage
"""

import sqlite3
import json
from datetime import datetime, UTC
from typing import Dict, List, Optional
from pathlib import Path


class MemoryService:
    """
    Service de mémoire persistante avec SQLite.
    Stocke faits utilisateurs et historique conversations.
    """
    
    def __init__(self, db_path: str = "data/agent_memory.db"):
        """
        Initialiser le service de mémoire.
        
        Args:
            db_path: Chemin vers la base SQLite (créée automatiquement)
        """
        self.db_path = db_path
        
        # Créer dossier data/ si nécessaire
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialiser base de données et tables
        self._init_database()
        
        print(f"[MemoryService] Initialized - Database: {db_path}")
    
    def _init_database(self):
        """Créer les tables si elles n'existent pas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table 1: Faits utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                fact_type TEXT NOT NULL,
                fact_key TEXT NOT NULL,
                fact_value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, fact_type, fact_key)
            )
        """)
        
        # Table 2: Historique conversations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Index pour performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_facts_user_id 
            ON user_facts(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
            ON conversations(user_id, timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
        
        print("[MemoryService] Database tables initialized ✅")
    
    # ==================== USER FACTS ====================
    
    def add_fact(
        self,
        user_id: str,
        fact_type: str,
        fact_key: str,
        fact_value: str,
        confidence: float = 1.0
    ) -> bool:
        """
        Ajouter ou mettre à jour un fait utilisateur.
        
        Args:
            user_id: ID utilisateur
            fact_type: Type (name, preference, device_info, location, etc.)
            fact_key: Clé du fait (ex: "first_name", "favorite_color")
            fact_value: Valeur du fait
            confidence: Confiance (0.0-1.0)
            
        Returns:
            True si succès
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now(UTC).isoformat()
            
            cursor.execute("""
                INSERT INTO user_facts (user_id, fact_type, fact_key, fact_value, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, fact_type, fact_key) 
                DO UPDATE SET 
                    fact_value = excluded.fact_value,
                    confidence = excluded.confidence,
                    updated_at = excluded.updated_at
            """, (user_id, fact_type, fact_key, fact_value, confidence, now, now))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"[MemoryService] Error adding fact: {e}")
            return False
    
    def get_facts(
        self,
        user_id: str,
        fact_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Récupérer les faits d'un utilisateur.
        
        Args:
            user_id: ID utilisateur
            fact_type: Type optionnel pour filtrer
            
        Returns:
            Liste de faits
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if fact_type:
                cursor.execute("""
                    SELECT * FROM user_facts 
                    WHERE user_id = ? AND fact_type = ?
                    ORDER BY updated_at DESC
                """, (user_id, fact_type))
            else:
                cursor.execute("""
                    SELECT * FROM user_facts 
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"[MemoryService] Error getting facts: {e}")
            return []
    
    def get_fact(
        self,
        user_id: str,
        fact_type: str,
        fact_key: str
    ) -> Optional[str]:
        """
        Récupérer un fait spécifique.
        
        Args:
            user_id: ID utilisateur
            fact_type: Type de fait
            fact_key: Clé du fait
            
        Returns:
            Valeur du fait ou None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT fact_value FROM user_facts 
                WHERE user_id = ? AND fact_type = ? AND fact_key = ?
            """, (user_id, fact_type, fact_key))
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else None
            
        except Exception as e:
            print(f"[MemoryService] Error getting fact: {e}")
            return None
    
    # ==================== CONVERSATIONS ====================
    
    def add_conversation_turn(
        self,
        user_id: str,
        role: str,
        message: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Ajouter un tour de conversation.
        
        Args:
            user_id: ID utilisateur
            role: "user" ou "assistant"
            message: Texte du message
            metadata: Métadonnées optionnelles (dict)
            
        Returns:
            True si succès
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now(UTC).isoformat()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO conversations (user_id, role, message, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, role, message, timestamp, metadata_json))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"[MemoryService] Error adding conversation: {e}")
            return False
    
    def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Récupérer historique conversations récentes.
        
        Args:
            user_id: ID utilisateur
            limit: Nombre max de tours (default: 10 derniers)
            
        Returns:
            Liste de tours de conversation [{role, message, timestamp}]
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT role, message, timestamp, metadata 
                FROM conversations 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Inverser pour avoir ordre chronologique (plus ancien → plus récent)
            conversations = []
            for row in reversed(rows):
                conv = dict(row)
                if conv['metadata']:
                    conv['metadata'] = json.loads(conv['metadata'])
                conversations.append(conv)
            
            return conversations
            
        except Exception as e:
            print(f"[MemoryService] Error getting conversation history: {e}")
            return []
    
    # ==================== MEMORY CONTEXT ====================
    
    def build_memory_context(self, user_id: str, max_facts: int = 10) -> str:
        """
        Construire contexte mémoire pour injection dans prompt LLM.
        
        Args:
            user_id: ID utilisateur
            max_facts: Nombre max de faits à inclure
            
        Returns:
            Texte formaté pour prompt LLM
        """
        facts = self.get_facts(user_id)
        
        if not facts:
            return ""
        
        # Limiter nombre de faits
        facts = facts[:max_facts]
        
        # Formater pour prompt
        context_lines = ["# User Memory"]
        
        for fact in facts:
            fact_text = f"- {fact['fact_type']}.{fact['fact_key']}: {fact['fact_value']}"
            context_lines.append(fact_text)
        
        return "\n".join(context_lines)
    
    # ==================== UTILITIES ====================
    
    def clear_user_memory(self, user_id: str) -> bool:
        """
        Effacer toute la mémoire d'un utilisateur.
        
        Args:
            user_id: ID utilisateur
            
        Returns:
            True si succès
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM user_facts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            print(f"[MemoryService] Cleared memory for user {user_id}")
            return True
            
        except Exception as e:
            print(f"[MemoryService] Error clearing memory: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """
        Obtenir statistiques de la base mémoire.
        
        Returns:
            Dict avec statistiques
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_facts")
            users_with_facts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_facts")
            total_facts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM conversations")
            total_conversations = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "users_with_facts": users_with_facts,
                "total_facts": total_facts,
                "total_conversations": total_conversations,
                "database_path": self.db_path
            }
            
        except Exception as e:
            print(f"[MemoryService] Error getting stats: {e}")
            return {}
