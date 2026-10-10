# 📧 Système de Contacts - Option 1 + 2 Implémenté

## ✅ Ce Qui A Été Ajouté

### 1. **Base de Contacts** (`backend/data/contacts.json`)
- Fichier JSON avec tous vos contacts
- Alias pour noms familiers ("mon ami" → "jean")
- Informations complètes (nom, email, téléphone, tags)

### 2. **ContactManager** (`backend/utils/contact_manager.py`)
- Résolution intelligente nom → email
- Détection emails fictifs
- API pour gérer contacts

### 3. **Validation Backend** (action_builder.py)
- Recherche automatique dans contacts.json
- Rejet emails @example.com
- Erreur explicite si contact inconnu

### 4. **Double Validation n8n** (wf_send_email.json)
- Validation format email
- Rejet emails fictifs
- Message d'erreur clair

---

## 🎯 Comment Ça Marche Maintenant

### Cas 1 : Contact Connu ✅

```
User: "Envoie un mail à Amine"
    ↓
Backend: Cherche "amine" dans contacts.json
    → Trouvé: amine@ensi.tn ✅
    ↓
ActionJSON: {"recipient_email": "amine@ensi.tn"}
    ↓
n8n: Valide + Envoie ✅
```

### Cas 2 : Alias Reconnu ✅

```
User: "Envoie un mail à mon ami"
    ↓
Backend: Cherche "mon ami" dans aliases
    → Alias trouvé: "mon ami" → "jean"
    → Contact trouvé: jean.martin@gmail.com ✅
    ↓
ActionJSON: {"recipient_email": "jean.martin@gmail.com"}
    ↓
n8n: Valide + Envoie ✅
```

### Cas 3 : Contact Inconnu ❌

```
User: "Envoie un mail à inconnu"
    ↓
Backend: Cherche "inconnu" dans contacts.json
    → Pas trouvé ❌
    → LLM génère: inconnu@example.com
    ↓
Backend: Détecte @example.com → REJETTE
    ↓
Erreur: "Contact 'inconnu' introuvable. Ajoutez-le dans vos contacts."
    ↓
TTS: "Je ne connais pas ce contact. Dites 'ajoute contact' pour le créer."
```

### Cas 4 : Email Fictif Passé ❌ (Double Sécurité)

```
Backend: Ne détecte pas (bug hypothétique)
    ↓
ActionJSON: {"recipient_email": "fake@example.com"}
    ↓
n8n Validate Recipient: Détecte @example.com → REJETTE ❌
    ↓
Erreur: "Email fictif rejeté: fake@example.com"
```

---

## 📝 Ajouter un Nouveau Contact

### Méthode 1 : Éditer `backend/data/contacts.json`

```json
{
  "contacts": {
    "amine": {
      "name": "Amine Ben Salem",
      "email": "amine@ensi.tn",
      "phone": "+216 20 123 456",
      "tags": ["collègue", "projet"]
    },
    "nouveau_contact": {
      "name": "Nouveau Nom",
      "email": "nouveau@example.com",
      "phone": "+216 XX XXX XXX",
      "tags": ["ami"]
    }
  },
  "aliases": {
    "mon ami": "jean",
    "mon pote": "jean",
    "amin": "amine"
  }
}
```

Puis **redémarrer le backend** pour recharger :
```powershell
# Kill backend
Ctrl+C dans le terminal uvicorn

# Relancer
uvicorn backend.main:app --reload --port 8000
```

### Méthode 2 : API Python (À implémenter)

```python
from backend.utils.contact_manager import contact_manager

contact_manager.add_contact(
    contact_id="alice",
    name="Alice Dupont",
    email="alice.dupont@gmail.com",
    phone="+33 6 12 34 56 78",
    tags=["amie", "paris"]
)
```

---

## 🧪 Tests

### Test 1 : Contact Existant

```powershell
cd "C:\Users\lapte\OneDrive - ensi-uma.tn\Bureau\GOB agint\pcd-ai-embedded-agent"

# Via voice_client
# Dites: "Envoie un mail à Amine"
# Résultat attendu: Email envoyé à amine@ensi.tn ✅
```

### Test 2 : Contact Inconnu

```powershell
# Dites: "Envoie un mail à personne-inconnue"
# Résultat attendu: Erreur "Contact non trouvé" ❌
# TTS: "Je ne connais pas ce contact..."
```

### Test 3 : Alias

```powershell
# Dites: "Envoie un mail à mon ami"
# Résultat attendu: Email envoyé à jean.martin@gmail.com ✅
```

### Test 4 : Email Fictif Direct

```powershell
$payload = @{
    action_id = "act_test_fake"
    intent = "send_email"
    payload = @{
        recipient = "Test"
        recipient_email = "test@example.com"  # Fictif!
        subject = "Test"
        body = "Test"
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:5678/webhook-test/send_email" -Method POST -ContentType "application/json" -Body $payload
```

**Résultat attendu :**
```
Error: Email fictif rejeté: test@example.com. 
Le contact "Test" n'est pas dans votre liste.
```

---

## 📊 Contacts par Défaut

Le système vient avec ces contacts pré-configurés :

| ID | Nom | Email | Alias |
|----|-----|-------|-------|
| amine | Amine Ben Salem | amine@ensi.tn | amin |
| jean | Jean Martin | jean.martin@gmail.com | mon ami, mon pote |
| montassar | Montassar Nawara | montassar.nawara@ensi-uma.tn | |

---

## 🔧 Personnalisation

### Ajouter un Alias

```json
{
  "aliases": {
    "mon ami": "jean",
    "mon pote": "jean",
    "le prof": "professeur",
    "ma mère": "maman"
  }
}
```

### Ajouter des Tags

```json
{
  "contacts": {
    "amine": {
      "name": "Amine",
      "email": "amine@ensi.tn",
      "tags": ["collègue", "projet", "pcd", "ensi"]
    }
  }
}
```

**Utilité future :** Filtrage par tags
```
User: "Envoie un mail à tous mes collègues"
→ Résolution: Tous les contacts avec tag "collègue"
```

---

## ⚠️ Limitations Actuelles

1. **Ajout contact par voix** : Pas encore implémenté
   - Workaround: Éditer manuellement contacts.json
   
2. **Recherche floue** : Pas d'auto-correction
   - "Aminn" ne trouve pas "Amine"
   - Workaround: Utiliser les alias
   
3. **Contacts groupes** : Pas supporté
   - "Envoie mail à toute l'équipe"
   - Workaround: Utiliser CC

---

## 🚀 Prochaines Améliorations Possibles

1. **Endpoint API** : POST /contacts/add
2. **Commande vocale** : "Ajoute contact Jean avec email jean@gmail.com"
3. **Recherche floue** : Tolérance fautes frappe
4. **Import CSV** : Import contacts depuis fichier
5. **Sync Google Contacts** : Import automatique

---

## 📞 Support

Si un email légitime est rejeté :
1. Vérifier qu'il n'utilise pas @example.com
2. Vérifier format: nom@domaine.extension
3. Ajouter dans contacts.json
4. Redémarrer backend

**Logs utiles :**
```
✅ [Contacts] Contact trouvé: Amine Ben Salem (amine@ensi.tn)
❌ [Contacts] Contact non trouvé: 'inconnu'
🚫 [Contacts] Email fictif détecté: test@example.com
```

---

**Système Opérationnel ! Option 1 + 2 Implémentées ✅**
