#!/usr/bin/env python3
"""Test script to verify Cohere ClientV2 functionality"""

import sys
import os

# Set environment variables
os.environ['COHERE_API_KEY'] = 'test-key'
os.environ['GOOGLE_API_KEY'] = 'test-key'

try:
    from core.embeddings import co_client
    print('✓ Successfully imported cohere ClientV2')
    print(f'Client type: {type(co_client)}')
    
    # Test if embed method exists
    print(f'Has embed method: {hasattr(co_client, "embed")}')
    
    # Check cohere version
    import cohere
    print(f'Cohere version: {cohere.__version__}')
    
    # Test ClientV2 type
    print(f'Is ClientV2: {isinstance(co_client, cohere.ClientV2)}')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
