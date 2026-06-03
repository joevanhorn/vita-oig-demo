-- ==============================================================================
-- OKTA GENERIC DATABASE CONNECTOR - "HR SYSTEM" SCHEMA (VITA OIG PREVIEW)
-- ==============================================================================
-- PostgreSQL schema backing the demo HR System for the Okta Generic Database
-- Connector. Supports:
--   - User provisioning (create, update, deactivate)
--   - Entitlement management (assign, revoke)
--   - User import to Okta
--
-- Seed data models Virginia commonwealth agency employees.
-- ==============================================================================

-- ==============================================================================
-- USERS TABLE
-- ==============================================================================
-- Core HR employee table. Maps to Okta user profile attributes.

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(100) UNIQUE NOT NULL,  -- Unique identifier (maps to Okta externalId)
    username        VARCHAR(100) UNIQUE NOT NULL,  -- Login username
    email           VARCHAR(255) UNIQUE NOT NULL,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    display_name    VARCHAR(200),
    department      VARCHAR(100),                  -- Commonwealth agency
    title           VARCHAR(100),
    manager_id      VARCHAR(100),                  -- References another user's user_id
    employee_number VARCHAR(50),
    phone           VARCHAR(50),
    mobile_phone    VARCHAR(50),
    status          VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, INACTIVE, SUSPENDED
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deactivated_at  TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);

-- ==============================================================================
-- ENTITLEMENTS TABLE
-- ==============================================================================
-- Available entitlements/roles that can be assigned to users

CREATE TABLE IF NOT EXISTS entitlements (
    id              SERIAL PRIMARY KEY,
    entitlement_id  VARCHAR(100) UNIQUE NOT NULL,  -- Unique identifier for Okta
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    category        VARCHAR(100),                   -- e.g., 'Application', 'Role', 'Permission'
    risk_level      VARCHAR(20) DEFAULT 'LOW',      -- LOW, MEDIUM, HIGH, CRITICAL
    owner           VARCHAR(100),                   -- Owner email or ID
    status          VARCHAR(20) DEFAULT 'ACTIVE',   -- ACTIVE, DEPRECATED
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entitlements_category ON entitlements(category);
CREATE INDEX IF NOT EXISTS idx_entitlements_status ON entitlements(status);

-- ==============================================================================
-- USER_ENTITLEMENTS TABLE (Junction)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS user_entitlements (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(100) NOT NULL,         -- References users.user_id
    entitlement_id  VARCHAR(100) NOT NULL,         -- References entitlements.entitlement_id
    granted_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by      VARCHAR(100),
    expires_at      TIMESTAMP,
    status          VARCHAR(20) DEFAULT 'ACTIVE',   -- ACTIVE, REVOKED
    revoked_at      TIMESTAMP,
    revoked_by      VARCHAR(100),
    UNIQUE(user_id, entitlement_id)
);

CREATE INDEX IF NOT EXISTS idx_user_entitlements_user ON user_entitlements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_entitlements_entitlement ON user_entitlements(entitlement_id);
CREATE INDEX IF NOT EXISTS idx_user_entitlements_status ON user_entitlements(status);

-- ==============================================================================
-- GROUPS TABLE (Optional)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS groups (
    id              SERIAL PRIMARY KEY,
    group_id        VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    group_type      VARCHAR(50) DEFAULT 'STANDARD', -- STANDARD, DYNAMIC
    status          VARCHAR(20) DEFAULT 'ACTIVE',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- USER_GROUPS TABLE (Junction)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS user_groups (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(100) NOT NULL,
    group_id        VARCHAR(100) NOT NULL,
    added_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by        VARCHAR(100),
    UNIQUE(user_id, group_id)
);

CREATE INDEX IF NOT EXISTS idx_user_groups_user ON user_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_group ON user_groups(group_id);

-- ==============================================================================
-- AUDIT LOG TABLE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id              SERIAL PRIMARY KEY,
    operation       VARCHAR(50) NOT NULL,          -- CREATE, UPDATE, DELETE, ASSIGN, REVOKE
    entity_type     VARCHAR(50) NOT NULL,          -- USER, ENTITLEMENT, GROUP
    entity_id       VARCHAR(100) NOT NULL,
    old_values      JSONB,
    new_values      JSONB,
    performed_by    VARCHAR(100),
    performed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source          VARCHAR(50) DEFAULT 'OKTA'     -- OKTA, MANUAL, SYSTEM
);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_performed_at ON audit_log(performed_at);

-- ==============================================================================
-- TRIGGER FOR UPDATED_AT
-- ==============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_entitlements_updated_at ON entitlements;
CREATE TRIGGER update_entitlements_updated_at
    BEFORE UPDATE ON entitlements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- SEED DATA - ENTITLEMENTS (HR System roles & application access)
-- ==============================================================================

INSERT INTO entitlements (entitlement_id, name, description, category, risk_level) VALUES
    ('ent-hr-employee',     'HR Employee Self-Service', 'View and update own HR records (Cardinal HCM self-service)', 'Application', 'LOW'),
    ('ent-hr-manager',      'HR Manager',               'Approve time, view direct-report records',                   'Role',        'MEDIUM'),
    ('ent-hr-specialist',   'HR Specialist',            'Maintain employee records for an agency',                    'Role',        'HIGH'),
    ('ent-hr-admin',        'HR Administrator',         'Full administration of the HR System',                       'Role',        'CRITICAL'),
    ('ent-payroll-view',    'Payroll Viewer',           'View payroll registers and pay history',                     'Application', 'MEDIUM'),
    ('ent-payroll-process', 'Payroll Processor',        'Run payroll cycles and adjustments',                         'Application', 'HIGH'),
    ('ent-benefits-admin',  'Benefits Administrator',   'Manage health and retirement benefit enrollments',           'Application', 'HIGH'),
    ('ent-recruiting',      'Recruiting (PageUp)',      'Post requisitions and manage applicants',                    'Application', 'MEDIUM'),
    ('ent-reporting',       'Workforce Reporting',      'Access workforce analytics and reporting',                   'Role',        'LOW'),
    ('ent-timekeeping',     'Timekeeping Approver',     'Approve timesheets and leave requests',                      'Permission',  'MEDIUM')
ON CONFLICT (entitlement_id) DO NOTHING;

-- ==============================================================================
-- SEED DATA - USERS (Virginia commonwealth agency employees)
-- ==============================================================================

INSERT INTO users (user_id, username, email, first_name, last_name, display_name, department, title, employee_number, status) VALUES
    ('emp-1001', 'rwhitfield', 'robert.whitfield@vita.virginia.gov',  'Robert',  'Whitfield', 'Robert Whitfield', 'VITA',  'Director of Workforce Systems', 'E1001', 'ACTIVE'),
    ('emp-1002', 'lnguyen',    'linda.nguyen@vita.virginia.gov',      'Linda',   'Nguyen',    'Linda Nguyen',     'VITA',  'HR Business Partner',           'E1002', 'ACTIVE'),
    ('emp-1003', 'dcarter',    'david.carter@dmv.virginia.gov',       'David',   'Carter',    'David Carter',     'DMV',   'Payroll Manager',               'E1003', 'ACTIVE'),
    ('emp-1004', 'mreyes',     'maria.reyes@dmv.virginia.gov',        'Maria',   'Reyes',     'Maria Reyes',      'DMV',   'HR Specialist',                 'E1004', 'ACTIVE'),
    ('emp-1005', 'jthompson',  'james.thompson@vdot.virginia.gov',    'James',   'Thompson',  'James Thompson',   'VDOT',  'Benefits Administrator',        'E1005', 'ACTIVE'),
    ('emp-1006', 'sokafor',    'sarah.okafor@vdot.virginia.gov',      'Sarah',   'Okafor',    'Sarah Okafor',     'VDOT',  'District HR Manager',           'E1006', 'ACTIVE'),
    ('emp-1007', 'bmartin',    'brian.martin@dss.virginia.gov',       'Brian',   'Martin',    'Brian Martin',     'DSS',   'Recruiting Coordinator',        'E1007', 'ACTIVE'),
    ('emp-1008', 'kpatel',     'kavita.patel@dss.virginia.gov',       'Kavita',  'Patel',     'Kavita Patel',     'DSS',   'Timekeeping Supervisor',        'E1008', 'ACTIVE'),
    ('emp-1009', 'gfoster',    'gregory.foster@vdh.virginia.gov',     'Gregory', 'Foster',    'Gregory Foster',   'VDH',   'Workforce Analyst',             'E1009', 'ACTIVE'),
    ('emp-1010', 'achen',      'amy.chen@vdh.virginia.gov',           'Amy',     'Chen',      'Amy Chen',         'VDH',   'HR Administrator',              'E1010', 'ACTIVE')
ON CONFLICT (user_id) DO NOTHING;

-- Manager relationships
UPDATE users SET manager_id = 'emp-1001' WHERE user_id IN ('emp-1002');
UPDATE users SET manager_id = 'emp-1003' WHERE user_id IN ('emp-1004');
UPDATE users SET manager_id = 'emp-1006' WHERE user_id IN ('emp-1005');
UPDATE users SET manager_id = 'emp-1010' WHERE user_id IN ('emp-1009');

-- Entitlement assignments
INSERT INTO user_entitlements (user_id, entitlement_id, granted_by) VALUES
    ('emp-1001', 'ent-hr-admin',        'system'),
    ('emp-1001', 'ent-reporting',       'system'),
    ('emp-1002', 'ent-hr-specialist',   'system'),
    ('emp-1002', 'ent-recruiting',      'system'),
    ('emp-1003', 'ent-payroll-process', 'system'),
    ('emp-1003', 'ent-payroll-view',    'system'),
    ('emp-1004', 'ent-hr-specialist',   'system'),
    ('emp-1005', 'ent-benefits-admin',  'system'),
    ('emp-1006', 'ent-hr-manager',      'system'),
    ('emp-1006', 'ent-timekeeping',     'system'),
    ('emp-1007', 'ent-recruiting',      'system'),
    ('emp-1008', 'ent-timekeeping',     'system'),
    ('emp-1009', 'ent-reporting',       'system'),
    ('emp-1010', 'ent-hr-admin',        'system')
ON CONFLICT (user_id, entitlement_id) DO NOTHING;

-- ==============================================================================
-- VIEWS FOR OKTA CONNECTOR
-- ==============================================================================

CREATE OR REPLACE VIEW v_users_with_entitlements AS
SELECT
    u.user_id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.display_name,
    u.department,
    u.title,
    u.status,
    COUNT(ue.id) as entitlement_count,
    ARRAY_AGG(e.name) FILTER (WHERE e.name IS NOT NULL) as entitlement_names
FROM users u
LEFT JOIN user_entitlements ue ON u.user_id = ue.user_id AND ue.status = 'ACTIVE'
LEFT JOIN entitlements e ON ue.entitlement_id = e.entitlement_id
GROUP BY u.id, u.user_id, u.username, u.email, u.first_name, u.last_name,
         u.display_name, u.department, u.title, u.status;

CREATE OR REPLACE VIEW v_active_entitlements AS
SELECT
    e.entitlement_id,
    e.name,
    e.description,
    e.category,
    e.risk_level,
    COUNT(ue.id) as assigned_users
FROM entitlements e
LEFT JOIN user_entitlements ue ON e.entitlement_id = ue.entitlement_id AND ue.status = 'ACTIVE'
WHERE e.status = 'ACTIVE'
GROUP BY e.id, e.entitlement_id, e.name, e.description, e.category, e.risk_level;

-- ==============================================================================
-- STORED PROCEDURES FOR OKTA CONNECTOR
-- ==============================================================================

CREATE OR REPLACE FUNCTION create_user(
    p_user_id VARCHAR(100),
    p_username VARCHAR(100),
    p_email VARCHAR(255),
    p_first_name VARCHAR(100),
    p_last_name VARCHAR(100),
    p_department VARCHAR(100) DEFAULT NULL,
    p_title VARCHAR(100) DEFAULT NULL
) RETURNS VARCHAR(100) AS $$
BEGIN
    INSERT INTO users (user_id, username, email, first_name, last_name, department, title, status)
    VALUES (p_user_id, p_username, p_email, p_first_name, p_last_name, p_department, p_title, 'ACTIVE');

    INSERT INTO audit_log (operation, entity_type, entity_id, new_values, performed_by, source)
    VALUES ('CREATE', 'USER', p_user_id,
            jsonb_build_object('username', p_username, 'email', p_email),
            'okta', 'OKTA');

    RETURN p_user_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_user(
    p_user_id VARCHAR(100),
    p_email VARCHAR(255) DEFAULT NULL,
    p_first_name VARCHAR(100) DEFAULT NULL,
    p_last_name VARCHAR(100) DEFAULT NULL,
    p_department VARCHAR(100) DEFAULT NULL,
    p_title VARCHAR(100) DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_old_values JSONB;
BEGIN
    SELECT jsonb_build_object('email', email, 'first_name', first_name, 'last_name', last_name)
    INTO v_old_values FROM users WHERE user_id = p_user_id;

    UPDATE users SET
        email = COALESCE(p_email, email),
        first_name = COALESCE(p_first_name, first_name),
        last_name = COALESCE(p_last_name, last_name),
        department = COALESCE(p_department, department),
        title = COALESCE(p_title, title)
    WHERE user_id = p_user_id;

    INSERT INTO audit_log (operation, entity_type, entity_id, old_values, performed_by, source)
    VALUES ('UPDATE', 'USER', p_user_id, v_old_values, 'okta', 'OKTA');

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION deactivate_user(p_user_id VARCHAR(100)) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE users SET
        status = 'INACTIVE',
        deactivated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;

    UPDATE user_entitlements SET
        status = 'REVOKED',
        revoked_at = CURRENT_TIMESTAMP,
        revoked_by = 'okta'
    WHERE user_id = p_user_id AND status = 'ACTIVE';

    INSERT INTO audit_log (operation, entity_type, entity_id, performed_by, source)
    VALUES ('DEACTIVATE', 'USER', p_user_id, 'okta', 'OKTA');

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION assign_entitlement(
    p_user_id VARCHAR(100),
    p_entitlement_id VARCHAR(100)
) RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO user_entitlements (user_id, entitlement_id, granted_by, status)
    VALUES (p_user_id, p_entitlement_id, 'okta', 'ACTIVE')
    ON CONFLICT (user_id, entitlement_id)
    DO UPDATE SET status = 'ACTIVE', granted_at = CURRENT_TIMESTAMP, revoked_at = NULL;

    INSERT INTO audit_log (operation, entity_type, entity_id, new_values, performed_by, source)
    VALUES ('ASSIGN', 'ENTITLEMENT', p_entitlement_id,
            jsonb_build_object('user_id', p_user_id),
            'okta', 'OKTA');

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION revoke_entitlement(
    p_user_id VARCHAR(100),
    p_entitlement_id VARCHAR(100)
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE user_entitlements SET
        status = 'REVOKED',
        revoked_at = CURRENT_TIMESTAMP,
        revoked_by = 'okta'
    WHERE user_id = p_user_id AND entitlement_id = p_entitlement_id;

    INSERT INTO audit_log (operation, entity_type, entity_id, old_values, performed_by, source)
    VALUES ('REVOKE', 'ENTITLEMENT', p_entitlement_id,
            jsonb_build_object('user_id', p_user_id),
            'okta', 'OKTA');

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- VERIFICATION QUERIES (run manually to confirm)
-- ==============================================================================
-- SELECT COUNT(*) AS user_count FROM users;
-- SELECT COUNT(*) AS entitlement_count FROM entitlements;
-- SELECT * FROM v_users_with_entitlements;
-- SELECT * FROM v_active_entitlements;
