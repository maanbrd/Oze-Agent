-- Grant beta tester access to pawelwziontek94@gmail.com.
-- Idempotent: re-running keeps the row in active state with the original claim intact.

INSERT INTO beta_access_grants (email, status, note)
VALUES ('pawelwziontek94@gmail.com', 'active', 'Beta tester (22.05.2026)')
ON CONFLICT (email) DO UPDATE
    SET status = 'active',
        revoked_at = NULL,
        updated_at = NOW();
