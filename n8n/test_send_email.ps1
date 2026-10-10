# 📧 Script de Test - wf_send_email.json
# Test du workflow d'envoi d'email via n8n

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    TEST WORKFLOW SEND EMAIL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si n8n est actif
Write-Host "[1/5] Vérification n8n..." -ForegroundColor Yellow
try {
    $n8nCheck = Invoke-WebRequest -Uri "http://localhost:5678" -Method GET -UseBasicParsing -TimeoutSec 3
    Write-Host "✅ n8n est actif (port 5678)" -ForegroundColor Green
} catch {
    Write-Host "❌ n8n n'est pas actif ou n'est pas accessible sur le port 5678" -ForegroundColor Red
    Write-Host "   Lancez n8n avec: npm start" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Demander l'email de test
Write-Host "[2/5] Configuration email de test" -ForegroundColor Yellow
$testEmail = Read-Host "Entrez votre email pour recevoir le test (ex: votre-email@gmail.com)"

if ([string]::IsNullOrWhiteSpace($testEmail)) {
    Write-Host "❌ Email requis pour le test" -ForegroundColor Red
    exit 1
}

Write-Host "📧 Email de test: $testEmail" -ForegroundColor Cyan
Write-Host ""

# Préparer le payload ActionJSON
Write-Host "[3/5] Préparation ActionJSON..." -ForegroundColor Yellow

$actionJson = @{
    action_id = "act_test_$(Get-Date -Format 'yyyyMMddHHmmss')"
    intent = "send_email"
    state = "CONFIRMED"
    confirmed = $true
    priority = "normal"
    payload = @{
        recipient = "Test User"
        recipient_email = $testEmail
        cc = @()
        bcc = @()
        subject = "✅ Test n8n Workflow - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        body = @"
Bonjour,

Ceci est un email de test envoyé depuis le workflow n8n wf_send_email.

Si vous recevez ce message, cela signifie que :
✅ L'extraction du payload ActionJSON fonctionne
✅ La validation de l'email est correcte
✅ La connexion Gmail SMTP est établie
✅ L'envoi d'email est opérationnel

Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Action ID: act_test_$(Get-Date -Format 'yyyyMMddHHmmss')

Cordialement,
Agent PCD (Workflow n8n)
"@
        body_format = "plain"
        attachments = @()
        priority = "normal"
        reply_to = $null
        send_at = $null
    }
    context = @{
        user_id = "user_test"
        language = "fr"
        channel = "test"
        session_id = "session_test_$(Get-Date -Format 'yyyyMMddHHmmss')"
        location = "development"
        time_of_day = "test"
    }
    security = @{
        auth_level = 1
        signature = "test_signature"
        signed_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        requires_confirmation = $false
        permissions_required = @("email.send")
    }
    metadata = @{
        request_id = "req_test_$(Get-Date -Format 'yyyyMMddHHmmss')"
        llm_confidence = 0.98
        classification_confidence = 0.95
        retry_count = 0
        parent_action_id = $null
    }
    timestamps = @{
        created_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        updated_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        expires_at = (Get-Date).AddMinutes(30).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    version = "2.0"
}

$jsonPayload = $actionJson | ConvertTo-Json -Depth 10

Write-Host "✅ ActionJSON préparé (Action ID: $($actionJson.action_id))" -ForegroundColor Green
Write-Host ""

# Envoyer le webhook
Write-Host "[4/5] Envoi webhook à n8n..." -ForegroundColor Yellow
Write-Host "URL: http://localhost:5678/webhook/send_email" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "http://localhost:5678/webhook/send_email" `
        -Method POST `
        -ContentType "application/json" `
        -Body $jsonPayload `
        -TimeoutSec 30

    Write-Host "✅ Requête envoyée avec succès" -ForegroundColor Green
    Write-Host ""

    # Afficher la réponse
    Write-Host "[5/5] Résultat:" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    
    if ($response.state -eq "SUCCESS") {
        Write-Host "✅ SUCCÈS - Email envoyé!" -ForegroundColor Green
        Write-Host "   Action ID: $($response.action_id)" -ForegroundColor Cyan
        Write-Host "   Destinataire: $($response.result.recipient_email)" -ForegroundColor Cyan
        Write-Host "   Sujet: $($response.result.subject)" -ForegroundColor Cyan
        Write-Host "   Envoyé à: $($response.result.sent_at)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📬 Vérifiez votre boîte de réception: $testEmail" -ForegroundColor Yellow
    } elseif ($response.state -eq "FAILED") {
        Write-Host "❌ ÉCHEC - Erreur d'envoi" -ForegroundColor Red
        Write-Host "   Code erreur: $($response.error.code)" -ForegroundColor Red
        Write-Host "   Message: $($response.error.message)" -ForegroundColor Red
        
        if ($response.error.message -like "*Invalid credentials*") {
            Write-Host ""
            Write-Host "💡 Solution: Vérifiez vos variables d'environnement n8n:" -ForegroundColor Yellow
            Write-Host "   - GMAIL_USER = votre-email@gmail.com" -ForegroundColor Yellow
            Write-Host "   - GMAIL_APP_PASSWORD = mot-de-passe-application-gmail" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "   Comment obtenir un mot de passe application Gmail:" -ForegroundColor Yellow
            Write-Host "   1. Activer la validation en 2 étapes sur Google" -ForegroundColor Yellow
            Write-Host "   2. https://myaccount.google.com/apppasswords" -ForegroundColor Yellow
            Write-Host "   3. Créer un nouveau mot de passe pour 'n8n'" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️ État inconnu: $($response.state)" -ForegroundColor Yellow
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Réponse complète (JSON):" -ForegroundColor Gray
    $response | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor DarkGray

} catch {
    Write-Host "❌ ERREUR lors de l'envoi du webhook" -ForegroundColor Red
    Write-Host "Message: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    
    if ($_.Exception.Message -like "*Unable to connect*") {
        Write-Host "💡 Vérifiez que:" -ForegroundColor Yellow
        Write-Host "   1. n8n est bien démarré (npm start)" -ForegroundColor Yellow
        Write-Host "   2. Le workflow wf_send_email.json est importé et activé" -ForegroundColor Yellow
        Write-Host "   3. Le webhook path est: /send_email" -ForegroundColor Yellow
    }
    
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    TEST TERMINÉ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
