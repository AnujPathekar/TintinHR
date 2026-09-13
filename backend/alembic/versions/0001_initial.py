"""Initial TintinHR schema."""
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE TYPE user_role AS ENUM ('EMPLOYEE','MANAGER','HR','ADMIN')")
    op.execute("CREATE TYPE document_visibility AS ENUM ('PUBLIC','EMPLOYEE','MANAGER','HR','ADMIN')")
    op.execute("CREATE TYPE document_status AS ENUM ('PENDING','PROCESSING','ACTIVE','FAILED','ARCHIVED')")
    op.execute("CREATE TYPE message_role AS ENUM ('USER','ASSISTANT')")
    op.execute("""
    CREATE TABLE users (
      id UUID PRIMARY KEY, email VARCHAR(320) UNIQUE NOT NULL, full_name VARCHAR(200) NOT NULL,
      password_hash VARCHAR(500) NOT NULL, role user_role NOT NULL DEFAULT 'EMPLOYEE',
      is_active BOOLEAN NOT NULL DEFAULT TRUE, authz_version INTEGER NOT NULL DEFAULT 1,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
    );
    CREATE INDEX ix_users_email ON users(email);
    CREATE TABLE departments (
      id UUID PRIMARY KEY, name VARCHAR(120) UNIQUE NOT NULL, code VARCHAR(30) UNIQUE NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
    );
    CREATE TABLE employees (
      id UUID PRIMARY KEY, user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      employee_code VARCHAR(40) UNIQUE NOT NULL, department_id UUID REFERENCES departments(id),
      manager_id UUID REFERENCES employees(id), joining_date DATE NOT NULL, job_title VARCHAR(150) NOT NULL,
      location VARCHAR(120) NOT NULL DEFAULT 'Bengaluru', created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
    );
    CREATE INDEX ix_employees_employee_code ON employees(employee_code);
    CREATE TABLE leave_balances (
      id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
      leave_type VARCHAR(80) NOT NULL, year INTEGER NOT NULL, allocated FLOAT NOT NULL,
      used FLOAT NOT NULL DEFAULT 0, pending FLOAT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_leave_employee_type_year UNIQUE(employee_id, leave_type, year)
    );
    CREATE INDEX ix_leave_balances_employee_id ON leave_balances(employee_id);
    CREATE TABLE leave_requests (
      id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
      leave_type VARCHAR(80) NOT NULL, start_date DATE NOT NULL, end_date DATE NOT NULL,
      days FLOAT NOT NULL, status VARCHAR(30) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
    );
    CREATE TABLE holidays (
      id UUID PRIMARY KEY, name VARCHAR(150) NOT NULL, holiday_date DATE NOT NULL,
      location VARCHAR(120), is_optional BOOLEAN NOT NULL DEFAULT FALSE
    );
    CREATE TABLE documents (
      id UUID PRIMARY KEY, title VARCHAR(250) NOT NULL, description TEXT, filename VARCHAR(300) NOT NULL,
      mime_type VARCHAR(120) NOT NULL, sha256 VARCHAR(64) NOT NULL, visibility document_visibility NOT NULL,
      department_id UUID REFERENCES departments(id), status document_status NOT NULL,
      current_version INTEGER NOT NULL DEFAULT 1, corpus_version INTEGER NOT NULL DEFAULT 1,
      valid_from DATE, valid_until DATE, uploaded_by UUID NOT NULL REFERENCES users(id), failure_reason TEXT,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
    );
    CREATE INDEX ix_documents_sha256 ON documents(sha256);
    CREATE INDEX ix_documents_department_id ON documents(department_id);
    CREATE TABLE document_versions (
      id UUID PRIMARY KEY, document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
      version INTEGER NOT NULL, storage_path VARCHAR(500) NOT NULL, sha256 VARCHAR(64) NOT NULL,
      size_bytes INTEGER NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_document_version UNIQUE(document_id, version)
    );
    CREATE TABLE document_chunks (
      id UUID PRIMARY KEY, document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
      version INTEGER NOT NULL, chunk_index INTEGER NOT NULL, page_number INTEGER, section VARCHAR(250),
      content TEXT NOT NULL, token_count INTEGER NOT NULL, metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
      search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
      embedding VECTOR(384) NOT NULL
    );
    CREATE INDEX ix_chunks_fts ON document_chunks USING gin(search_vector);
    CREATE INDEX ix_chunks_embedding ON document_chunks USING hnsw(embedding vector_cosine_ops);
    CREATE TABLE conversations (
      id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      title VARCHAR(200) NOT NULL DEFAULT 'New conversation', created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
    );
    CREATE TABLE messages (
      id UUID PRIMARY KEY, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
      role message_role NOT NULL, content TEXT NOT NULL, citations JSONB NOT NULL DEFAULT '[]'::jsonb,
      trace JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL
    );
    CREATE TABLE audit_events (
      id UUID PRIMARY KEY, actor_user_id UUID REFERENCES users(id), action VARCHAR(120) NOT NULL,
      resource_type VARCHAR(120) NOT NULL, resource_id VARCHAR(100), details JSONB NOT NULL DEFAULT '{}'::jsonb,
      ip_address VARCHAR(64), created_at TIMESTAMPTZ NOT NULL
    );
    CREATE INDEX ix_audit_events_created_at ON audit_events(created_at);
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS audit_events, messages, conversations, document_chunks, document_versions,
      documents, holidays, leave_requests, leave_balances, employees, departments, users CASCADE;
    DROP TYPE IF EXISTS message_role, document_status, document_visibility, user_role;
    """)

