#!/bin/bash

# Environment Configuration Verification Script
# This script checks if your .env file is properly configured

echo "🔍 Environment Configuration Verification"
echo "========================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with your API keys."
    exit 1
fi

echo "✅ .env file found"
echo ""

# Check .env file content
echo "📋 Checking .env file content..."
echo "================================"

# Function to check a variable
check_env_var() {
    local var_name=$1
    local var_value=$(grep "^${var_name}=" .env | cut -d'=' -f2-)
    
    if [ -z "$var_value" ]; then
        echo "❌ $var_name: Not found in .env file"
        return 1
    elif [[ "$var_value" == *"your_"* ]] || [[ "$var_value" == *"_here"* ]]; then
        echo "❌ $var_name: Contains placeholder text: $var_value"
        return 1
    elif [[ "$var_value" == \"*\" ]] || [[ "$var_value" == \'*\' ]]; then
        echo "⚠️  $var_name: Contains quotes (remove them): $var_value"
        return 1
    else
        # Mask the key for security
        local masked_value="${var_value:0:4}****${var_value: -4}"
        echo "✅ $var_name: $masked_value"
        return 0
    fi
}

# Check all required variables
echo "Required API Keys:"
check_env_var "COHERE_API_KEY"
cohere_ok=$?

check_env_var "GEMINI_API_KEY"
gemini_ok=$?

echo ""
echo "Optional Configuration:"
check_env_var "GEMINI_MODEL"
check_env_var "N8N_USER"
check_env_var "N8N_PASSWORD"
check_env_var "N8N_ENCRYPTION_KEY"
check_env_var "N8N_HOST"

echo ""
echo "📝 .env File Format Check:"
echo "========================="

# Check for common formatting issues
if grep -q "=" .env; then
    echo "✅ Uses proper KEY=VALUE format"
else
    echo "❌ Invalid format detected"
fi

if grep -q "^[[:space:]]*#" .env; then
    echo "✅ Comments found (lines starting with #)"
fi

if grep -q "^[[:space:]]*$" .env; then
    echo "✅ Contains blank lines (OK)"
fi

# Check for quotes
if grep -q "=" .env | grep -q '"'; then
    echo "⚠️  Found quotes in values - remove them for Docker compatibility"
fi

echo ""
echo "🎯 Summary:"
echo "==========="

if [ $cohere_ok -eq 0 ] && [ $gemini_ok -eq 0 ]; then
    echo "✅ Configuration looks good! Ready to deploy."
    echo ""
    echo "Next steps:"
    echo "1. Run: docker-compose up -d"
    echo "2. Monitor: docker-compose logs -f"
    echo "3. Verify: curl http://localhost:8000/health"
else
    echo "❌ Configuration issues detected!"
    echo ""
    echo "Please fix the following:"
    echo "1. Set your actual Cohere API key from https://dashboard.cohere.com/"
    echo "2. Set your actual Gemini API key from https://aistudio.google.com/"
    echo "3. Remove any quotes around the values"
    echo "4. Remove any placeholder text"
    echo ""
    echo "Example .env format:"
    echo "COHERE_API_KEY=co_1234567890abcdef"
    echo "GEMINI_API_KEY=AIza1234567890abcdef"
    echo "GEMINI_MODEL=gemini-2.5-flash-preview-04-17"
    exit 1
fi
