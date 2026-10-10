# Résumé de Compréhension - Cahier des Charges Agent Embarqué

**Date de lecture :** 20 janvier 2026

---

## 🎯 Vue Globale du Projet

Le projet consiste à développer un **agent intelligent embarqué** capable d'interagir naturellement avec l'utilisateur par **commandes vocales ou textuelles** et d'exécuter de manière autonome diverses actions pratiques (envoi d'emails, contrôle domotique, recherches web, rappels, etc.).

### Objectif Principal
Créer un assistant personnel intelligent, local et sécurisé, offrant une alternative éthique et flexible aux assistants commerciaux (Google Assistant, Alexa, Siri).

---

## 🏗️ Architecture Technique - Principe Fondamental

L'architecture repose sur une **séparation stricte des responsabilités** en 3 couches :

### 1️⃣ **Couche d'Entrée/Sortie : ESP32**
- **Rôle :** Interface vocale embarquée (microphone + haut-parleur)
- **Responsabilités :**
  - Capture des commandes vocales de l'utilisateur
  - Enregistrement de segments audio courts
  - Transmission des données audio au Backend Python via réseau
  - Restitution des réponses vocales à l'utilisateur
- **Limitations volontaires :** 
  - ❌ Aucune intelligence artificielle embarquée
  - ❌ Aucun traitement vocal sur l'ESP32
  - ❌ Aucune prise de décision locale
  - ✅ Composant "muet" respectant les contraintes matérielles

### 2️⃣ **Couche Intelligence : Backend Python**
- **Rôle :** Noyau intelligent et décisionnel du système
- **Responsabilités :**
  - Transcription vocale (Speech-to-Text)
  - Analyse linguistique via module LLM
  - Détection des intentions utilisateur
  - Extraction des paramètres d'action
  - Gestion d'état des commandes (DRAFT → CONFIRMED)
  - Génération de confirmations vocales
  - Transmission des actions validées vers n8n
- **Principe clé :** 
  - ✅ Centralise toute l'intelligence
  - ✅ Ne fait AUCUNE exécution directe d'actions
  - ✅ Contrôle total du flux décisionnel

### 3️⃣ **Couche Exécution : n8n**
- **Rôle :** Moteur d'orchestration et d'exécution des workflows
- **Responsabilités :**
  - Réception des actions confirmées via webhooks
  - Routage vers les workflows spécialisés
  - Exécution des actions concrètes (envoi email, message, domotique)
  - Journalisation et traçabilité des actions
- **Principe clé :**
  - ❌ N'effectue aucune décision intelligente
  - ❌ N'interagit jamais directement avec l'utilisateur
  - ✅ Exécute uniquement les actions pré-validées

---

## 🔄 Flux de Traitement (Cycle de Vie d'une Commande)

### Étape 1 : Capture vocale
```
Utilisateur → ESP32 → Backend Python (audio brut)
```

### Étape 2 : Traitement intelligent
```
Backend Python :
1. Transcription vocale (Whisper/Speech Recognition)
2. Analyse linguistique (LLM)
3. Extraction intention + paramètres
4. État = DRAFT
```

### Étape 3 : Confirmation utilisateur
```
Backend Python → ESP32 → Utilisateur (confirmation vocale)
Utilisateur répond : "Confirme" / "Corrige" / "Annule"
```

### Étape 4 : Validation ou correction
```
Si confirmation → État = CONFIRMED
Si correction → Retour DRAFT avec nouveaux paramètres
Si annulation → Fin du cycle (aucune action)
```

### Étape 5 : Exécution (uniquement si CONFIRMED)
```
Backend Python → n8n (webhook avec action structurée)
n8n → Workflow spécialisé → Service externe → Exécution
```

---

## 🎭 Les 4 Acteurs du Système

### 1. **Utilisateur**
- Personne utilisant l'assistant (particulier, PMR, foyer connecté)
- Interagit par voix ou texte
- Configure préférences et autorisations
- Valide explicitement les actions sensibles

### 2. **Développeurs du système**
- Conçoivent et maintiennent le système
- Ajoutent/modifient les agents et workflows
- Gèrent sécurité, modèles IA et APIs
- Déploient les mises à jour

### 3. **Services externes**
- APIs tierces (météo, email, recherche, IoT)
- Fournissent données et fonctionnalités
- Interagissent uniquement avec n8n après validation

### 4. **Système matériel embarqué (ESP32)**
- Dispositif IoT d'entrée/sortie vocale
- Exécute actions physiques sur instruction validée
- Remonte états capteurs vers Backend

---

## 🛡️ Principes de Sécurité Fondamentaux

### ✅ Validation Humaine Obligatoire (Human-in-the-Loop)
- **Aucune action sensible sans confirmation explicite**
- Machine d'états DRAFT → CONFIRMED
- Possibilité de correction/annulation avant exécution

### ✅ Séparation Intelligence / Exécution
- LLM utilisé uniquement pour compréhension linguistique
- Aucun accès direct du LLM aux services d'exécution
- Backend Python garde le contrôle final

### ✅ Sécurité Multi-Niveaux
- Protection contre injections SQL
- Prévention attaques par prompt
- Chiffrement données sensibles
- Authentification utilisateur obligatoire
- Traçabilité complète des actions

---

## 🔧 Technologies Utilisées

### Intelligence & Backend
- **Python** : Noyau du système
- **LLM / Whisper** : NLP et reconnaissance vocale
- **PyTorch / TensorFlow** : Deep Learning
- **Hugging Face Transformers** : Modèles NLP

### Orchestration & Exécution
- **n8n** : Workflows et automatisation
- **APIs REST/GraphQL** : Services externes

### Matériel Embarqué
- **ESP32** : Dispositif IoT vocal
- **MQTT** : Communication IoT

### Infrastructure
- **SQL** (MySQL/PostgreSQL/SQLite) : Base de données
- **Docker** : Déploiement conteneurisé
- **Git/GitHub** : Versioning

### Frontend (optionnel)
- **React.js / Vue.js** : Interface web interactive

---

## 📋 Besoins Fonctionnels Clés (Utilisateur)

| ID | Besoin | Description |
|----|--------|-------------|
| BF1 | Communication naturelle | Voix ou texte via interface web/mobile |
| BF2 | Exécution d'actions | Instructions en langage naturel |
| BF3 | Recherche web | Résultats clairs et résumés |
| BF5 | Envoi d'emails | Dictée ou saisie du contenu |
| BF7 | Notifications intelligentes | Rappels, météo, événements, médicaments, prière |
| BF9 | Contrôle domotique | Lampes, TV, climatiseur via commandes vocales |
| BF10 | Gestion permissions | Confirmation avant actions sensibles |
| BF12 | Historique | Consultation des interactions passées |

---

## ⚙️ Besoins Non-Fonctionnels Essentiels

| ID | Besoin | Impact |
|----|--------|--------|
| BNF3 | Distribution automatique | Agents spécialisés selon tâches |
| BNF4 | Authentification | Sécurité actions sensibles |
| BNF5 | Protection malveillante | Blocage virus, injections, attaques |
| BNF7 | Mode hors ligne | Fonctionnement partiel local |
| BNF9 | Confidentialité | Suppression données à tout moment |
| BNF10 | Modularité | Ajout/suppression agents facilité |
| BNF12 | Interface intuitive | UX simple et responsive |

---

## 🎬 Scénarios d'Utilisation Types

### Scénario 1 : Envoi d'email réussi
1. Utilisateur : *"Envoie un email à Jean pour lui dire que la réunion est reportée"*
2. ESP32 capture → Backend traite
3. Backend génère confirmation : *"J'ai préparé un email pour Jean avec le message suivant : 'La réunion est reportée'. Dois-je l'envoyer ?"*
4. Utilisateur : *"Oui, envoie"*
5. Backend → n8n → Workflow email → Envoi effectif
6. Confirmation à l'utilisateur

### Scénario 2 : Correction avant envoi
1. Utilisateur : *"Envoie un email à Marc"*
2. Backend : *"Email pour Marc. Quel est le contenu ?"*
3. Utilisateur fournit corrections
4. Cycle DRAFT jusqu'à validation complète

### Scénario 3 : Annulation
1. Utilisateur demande action
2. Confirmation générée
3. Utilisateur : *"Non, annule"*
4. Backend stoppe le cycle, aucune exécution

---

## 🎯 Points Clés de Différenciation

### Vs Assistants Commerciaux (Google/Alexa/Siri)
✅ **Autonomie locale** : Fonctionne hors ligne partiellement  
✅ **Pas de dépendance cloud** : Système embarqué contrôlé  
✅ **Transparence totale** : Architecture ouverte et modulaire  
✅ **Éthique & Confidentialité** : Données sous contrôle utilisateur  
✅ **Personnalisation complète** : Ajout agents/workflows sur mesure  

---

## 📊 Contraintes Générales Identifiées

### Matérielles
- Ressources limitées sur ESP32 (CPU, RAM)
- Système doit être optimisé pour dispositifs embarqués

### Sécurité
- Protection données personnelles obligatoire
- Gestion permissions complexe
- Prévention attaques multiples (SQL, prompt, réseau)

### Techniques
- Compatibilité multi-langages/frameworks
- Intégration fluide Python-n8n-ESP32
- Respect contraintes temps réel pour vocal

### Organisationnelles
- Délais académiques du projet
- Ressources équipe développement

---

## ✅ Compréhension Validée

J'ai bien compris :
1. ✅ L'architecture distribuée en 3 couches distinctes
2. ✅ Le principe de séparation Intelligence/Décision/Exécution
3. ✅ Le rôle limité de l'ESP32 (pas d'IA embarquée)
4. ✅ Le rôle central du Backend Python (noyau intelligent)
5. ✅ Le rôle d'exécution de n8n (pas de décision)
6. ✅ Le système de validation DRAFT → CONFIRMED
7. ✅ L'importance de la sécurité et du contrôle utilisateur
8. ✅ Les différents besoins fonctionnels et non-fonctionnels
9. ✅ Les technologies à utiliser
10. ✅ Les scénarios d'utilisation types

---

## 🚀 Prochaines Étapes

Je suis maintenant prêt à :
- Lire les fichiers techniques détaillés un par un
- Comprendre l'architecture spécifique de chaque module
- Créer des résumés pour chaque composant
- Commencer l'implémentation pas à pas
