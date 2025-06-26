#!/bin/bash

# Multimodal RAG System Deployment Script for Ubuntu Server
# This script sets up the complete production environment

set -e

echo "🚀 Starting Multimodal RAG System Deployment"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root. Use a regular user with sudo privileges."
    exit 1
fi

# Check Ubuntu version
if ! lsb_release -d | grep -q "Ubuntu"; then
    print_warning "This script is designed for Ubuntu. Other distributions may not work correctly."
fi

print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

print_status "Installing required system packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    poppler-utils \
    nginx \
    certbot \
    python3-certbot-nginx

# Install Docker
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    print_status "Docker installed successfully"
else
    print_status "Docker is already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose is already installed"
fi

# Create application directory
APP_DIR="/opt/multimodal-rag"
print_status "Creating application directory at $APP_DIR..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
print_status "Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Create data directories
print_status "Creating data directories..."
mkdir -p data/{uploads,faiss_indices,previews,logs}
mkdir -p logs/{api,ui,worker,nginx}

# Set up environment file
if [ ! -f .env ]; then
    print_status "Creating environment file..."
    cp .env.example .env
    
    # Generate secure secrets
    API_SECRET_KEY=$(openssl rand -hex 32)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    GRAFANA_PASSWORD=$(openssl rand -hex 16)
    N8N_WEBHOOK_SECRET=$(openssl rand -hex 16)
    
    # Update .env file
    sed -i "s/your_very_secure_secret_key_here_change_this/$API_SECRET_KEY/" .env
    sed -i "s/multimodal_rag_secure_password_change_this/$REDIS_PASSWORD/" .env
    sed -i "s/secure_postgres_password_change_this/$POSTGRES_PASSWORD/" .env
    sed -i "s/admin_secure_password_change_this/$GRAFANA_PASSWORD/" .env
    sed -i "s/n8n_webhook_secret_change_this/$N8N_WEBHOOK_SECRET/" .env
    
    print_warning "Please edit .env file and add your API keys:"
    print_warning "- COHERE_API_KEY"
    print_warning "- GEMINI_API_KEY"
    
    echo
    read -p "Press Enter after you have configured the API keys..."
fi

# Create SSL directory
print_status "Creating SSL directory..."
sudo mkdir -p /etc/nginx/ssl
sudo chown $USER:$USER /etc/nginx/ssl

# Generate self-signed certificate for testing (replace with real certificate for production)
if [ ! -f /etc/nginx/ssl/cert.pem ]; then
    print_status "Generating self-signed SSL certificate for testing..."
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/key.pem \
        -out /etc/nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Set up log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/multimodal-rag > /dev/null <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f $APP_DIR/docker-compose.yml restart nginx
    endscript
}
EOF

# Create systemd service for auto-start
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/multimodal-rag.service > /dev/null <<EOF
[Unit]
Description=Multimodal RAG System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/docker-compose -f $APP_DIR/docker-compose.yml up -d
ExecStop=/usr/local/bin/docker-compose -f $APP_DIR/docker-compose.yml down
WorkingDirectory=$APP_DIR
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable multimodal-rag.service

# Set up firewall
print_status "Configuring UFW firewall..."
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Build and start services
print_status "Building and starting services..."
docker-compose build
docker-compose up -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 30

# Health check
print_status "Performing health checks..."
for i in {1..10}; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        print_status "Services are healthy!"
        break
    else
        print_warning "Waiting for services to be ready... (attempt $i/10)"
        sleep 10
    fi
done

# Display status
print_status "Deployment completed!"
echo
echo "🎉 Multimodal RAG System has been deployed successfully!"
echo
echo "📊 Service URLs:"
echo "  - Main UI: http://localhost (or your server IP)"
echo "  - API Documentation: http://localhost/api/docs"
echo "  - Grafana Monitoring: http://localhost:3000"
echo "  - Prometheus Metrics: http://localhost:9090"
echo
echo "🔧 Management Commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Start services: docker-compose up -d"
echo "  - View status: docker-compose ps"
echo
echo "🔐 Generated Passwords (saved in .env file):"
echo "  - Check .env file for database and service passwords"
echo
echo "⚠️  Important Notes:"
echo "  1. Replace self-signed SSL certificate with real certificate for production"
echo "  2. Configure your domain name in nginx configuration"
echo "  3. Set up regular backups for data directory"
echo "  4. Monitor logs regularly"
echo
print_status "Deployment script completed successfully!"
