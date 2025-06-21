# 🚨 Important: Development vs Production Commands

## Issue Resolution: Nginx Unhealthy Status

### **Root Cause:**
You were running the **production** docker-compose.yml which includes nginx, but you should be using the **development** configuration for testing.

### **✅ Fixed Issues:**

#### **1. Nginx Health Check Fixed:**
- Changed from `wget` (not available in nginx:alpine) 
- Now uses `pidof nginx` to check if nginx process is running
- Added proper start_period for container initialization

#### **2. Development vs Production Clarification:**

### **🔧 For Development (No Nginx):**
```bash
# Use development configuration (no nginx, direct access)
sudo docker-compose -f docker-compose.dev.yml up -d

# Access directly
http://your-server-ip:8501  # Streamlit UI
http://your-server-ip:8000  # API endpoints
```

### **🚀 For Production (With Nginx):**
```bash
# Use production configuration (with nginx reverse proxy)
sudo docker-compose up -d

# Access through nginx
http://your-server-ip        # Streamlit UI (via nginx)
http://your-server-ip/api/   # API endpoints (via nginx)
```

## **Recommended Workflow:**

### **Development Phase:**
```bash
# Stop any existing containers
sudo docker-compose -f docker-compose.dev.yml down
sudo docker-compose down

# Start development environment
sudo docker-compose -f docker-compose.dev.yml up --build -d

# Check status (should only see rag-app and redis)
sudo docker-compose -f docker-compose.dev.yml ps

# Test access
curl http://your-server-ip:8501  # Should work
curl http://your-server-ip:8000/health  # Should work
```

### **Production Deployment:**
```bash
# Stop development
sudo docker-compose -f docker-compose.dev.yml down

# Start production with nginx
sudo docker-compose up --build -d

# Check status (should see rag-app, redis, postgres, nginx)
sudo docker-compose ps

# Test access
curl http://your-server-ip/health  # Through nginx
curl http://your-server-ip:8501    # Direct to streamlit (bypassing nginx)
```

## **Key Differences:**

| Feature | Development | Production |
|---------|-------------|------------|
| Nginx | ❌ No | ✅ Yes |
| PostgreSQL | ❌ No | ✅ Yes |
| SSL Support | ❌ No | ✅ Yes |
| Direct Port Access | ✅ Yes | ⚠️ Limited |
| Hot Reload | ✅ Yes | ❌ No |
| Volume Mounting | ✅ Code mounted | ❌ Code copied |

## **Current Status Check:**
```bash
# Check which compose file you're using
sudo docker-compose ps  # Shows production services
sudo docker-compose -f docker-compose.dev.yml ps  # Shows dev services

# If you see nginx, you're running production
# If you only see rag-app and redis, you're running development
```

## **Next Steps:**

### **For Development Testing:**
```bash
sudo docker-compose down
sudo docker-compose -f docker-compose.dev.yml up --build -d
```

### **For Production Deployment:**
```bash
sudo docker-compose -f docker-compose.dev.yml down
sudo docker-compose up --build -d
```

The nginx health check is now fixed, but make sure you're using the right environment for your needs! 🎯
