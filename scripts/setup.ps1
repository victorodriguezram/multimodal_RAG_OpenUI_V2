# Multimodal RAG System - Quick Setup Script (PowerShell)
# This script automates the deployment process on Windows

Write-Host "🔍 Multimodal RAG System - Docker Deployment Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check if Docker is installed
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✅ Docker is installed: $dockerVersion" -ForegroundColor Green
    } else {
        throw "Docker not found"
    }
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first:" -ForegroundColor Red
    Write-Host "   https://docs.docker.com/desktop/install/windows/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker Compose is installed
try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "✅ Docker Compose is installed: $composeVersion" -ForegroundColor Green
    } else {
        throw "Docker Compose not found"
    }
} catch {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Desktop which includes Docker Compose" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Please create it with your API keys:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "COHERE_API_KEY=your_actual_cohere_api_key_here"
    Write-Host "GEMINI_API_KEY=your_actual_gemini_api_key_here"
    Write-Host "GEMINI_MODEL=gemini-2.5-flash-preview-04-17"
    Write-Host "N8N_USER=admin"
    Write-Host "N8N_PASSWORD=your_secure_password_here"
    Write-Host "N8N_ENCRYPTION_KEY=your_secure_encryption_key_here"
    Write-Host "N8N_HOST=localhost"
    Write-Host ""
    Write-Host "Please create .env file and run this script again." -ForegroundColor Red
    exit 1
}

Write-Host "✅ .env file found" -ForegroundColor Green

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Blue
if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path "data" -Force | Out-Null }
if (-not (Test-Path "uploads")) { New-Item -ItemType Directory -Path "uploads" -Force | Out-Null }

# Build and start services
Write-Host "🚀 Building and starting services..." -ForegroundColor Blue
docker-compose down --remove-orphans
docker-compose pull
docker-compose build --no-cache
docker-compose up -d

# Wait for services to start
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Blue
Start-Sleep -Seconds 30

# Check service health
Write-Host "🔍 Checking service health..." -ForegroundColor Blue

# Check multimodal-rag service
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Multimodal RAG API is healthy" -ForegroundColor Green
    } else {
        Write-Host "❌ Multimodal RAG API returned status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Multimodal RAG API is not responding" -ForegroundColor Red
}

# Check Streamlit
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Streamlit UI is healthy" -ForegroundColor Green
    } else {
        Write-Host "❌ Streamlit UI returned status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Streamlit UI is not responding" -ForegroundColor Red
}

# Check N8N
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5678" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ N8N is healthy" -ForegroundColor Green
    } else {
        Write-Host "❌ N8N returned status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ N8N is not responding" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Access your applications:" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host "📊 Streamlit UI:        http://localhost:8501" -ForegroundColor White
Write-Host "🔗 API Documentation:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "🤖 N8N Automation:      http://localhost:5678" -ForegroundColor White
Write-Host ""

# Read credentials from .env file
if (Test-Path ".env") {
    $envContent = Get-Content ".env"
    $n8nUser = ($envContent | Where-Object { $_ -match "^N8N_USER=" }) -replace "^N8N_USER=", ""
    $n8nPassword = ($envContent | Where-Object { $_ -match "^N8N_PASSWORD=" }) -replace "^N8N_PASSWORD=", ""
    
    Write-Host "N8N Login Credentials:" -ForegroundColor Cyan
    Write-Host "Username: $n8nUser" -ForegroundColor White
    Write-Host "Password: $n8nPassword" -ForegroundColor White
}

Write-Host ""
Write-Host "🔧 Useful Commands:" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host "View logs:           docker-compose logs -f" -ForegroundColor White
Write-Host "Stop services:       docker-compose down" -ForegroundColor White
Write-Host "Restart services:    docker-compose restart" -ForegroundColor White
Write-Host "Check status:        docker-compose ps" -ForegroundColor White
Write-Host ""
Write-Host "📖 For detailed documentation, see README_DOCKER.md" -ForegroundColor Yellow
