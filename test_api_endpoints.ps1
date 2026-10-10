# ==============================================================================
# Script de Test des Endpoints API Backend
# ==============================================================================

$baseUrl = "http://127.0.0.1:8000"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "🧪 TEST DES ENDPOINTS API - BACKEND PYTHON" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# ==============================================================================
# TEST 1: Health Check
# ==============================================================================
Write-Host "[1/6] 🏥 Test Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✅ Status: $($response.status)" -ForegroundColor Green
    Write-Host "   Version: $($response.version)" -ForegroundColor Gray
    Write-Host "   Environment: $($response.environment)" -ForegroundColor Gray
    Write-Host "   Components:" -ForegroundColor Gray
    $response.components.PSObject.Properties | ForEach-Object {
        $icon = if ($_.Value -eq "ok") { "✅" } elseif ($_.Value -eq "disabled") { "⚪" } else { "⚠️" }
        Write-Host "     $icon $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
    Write-Host ""
} catch {
    Write-Host "❌ Erreur: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# ==============================================================================
# TEST 2: Root Endpoint
# ==============================================================================
Write-Host "[2/6] 📋 Test Root Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method GET
    Write-Host "✅ API Name: $($response.name)" -ForegroundColor Green
    Write-Host "   Version: $($response.version)" -ForegroundColor Gray
    Write-Host "   Documentation: $($response.documentation)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Erreur: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# ==============================================================================
# TEST 3: Commande Textuelle - Conversation
# ==============================================================================
Write-Host "[3/6] 💬 Test Commande Textuelle (Conversation)..." -ForegroundColor Yellow
try {
    $body = @{
        text = "Bonjour, comment vas-tu ?"
        user_id = "user_test_001"
        language = "fr"
        source = "powershell_test"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/command/text" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    Write-Host "✅ Classification: $($response.classification)" -ForegroundColor Green
    Write-Host "   Request ID: $($response.request_id)" -ForegroundColor Gray
    Write-Host "   Status: $($response.response.status)" -ForegroundColor Gray
    Write-Host "   Réponse: $($response.response.response)" -ForegroundColor Cyan
    Write-Host "   Processing time: $($response.processing_time_ms)ms" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Erreur: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "   Détail: $($errorDetail.detail)" -ForegroundColor Red
    }
    Write-Host ""
}

# ==============================================================================
# TEST 4: Commande Textuelle - Action IoT
# ==============================================================================
Write-Host "[4/6] 🏠 Test Commande Textuelle (Action IoT)..." -ForegroundColor Yellow
try {
    $body = @{
        text = "Allume la lampe du salon"
        user_id = "user_test_001"
        language = "fr"
        source = "powershell_test"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/command/text" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    Write-Host "✅ Classification: $($response.classification)" -ForegroundColor Green
    Write-Host "   Request ID: $($response.request_id)" -ForegroundColor Gray
    Write-Host "   Action ID: $($response.action_id)" -ForegroundColor Yellow
    Write-Host "   Status: $($response.status)" -ForegroundColor Gray
    Write-Host "   State: $($response.state)" -ForegroundColor Gray
    Write-Host "   Message: $($response.message)" -ForegroundColor Cyan
    Write-Host "   Processing time: $($response.processing_time_ms)ms" -ForegroundColor Gray
    
    # Sauvegarder l'action_id pour le test suivant
    $global:lastActionId = $response.action_id
    Write-Host ""
} catch {
    Write-Host "❌ Erreur: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "   Détail: $($errorDetail.detail)" -ForegroundColor Red
    }
    Write-Host ""
}

# ==============================================================================
# TEST 5: Confirmation Action (si action créée)
# ==============================================================================
if ($global:lastActionId) {
    Write-Host "[5/6] ✅ Test Confirmation Action..." -ForegroundColor Yellow
    try {
        $body = @{
            response = "oui"
            user_id = "user_test_001"
        } | ConvertTo-Json

        $confirmResponse = Invoke-RestMethod -Uri "$baseUrl/action/confirm/$global:lastActionId" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body

        Write-Host "✅ Confirmation Status: $($confirmResponse.status)" -ForegroundColor Green
        Write-Host "   Action ID: $($confirmResponse.action_id)" -ForegroundColor Gray
        Write-Host "   State: $($confirmResponse.state)" -ForegroundColor Gray
        Write-Host "   Response: $($confirmResponse.response)" -ForegroundColor Cyan
        Write-Host ""
    } catch {
        Write-Host "❌ Erreur: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Détail: $($errorDetail.detail)" -ForegroundColor Red
        }
        Write-Host ""
    }

    # ==============================================================================
    # TEST 6: Status Action
    # ==============================================================================
    Write-Host "[6/6] 📊 Test Status Action..." -ForegroundColor Yellow
    try {
        $statusResponse = Invoke-RestMethod -Uri "$baseUrl/action/status/$global:lastActionId" `
            -Method GET

        Write-Host "✅ Action trouvée" -ForegroundColor Green
        Write-Host "   Action ID: $($statusResponse.action_id)" -ForegroundColor Gray
        Write-Host "   State: $($statusResponse.current_state)" -ForegroundColor Yellow
        Write-Host "   Created: $($statusResponse.action_data.created_at)" -ForegroundColor Gray
        Write-Host "   Updated: $($statusResponse.action_data.updated_at)" -ForegroundColor Gray
        Write-Host "   History:" -ForegroundColor Gray
        $statusResponse.state_history | ForEach-Object {
            Write-Host "     - $($_.state) ($($_.timestamp))" -ForegroundColor Gray
        }
        Write-Host ""
    } catch {
        Write-Host "❌ Erreur: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
} else {
    Write-Host "[5/6] ⏭️  Test Confirmation - Skipped (pas d'action créée)" -ForegroundColor Gray
    Write-Host "[6/6] ⏭️  Test Status - Skipped (pas d'action créée)" -ForegroundColor Gray
    Write-Host ""
}

# ==============================================================================
# RÉSUMÉ
# ==============================================================================
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "✅ TESTS TERMINÉS" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 Documentation complète: $baseUrl/docs" -ForegroundColor Cyan
Write-Host "📊 Statistics: $baseUrl/stats" -ForegroundColor Cyan
Write-Host ""
