-- Initialize database schema for RAG system
-- This file is executed when PostgreSQL container starts for the first time

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)

-- Create documents table for metadata storage
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    page_count INTEGER,
    processed BOOLEAN DEFAULT FALSE,
    embedding_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create embeddings metadata table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL, -- 'text' or 'image'
    page_number INTEGER,
    chunk_index INTEGER,
    faiss_index_position INTEGER,
    preview_path VARCHAR(500),
    content_preview TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user sessions table (for future user management)
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Create search queries table for analytics
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    query_text TEXT NOT NULL,
    results_count INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed);
CREATE INDEX IF NOT EXISTS idx_embeddings_document_id ON embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_content_type ON embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_session_id ON search_queries(session_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_created_at ON search_queries(created_at);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some initial data for testing (optional)
-- Uncomment the following lines if you want sample data

-- INSERT INTO documents (filename, content_type, file_size, page_count, processed) 
-- VALUES ('sample.pdf', 'application/pdf', 1024000, 5, true);

COMMENT ON TABLE documents IS 'Stores metadata about uploaded documents';
COMMENT ON TABLE embeddings IS 'Stores metadata about generated embeddings';
COMMENT ON TABLE user_sessions IS 'Tracks user sessions for analytics';
COMMENT ON TABLE search_queries IS 'Logs search queries for analytics and improvements';
