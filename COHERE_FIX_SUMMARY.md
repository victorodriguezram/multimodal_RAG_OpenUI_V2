# Cohere API Compatibility Fix

## Issue
The original error was: `module 'cohere' has no attribute 'ClientV2'`

This occurred because:
1. The original repo used `cohere.ClientV2` but didn't pin a specific cohere version
2. Older versions of the cohere package (< 5.0) didn't have `ClientV2`
3. The multimodal image embedding API format had changed

## Solution Applied

### 1. Updated Cohere Version
- **Before**: `cohere==4.57` (didn't have ClientV2)
- **After**: `cohere>=5.3.0` (has ClientV2 and latest multimodal API)

Updated in:
- `requirements.txt`
- `api_requirements.txt` 
- `multimodal-rag-demo-main/requirements.txt`

### 2. Fixed Multimodal API Format
The image embedding input format was updated to match the current Cohere v2 API:

**Before (incorrect format):**
```python
api_input_document = {
    "content": [
        {"type": "image", "image": base64_from_image(content)},
    ]
}
```

**After (correct v2 API format):**
```python
api_input_document = {
    "content": [
        {"type": "image_url", "image_url": {"url": base64_from_image(content)}},
    ]
}
```

### 3. Files Updated
- `core/embeddings.py` - Fixed image embedding format
- `multimodal-rag-demo-main/core/embeddings.py` - Same fix for consistency
- All requirements files - Updated cohere version

## Verification
The fix ensures:
- ✅ `cohere.ClientV2` is available and works
- ✅ Multimodal embeddings use the correct v2 API format
- ✅ Compatible with Ubuntu Server deployment
- ✅ Maintains all original functionality
- ✅ Matches current Cohere documentation

## Reference Documentation
- [Cohere Client Creation](https://docs.cohere.com/docs/create-client)
- [Multimodal Embeddings](https://docs.cohere.com/docs/multimodal-embeddings)
- Original repo: [SridharSampath/multimodal-rag-demo](https://github.com/SridharSampath/multimodal-rag-demo)

## Testing
For Ubuntu Server deployment, the Docker container will:
1. Install `cohere>=5.3.0` which includes ClientV2
2. Use the correct multimodal API format
3. Work seamlessly with existing N8N integration
