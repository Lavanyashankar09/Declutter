-- Database schema brainstorm
-- TODO: normalize the permissions table, it's getting unwieldy
-- TODO: add indexes on frequently queried columns
-- FIXME: the created_at default doesn't account for timezone properly

-- NOTE: DB migration scheduled for Saturday Feb 15 2025 at 11pm
--       during maintenance window. Coordinate with on-call.

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    created_at TIMESTAMP DEFAULT NOW(),  -- FIXME: should be TIMESTAMPTZ
    updated_at TIMESTAMP DEFAULT NOW()
);

-- TODO: add soft delete support (deleted_at column)
-- TODO: add audit log table for compliance

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT
);

-- Quick thought: should we use RBAC or ABAC for permissions?
-- RBAC is simpler and fits our current needs.
-- Revisit if we need attribute-based rules later.
-- Schedule a decision review for this by end of Q1.

CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER REFERENCES roles(id),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL  -- TODO: enum type instead?
);
