-- =============================================================
-- MonTour — PostgreSQL Row Level Security (RLS) Policies
-- Script SQL d'activation RLS pour environnement de production PostgreSQL
-- =============================================================

-- 1. Activer RLS sur toutes les tables MonTour
ALTER TABLE mt_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE mt_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE mt_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE mt_chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE mt_fcm_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE mt_queues ENABLE ROW LEVEL SECURITY;
ALTER TABLE mt_services ENABLE ROW LEVEL SECURITY;

-- =============================================================
-- 2. POLICIES: mt_users
-- =============================================================
-- Les utilisateurs peuvent voir et modifier leur propre profil
CREATE POLICY user_read_own_profile ON mt_users
    FOR SELECT
    USING (id = current_setting('request.jwt.claim.user_id', true)::uuid OR current_setting('request.jwt.claim.role', true) = 'admin');

CREATE POLICY user_update_own_profile ON mt_users
    FOR UPDATE
    USING (id = current_setting('request.jwt.claim.user_id', true)::uuid OR current_setting('request.jwt.claim.role', true) = 'admin');

-- =============================================================
-- 3. POLICIES: mt_tickets
-- =============================================================
-- Lecture : Le propriétaire du ticket, les agents et les administrateurs
CREATE POLICY ticket_read_policy ON mt_tickets
    FOR SELECT
    USING (
        user_id = current_setting('request.jwt.claim.user_id', true)::uuid
        OR current_setting('request.jwt.claim.role', true) IN ('agent', 'admin')
    );

-- Insertion : L'utilisateur pour lui-même
CREATE POLICY ticket_insert_policy ON mt_tickets
    FOR INSERT
    WITH CHECK (user_id = current_setting('request.jwt.claim.user_id', true)::uuid);

-- Mise à jour : L'utilisateur (pour annuler/noter) ou agents/admins (pour appeler/servir)
CREATE POLICY ticket_update_policy ON mt_tickets
    FOR UPDATE
    USING (
        user_id = current_setting('request.jwt.claim.user_id', true)::uuid
        OR current_setting('request.jwt.claim.role', true) IN ('agent', 'admin')
    );

-- =============================================================
-- 4. POLICIES: mt_notifications
-- =============================================================
-- RLS stricte: Seul le destinataire peut lire/modifier/supprimer ses notifications
CREATE POLICY notification_owner_all ON mt_notifications
    FOR ALL
    USING (user_id = current_setting('request.jwt.claim.user_id', true)::uuid);

-- =============================================================
-- 5. POLICIES: mt_chat_messages
-- =============================================================
-- RLS stricte: Seul l'utilisateur peut voir et gérer ses conversations chatbot
CREATE POLICY chat_owner_all ON mt_chat_messages
    FOR ALL
    USING (user_id = current_setting('request.jwt.claim.user_id', true)::uuid);

-- =============================================================
-- 6. POLICIES: mt_fcm_tokens
-- =============================================================
-- RLS stricte: Seul l'utilisateur peut gérer ses jetons de notification push
CREATE POLICY fcm_owner_all ON mt_fcm_tokens
    FOR ALL
    USING (user_id = current_setting('request.jwt.claim.user_id', true)::uuid);

-- =============================================================
-- 7. POLICIES: mt_services & mt_queues
-- =============================================================
-- Lecture publique/authentifiée pour tous les services et files
CREATE POLICY services_read_all ON mt_services
    FOR SELECT
    USING (is_active = true OR current_setting('request.jwt.claim.role', true) = 'admin');

CREATE POLICY queues_read_all ON mt_queues
    FOR SELECT
    USING (true);

-- Modification réservée aux admins et agents
CREATE POLICY services_admin_write ON mt_services
    FOR ALL
    USING (current_setting('request.jwt.claim.role', true) = 'admin');

CREATE POLICY queues_agent_admin_write ON mt_queues
    FOR ALL
    USING (current_setting('request.jwt.claim.role', true) IN ('agent', 'admin'));
