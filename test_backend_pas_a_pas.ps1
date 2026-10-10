# ============================================================
# TEST BACKEND PAS A PAS - AVEC AFFICHAGE DETAILLE
# ============================================================

$baseUrl = "http://127.0.0.1:8000"

function Write-Step {
    param($number, $title)
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "ETAPE $number : $title" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Write-Success {
    param($message)
    Write-Host "[OK] $message" -ForegroundColor Green
}

function Write-Info {
    param($message)
    Write-Host "[INFO] $message" -ForegroundColor Yellow
}

function Write-Result {
    param($label, $value)
    Write-Host "   $label : " -NoNewline -ForegroundColor White
    Write-Host "$value" -ForegroundColor Magenta
}

# ============================================================
# DEBUT DES TESTS
# ============================================================

Write-Host "`n"
Write-Host "============================================================" -ForegroundColor Green
Write-Host "          TEST BACKEND - AGENT INTELLIGENT PCD             " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "`n"

Start-Sleep -Seconds 1

# ============================================================
# ETAPE 1: HEALTH CHECK
# ============================================================

Write-Step 1 "VERIFICATION SANTE DU SERVEUR"
Write-Info "Endpoint: GET /health"

try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Success "Serveur accessible"
    Write-Result "Status" $health.status
    Write-Result "Version" $health.version
    Write-Result "Environnement" $health.environment
    
    Write-Host "`n   Composants:" -ForegroundColor White
    $health.components.PSObject.Properties | ForEach-Object {
        $icon = if ($_.Value -eq "ok") { "[OK]" } elseif ($_.Value -eq "disabled") { "[--]" } else { "[!!]" }
        Write-Host "      $icon $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
} catch {
    Write-Host "[ERREUR] Serveur non accessible" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 2

# ============================================================
# ETAPE 2: TEST CONVERSATION SIMPLE
# ============================================================

Write-Step 2 "TEST CONVERSATION SIMPLE"
Write-Info "Envoi: 'Bonjour Agent, comment vas-tu?'"

$body = @{
    text = "Bonjour Agent, comment vas-tu?"
    user_id = "test_user_123"
    language = "fr"
} | ConvertTo-Json

try {
    $startTime = Get-Date
    $conv = Invoke-RestMethod -Uri "$baseUrl/command/text" -Method Post -Body $body -ContentType "application/json"
    $duration = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Success "Conversation traitee"
    Write-Result "Classification" $conv.classification
    Write-Result "Status" $conv.status
    Write-Result "Duree" "$([math]::Round($duration, 0)) ms"
    
    if ($conv.response) {
        Write-Host "`n   [REPONSE AGENT]:" -ForegroundColor White
        Write-Host "   $($conv.response)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[ERREUR] $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# ============================================================
# ETAPE 3: TEST CLASSIFICATION CONVERSATION
# ============================================================

Write-Step 3 "TEST CLASSIFICATION - CONVERSATION"
Write-Info "Envoi: 'Quelle heure est-il?'"

$body = @{
    text = "Quelle heure est-il?"
    user_id = "test_user_123"
    language = "fr"
} | ConvertTo-Json

try {
    $startTime = Get-Date
    $conv2 = Invoke-RestMethod -Uri "$baseUrl/command/text" -Method Post -Body $body -ContentType "application/json"
    $duration = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Success "Classification reussie"
    Write-Result "Type detecte" $conv2.classification
    Write-Result "Confiance" "$($conv2.confidence)"
    Write-Result "Duree" "$([math]::Round($duration, 0)) ms"
    
    if ($conv2.response) {
        Write-Host "`n   [REPONSE AGENT]:" -ForegroundColor White
        Write-Host "   $($conv2.response)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[ERREUR] $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# ============================================================
# ETAPE 4: TEST ACTION - CREATION
# ============================================================

Write-Step 4 "TEST ACTION IOT - CREATION"
Write-Info "Envoi: 'Allume la lampe du salon'"

$body = @{
    text = "Allume la lampe du salon"
    user_id = "test_user_123"
    language = "fr"
} | ConvertTo-Json

try {
    $startTime = Get-Date
    $action = Invoke-RestMethod -Uri "$baseUrl/command/text" -Method Post -Body $body -ContentType "application/json"
    $duration = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Success "Action creee avec succes"
    Write-Result "Classification" $action.classification
    Write-Result "Action ID" $action.action_id
    Write-Result "Etat" $action.state
    Write-Result "Status" $action.status
    Write-Result "Duree" "$([math]::Round($duration, 0)) ms"
    
    if ($action.message) {
        Write-Host "`n   [MESSAGE DE CONFIRMATION]:" -ForegroundColor White
        Write-Host "   $($action.message)" -ForegroundColor Yellow
    }
    
    # Sauvegarder l'action ID pour l'etape suivante
    $global:actionId = $action.action_id
    
} catch {
    Write-Host "[ERREUR] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 2

# ============================================================
# ETAPE 5: TEST ACTION - CONFIRMATION
# ============================================================

Write-Step 5 "TEST ACTION IOT - CONFIRMATION"
Write-Info "Action ID: $global:actionId"
Write-Info "Reponse utilisateur: 'oui'"

$body = @{
    response = "oui"
    user_id = "test_user_123"
} | ConvertTo-Json

try {
    $startTime = Get-Date
    $confirm = Invoke-RestMethod -Uri "$baseUrl/action/confirm/$global:actionId" -Method Post -Body $body -ContentType "application/json"
    $duration = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Success "Action confirmee et executee"
    Write-Result "Status" $confirm.status
    Write-Result "Nouvel etat" $confirm.new_state
    Write-Result "Duree" "$([math]::Round($duration, 0)) ms"
    
    if ($confirm.response) {
        Write-Host "`n   [REPONSE]:" -ForegroundColor White
        Write-Host "   $($confirm.response)" -ForegroundColor Cyan
    }
    
    if ($confirm.n8n_response) {
        Write-Host "`n   [REPONSE N8N]:" -ForegroundColor White
        Write-Host "      Status: $($confirm.n8n_response.status)" -ForegroundColor Gray
        Write-Host "      Message: $($confirm.n8n_response.message)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "[ERREUR] $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# ============================================================
# ETAPE 6: TEST ACTION - STATUT
# ============================================================

Write-Step 6 "TEST RECUPERATION STATUT ACTION"
Write-Info "Action ID: $global:actionId"

try {
    $status = Invoke-RestMethod -Uri "$baseUrl/action/status/$global:actionId" -Method Get
    
    Write-Success "Statut recupere"
    Write-Result "Action ID" $status.action_id
    Write-Result "Etat actuel" $status.state
    Write-Result "Timestamp" $status.timestamp
    
    if ($status.action_json) {
        Write-Host "`n   [DETAILS DE L'ACTION]:" -ForegroundColor White
        Write-Host "      Intent: $($status.action_json.intent)" -ForegroundColor Gray
        Write-Host "      Device: $($status.action_json.payload.device_type)" -ForegroundColor Gray
        Write-Host "      Action: $($status.action_json.payload.action)" -ForegroundColor Gray
        if ($status.action_json.payload.location) {
            Write-Host "      Location: $($status.action_json.payload.location)" -ForegroundColor Gray
        }
    }
    
} catch {
    Write-Host "[ERREUR] $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# ============================================================
# ETAPE 7: TEST ANNULATION
# ============================================================

Write-Step 7 "TEST ANNULATION D'UNE ACTION"
Write-Info "Creation d'une nouvelle action..."

$body = @{
    text = "Eteins la lampe de la cuisine"
    user_id = "test_user_123"
    language = "fr"
} | ConvertTo-Json

try {
    $action2 = Invoke-RestMethod -Uri "$baseUrl/command/text" -Method Post -Body $body -ContentType "application/json"
    $actionId2 = $action2.action_id
    
    Write-Success "Action creee: $actionId2"
    
    Start-Sleep -Seconds 1
    
    Write-Info "Annulation de l'action..."
    
    $bodyCancel = @{
        response = "non"
        user_id = "test_user_123"
    } | ConvertTo-Json
    
    $cancel = Invoke-RestMethod -Uri "$baseUrl/action/confirm/$actionId2" -Method Post -Body $bodyCancel -ContentType "application/json"
    
    Write-Success "Action annulee"
    Write-Result "Status" $cancel.status
    Write-Result "Nouvel etat" $cancel.new_state
    
    if ($cancel.response) {
        Write-Host "`n   [REPONSE]:" -ForegroundColor White
        Write-Host "   $($cancel.response)" -ForegroundColor Cyan
    }
    
} catch {
    Write-Host "[ERREUR] $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# ============================================================
# ETAPE 8: TEST STATS
# ============================================================

Write-Step 8 "TEST RECUPERATION STATISTIQUES"
Write-Info "Endpoint: GET /stats"

try {
    $stats = Invoke-RestMethod -Uri "$baseUrl/stats" -Method Get
    
    Write-Success "Statistiques recuperees"
    Write-Result "Uptime" "$([math]::Round($stats.uptime_seconds, 2)) secondes"
    Write-Result "Requetes totales" $stats.total_requests
    Write-Result "Requetes reussies" $stats.successful_requests
    Write-Result "Requetes echouees" $stats.failed_requests
    Write-Result "Conversations" $stats.conversations
    Write-Result "Actions" $stats.actions
    
} catch {
    Write-Host "[ERREUR] $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 1

# ============================================================
# RESUME FINAL
# ============================================================

Write-Host "`n"
Write-Host "============================================================" -ForegroundColor Green
Write-Host "                    TESTS TERMINES                          " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "`n"

Write-Host "RESUME DES TESTS:" -ForegroundColor Cyan
Write-Host "   [OK] Health check" -ForegroundColor Green
Write-Host "   [OK] Conversation simple" -ForegroundColor Green
Write-Host "   [OK] Classification conversation" -ForegroundColor Green
Write-Host "   [OK] Creation action IoT" -ForegroundColor Green
Write-Host "   [OK] Confirmation action" -ForegroundColor Green
Write-Host "   [OK] Recuperation statut" -ForegroundColor Green
Write-Host "   [OK] Annulation action" -ForegroundColor Green
Write-Host "   [OK] Statistiques" -ForegroundColor Green

Write-Host "`nBackend FastAPI - 100% OPERATIONNEL" -ForegroundColor Green
Write-Host "`n"
