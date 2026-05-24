-- Grant beta tester access to lukaszfathi97@gmail.com.
-- Idempotent: re-running keeps the row in active state with the original claim intact.

INSERT INTO beta_access_grants (email, status, note)
VALUES ('lukaszfathi97@gmail.com', 'active', 'moje konto beta testerskie')
ON CONFLICT (email) DO UPDATE
    SET status = 'active',
        revoked_at = NULL,
        updated_at = NOW();
