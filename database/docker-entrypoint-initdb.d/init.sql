-- Initialize extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean initialization)
DROP TABLE IF EXISTS requests;
DROP TABLE IF EXISTS users;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    proof_threshold INTEGER DEFAULT 100,
    total_proofs INTEGER DEFAULT 0,
    successful_proofs INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0
);

-- Create index on users table
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Create requests table
CREATE TABLE requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    model_type VARCHAR(255) NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    proof_generated BOOLEAN DEFAULT FALSE,
    proof_verified BOOLEAN,
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Create index on requests table
CREATE INDEX idx_requests_user_id ON requests(user_id);
CREATE INDEX idx_requests_created_at ON requests(created_at);

-- Create necessary functions
CREATE OR REPLACE FUNCTION update_user_success_rate()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.total_proofs > 0 THEN
        NEW.success_rate := (NEW.successful_proofs::FLOAT / NEW.total_proofs) * 100;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updating success rate
CREATE TRIGGER trigger_update_success_rate
    BEFORE INSERT OR UPDATE OF total_proofs, successful_proofs
    ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_user_success_rate();

-- Add some initial test data (optional, commented out by default)
/*
INSERT INTO users (username, email, password_hash, proof_threshold) VALUES
    ('test_user', 'test@example.com', 'your_hashed_password_here', 100),
    ('admin', 'admin@example.com', 'your_admin_hashed_password_here', 100);

INSERT INTO requests (user_id, model_type, image_path) VALUES
    (1, 'ResNet-18', '/path/to/test/image1.jpg'),
    (1, 'ResNet-34', '/path/to/test/image2.jpg'),
    (2, 'ResNet-18', '/path/to/test/image3.jpg');
*/

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anas;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anas;