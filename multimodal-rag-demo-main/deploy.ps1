# Production deployment script for Windows PowerShell
# This script automates the deployment process on Windows systems

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("development", "production")]
    [string]$DeploymentType = "development"
)

# Color functions for PowerShell
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info { Write-ColorOutput "✓ $args" "Blue" }
function Write-Success { Write-ColorOutput "✓ $args" "Green" }
function Write-Warning { Write-ColorOutput "⚠ $args" "Yellow" }
function Write-Error { Write-ColorOutput "✗ $args" "Red" }

Write-ColorOutput "🚀 Starting Multimodal RAG System Deployment" "Cyan"
Write-ColorOutput "==============================================" "Cyan"

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed. Please install Docker Desktop for Windows first."
    Write-Info "Download from: https://www.docker.com/products/docker-desktop"
    exit 1
} else {
    Write-Success "Docker is installed"
}

# Check if Docker Compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Error "Docker Compose is not available. Please ensure Docker Desktop is properly installed."
    exit 1
} else {
    Write-Success "Docker Compose is available"
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Success "Docker is running"
} catch {
    Write-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.template") {
        Write-Info "Creating .env file from template..."
        Copy-Item ".env.template" ".env"
        Write-Warning "Please edit .env file with your actual API keys before continuing"
        Write-Warning "Required: COHERE_API_KEY and GEMINI_API_KEY"
        
        $continue = Read-Host "Have you configured your API keys in .env file? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-Error "Please configure your API keys in .env file and run this script again"
            exit 1
        }
    } else {
        Write-Error ".env file not found and no template available"
        exit 1
    }
}

# Validate environment file
Write-Info "Validating environment configuration..."
$envContent = Get-Content ".env" | Where-Object { $_ -match "^[^#].*=" }
$envVars = @{}
foreach ($line in $envContent) {
    $key, $value = $line -split "=", 2
    $envVars[$key] = $value
}

if (-not $envVars["COHERE_API_KEY"] -or $envVars["COHERE_API_KEY"] -eq "your_cohere_api_key_here") {
    Write-Error "COHERE_API_KEY is not configured in .env file"
    exit 1
}

if (-not $envVars["GEMINI_API_KEY"] -or $envVars["GEMINI_API_KEY"] -eq "your_gemini_api_key_here") {
    Write-Error "GEMINI_API_KEY is not configured in .env file"
    exit 1
}

Write-Success "Environment configuration validated"

# Choose deployment type if not specified
if (-not $DeploymentType) {
    Write-Host "`nSelect deployment type:"
    Write-Host "1) Development (with hot reload)"
    Write-Host "2) Production (with nginx, postgres, redis)"
    $choice = Read-Host "Enter your choice (1-2)"
    
    switch ($choice) {
        "1" { $DeploymentType = "development" }
        "2" { $DeploymentType = "production" }
        default {
            Write-Error "Invalid choice"
            exit 1
        }
    }
}

# Set compose file based on deployment type
if ($DeploymentType -eq "development") {
    $ComposeFile = "docker-compose.dev.yml"
} else {
    $ComposeFile = "docker-compose.yml"
}

Write-Info "Starting $DeploymentType deployment..."

# Pull latest images
Write-Info "Pulling Docker images..."
docker-compose -f $ComposeFile pull

# Build custom images
Write-Info "Building application images..."
docker-compose -f $ComposeFile build

# Start services
Write-Info "Starting services..."
docker-compose -f $ComposeFile up -d

# Wait for services to be ready
Write-Info "Waiting for services to be ready..."
Start-Sleep -Seconds 30

# Health checks
Write-Info "Performing health checks..."

# Check if containers are running
$containerStatus = docker-compose -f $ComposeFile ps
if ($containerStatus -notmatch "Up") {
    Write-Error "Some containers failed to start"
    docker-compose -f $ComposeFile logs
    exit 1
}

# Check application health
$maxAttempts = 10
$attempt = 1

while ($attempt -le $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Application is healthy and responding"
            break
        }
    } catch {
        Write-Info "Waiting for application to be ready... (attempt $attempt/$maxAttempts)"
        Start-Sleep -Seconds 10
        $attempt++
    }
}

if ($attempt -gt $maxAttempts) {
    Write-Error "Application failed to become healthy"
    Write-Info "Checking logs..."
    docker-compose -f $ComposeFile logs rag-app
    exit 1
}

# Additional health checks for production
if ($DeploymentType -eq "production") {
    # Check PostgreSQL
    try {
        docker-compose exec -T postgres pg_isready -U raguser | Out-Null
        Write-Success "PostgreSQL is ready"
    } catch {
        Write-Warning "PostgreSQL health check failed"
    }
    
    # Check Redis
    try {
        $redisResponse = docker-compose exec -T redis redis-cli ping
        if ($redisResponse -match "PONG") {
            Write-Success "Redis is ready"
        } else {
            Write-Warning "Redis health check failed"
        }
    } catch {
        Write-Warning "Redis health check failed"
    }
    
    # Check Nginx
    try {
        $response = Invoke-WebRequest -Uri "http://localhost/health" -TimeoutSec 5 -ErrorAction Stop
        Write-Success "Nginx is ready"
    } catch {
        Write-Warning "Nginx health check failed"
    }
}

# Display deployment information
Write-Host ""
Write-ColorOutput "🎉 Deployment completed successfully!" "Green"
Write-ColorOutput "======================================" "Green"
Write-Host ""
Write-Host "Application URL: http://localhost:8501"

if ($DeploymentType -eq "production") {
    Write-Host "Reverse Proxy URL: http://localhost"
    Write-Host ""
    Write-Host "Service Endpoints:"
    Write-Host "  - Application: http://localhost:8501"
    Write-Host "  - PostgreSQL: localhost:5432"
    Write-Host "  - Redis: localhost:6379"
    Write-Host "  - Nginx: http://localhost"
}

Write-Host ""
Write-Host "Management Commands:"
Write-Host "  - View logs: docker-compose -f $ComposeFile logs -f"
Write-Host "  - Stop services: docker-compose -f $ComposeFile down"
Write-Host "  - Restart services: docker-compose -f $ComposeFile restart"
Write-Host "  - View status: docker-compose -f $ComposeFile ps"

Write-Host ""
Write-Host "Data Locations:"
Write-Host "  - FAISS indices: Docker volume 'rag_data'"
Write-Host "  - Uploaded files: Docker volume 'rag_uploads'"
if ($DeploymentType -eq "production") {
    Write-Host "  - Database: Docker volume 'postgres_data'"
    Write-Host "  - Redis cache: Docker volume 'redis_data'"
}

Write-Host ""
Write-Host "Next Steps:"
Write-Host "1. Upload some PDF documents to test the system"
Write-Host "2. Try searching for content in the uploaded documents"
Write-Host "3. Monitor logs for any issues: docker-compose -f $ComposeFile logs -f"

if ($DeploymentType -eq "production") {
    Write-Host "4. Configure SSL certificates for production use"
    Write-Host "5. Set up monitoring and backup procedures"
}

Write-Host ""
Write-Success "Deployment script completed successfully!"

# Show running containers
Write-Host ""
Write-Info "Currently running containers:"
docker-compose -f $ComposeFile ps
