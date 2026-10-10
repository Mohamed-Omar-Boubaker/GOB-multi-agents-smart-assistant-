# 🧪 Script de Test Pipeline n8n + MQTT
# Teste le flux complet: Backend → n8n → MQTT → Callback

Write-Host "🧪 Test Pipeline n8n + MQTT" -ForegroundColor Cyan
Write-Host "=" * 60

# ==================== CONFIGURATION ====================
$BackendUrl = "http://localhost:8000"
$N8nWebhook = "http://localhost:5678/webhook/action"
$MqttBroker = "localhost"
$MqttPort = 1883

# ==================== ÉTAPE 1: Vérifier Services ====================
Write-Host "`n📋 ÉTAPE 1: Vérification des services..." -ForegroundColor Yellow

# Check Backend
Write-Host "  ✓ Backend..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host " OK (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host " ERREUR: Backend non accessible!" -ForegroundColor Red
    Write-Host "    → Lancez: uvicorn backend.main:app --reload --port 8000" -ForegroundColor Yellow
    exit 1
}

# Check n8n
Write-Host "  ✓ n8n..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5678" -TimeoutSec 5 -ErrorAction Stop
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " ERREUR: n8n non accessible!" -ForegroundColor Red
    Write-Host "    → Vérifiez: docker ps | grep n8n" -ForegroundColor Yellow
    exit 1
}

# Check MQTT
Write-Host "  ✓ MQTT..." -NoNewline
$mqttTest = Test-NetConnection -ComputerName $MqttBroker -Port $MqttPort -WarningAction SilentlyContinue
if ($mqttTest.TcpTestSucceeded) {
    Write-Host " OK (Port $MqttPort ouvert)" -ForegroundColor Green
} else {
    Write-Host " ERREUR: MQTT non accessible!" -ForegroundColor Red
    Write-Host "    → Vérifiez service MQTT Windows ou Docker" -ForegroundColor Yellow
    exit 1
}

# ==================== ÉTAPE 2: Vérifier Config Backend ====================
Write-Host "`n📋 ÉTAPE 2: Vérification configuration backend..." -ForegroundColor Yellow

try {
    $configTest = python -c @"
from backend.config import Config
import json
print(json.dumps({
    'n8n_enabled': Config.ENABLE_N8N_INTEGRATION,
    'n8n_url': Config.N8N_WEBHOOK_URL,
    'mqtt_enabled': Config.ENABLE_MQTT_INTEGRATION,
    'mqtt_broker': Config.MQTT_BROKER,
    'demo_mode': Config.DEMO_MODE
}))
"@
    
    $config = $configTest | ConvertFrom-Json
    
    Write-Host "  ✓ N8N Integration: " -NoNewline
    if ($config.n8n_enabled) {
        Write-Host "ENABLED ✓" -ForegroundColor Green
    } else {
        Write-Host "DISABLED ✗" -ForegroundColor Red
        Write-Host "    → Modifiez backend/.env: ENABLE_N8N_INTEGRATION=True" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "  ✓ Demo Mode: " -NoNewline
    if (-not $config.demo_mode) {
        Write-Host "OFF ✓" -ForegroundColor Green
    } else {
        Write-Host "ON ✗" -ForegroundColor Red
        Write-Host "    → Modifiez backend/.env: DEMO_MODE=False" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "  ✓ MQTT Integration: " -NoNewline
    if ($config.mqtt_enabled) {
        Write-Host "ENABLED ✓" -ForegroundColor Green
    } else {
        Write-Host "DISABLED ✗" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  ✗ Erreur lecture config: $_" -ForegroundColor Red
    exit 1
}

# ==================== ÉTAPE 3: Test Webhook n8n ====================
Write-Host "`n📋 ÉTAPE 3: Test webhooks n8n..." -ForegroundColor Yellow

# Test webhook routeur
Write-Host "  ✓ Webhook routeur..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri $N8nWebhook -Method GET -ErrorAction SilentlyContinue
    Write-Host " Accessible ✓" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 405 -or $_.Exception.Response.StatusCode -eq 400) {
        Write-Host " Accessible ✓ (Erreur attendue sans payload)" -ForegroundColor Green
    } else {
        Write-Host " ERREUR: $_" -ForegroundColor Red
        Write-Host "    → Vérifiez que workflow 'Action Router' est ACTIF dans n8n UI" -ForegroundColor Yellow
        exit 1
    }
}

# ==================== ÉTAPE 4: Test Création Action Backend ====================
Write-Host "`n📋 ÉTAPE 4: Test création action via Backend..." -ForegroundColor Yellow

$testPayload = @{
    text = "Turn on the lamp in the living room"
    user_id = "test_user_powershell"
    language = "en"
} | ConvertTo-Json

Write-Host "  ✓ Envoi requête /command/text..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$BackendUrl/command/text" -Method POST `
        -ContentType "application/json" -Body $testPayload -TimeoutSec 30
    
    Write-Host " OK ✓" -ForegroundColor Green
    
    Write-Host "`n  📊 Résultat Backend:" -ForegroundColor Cyan
    Write-Host "    - Transcription: $($response.transcription)" -ForegroundColor White
    Write-Host "    - Response: $($response.response)" -ForegroundColor White
    
    if ($response.metadata) {
        Write-Host "    - Classification: $($response.metadata.classification)" -ForegroundColor White
        
        if ($response.metadata.action_id) {
            Write-Host "    - Action ID: $($response.metadata.action_id)" -ForegroundColor Green
            Write-Host "    - State: $($response.metadata.state)" -ForegroundColor Green
            
            $actionId = $response.metadata.action_id
            
            # ==================== ÉTAPE 5: Vérifier État Action ====================
            Write-Host "`n📋 ÉTAPE 5: Vérification état action..." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            
            try {
                $actionStatus = Invoke-RestMethod -Uri "$BackendUrl/action/status/$actionId" -Method GET
                Write-Host "  ✓ État action: $($actionStatus.current_state)" -ForegroundColor Green
                
                if ($actionStatus.current_state -eq "COMPLETED") {
                    Write-Host "`n✅ TEST RÉUSSI! Pipeline complet fonctionnel:" -ForegroundColor Green
                    Write-Host "  1. ✓ Backend a reçu la commande" -ForegroundColor Green
                    Write-Host "  2. ✓ Classification → ACTION détectée" -ForegroundColor Green
                    Write-Host "  3. ✓ ActionJSON créée" -ForegroundColor Green
                    Write-Host "  4. ✓ Envoi à n8n réussi" -ForegroundColor Green
                    Write-Host "  5. ✓ n8n a publié MQTT" -ForegroundColor Green
                    Write-Host "  6. ✓ Callback backend réussi" -ForegroundColor Green
                    Write-Host "  7. ✓ État final: COMPLETED" -ForegroundColor Green
                } elseif ($actionStatus.current_state -eq "PENDING_CONFIRMATION") {
                    Write-Host "`n⚠️  Action en attente de confirmation" -ForegroundColor Yellow
                    Write-Host "  → État: PENDING_CONFIRMATION" -ForegroundColor Yellow
                    Write-Host "  → Normal: l'utilisateur doit confirmer avec 'yes'" -ForegroundColor Cyan
                    Write-Host "`n  Pour tester la confirmation:" -ForegroundColor Cyan
                    Write-Host "    curl $BackendUrl/action/confirm/$actionId -X POST -H 'Content-Type: application/json' -d '{\"user_response\": \"yes\"}'" -ForegroundColor Gray
                } else {
                    Write-Host "`n⚠️  Action dans état: $($actionStatus.current_state)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  ✗ Erreur vérification action: $_" -ForegroundColor Red
            }
            
        } else {
            Write-Host "    - Type: Conversation (pas d'action créée)" -ForegroundColor Cyan
        }
    }
    
} catch {
    Write-Host " ERREUR: $_" -ForegroundColor Red
    Write-Host "    → Vérifiez que backend est lancé et accessible" -ForegroundColor Yellow
    exit 1
}

# ==================== RÉSUMÉ ====================
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "🎯 RÉSUMÉ DES TESTS" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

Write-Host "✅ Services opérationnels:" -ForegroundColor Green
Write-Host "  - Backend (port 8000)" -ForegroundColor White
Write-Host "  - n8n (port 5678)" -ForegroundColor White
Write-Host "  - MQTT Broker (port 1883)" -ForegroundColor White

Write-Host "`n📱 Configuration app mobile MQTT:" -ForegroundColor Cyan
Write-Host "  - Broker: localhost (ou votre IP locale: $(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*'} | Select-Object -First 1 -ExpandProperty IPAddress))" -ForegroundColor White
Write-Host "  - Port: 1883" -ForegroundColor White
Write-Host "  - Topic: gob/actions/+/command" -ForegroundColor White
Write-Host "  - QoS: 1" -ForegroundColor White

Write-Host "`n🚀 Prochaines étapes:" -ForegroundColor Yellow
Write-Host "  1. Configurer app mobile MQTT avec les paramètres ci-dessus" -ForegroundColor White
Write-Host "  2. Lancer frontend: cd agent-ui; npm run dev" -ForegroundColor White
Write-Host "  3. Tester avec voix: 'Turn on the lamp'" -ForegroundColor White
Write-Host "  4. Vérifier réception sur téléphone!" -ForegroundColor White

Write-Host "`n✨ Test terminé!" -ForegroundColor Green
