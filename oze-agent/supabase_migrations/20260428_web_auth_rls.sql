-- Web Auth/RLS baseline for Agent-OZE.
-- Run after the original supabase_schema.sql.

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS auth_user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_users_auth_user_id
  ON public.users(auth_user_id)
  WHERE auth_user_id IS NOT NULL;

CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  display_name TEXT;
BEGIN
  display_name := NULLIF(
    TRIM(
      COALESCE(NEW.raw_user_meta_data->>'name', '') || ' ' ||
      COALESCE(NEW.raw_user_meta_data->>'first_name', '') || ' ' ||
      COALESCE(NEW.raw_user_meta_data->>'last_name', '')
    ),
    ''
  );

  INSERT INTO public.users (
    auth_user_id,
    email,
    name,
    phone,
    consent_terms,
    consent_marketing,
    consent_phone_contact
  )
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(display_name, SPLIT_PART(NEW.email, '@', 1), 'Użytkownik'),
    NULLIF(NEW.raw_user_meta_data->>'phone', ''),
    COALESCE((NEW.raw_user_meta_data->>'consent_terms')::BOOLEAN, FALSE),
    COALESCE((NEW.raw_user_meta_data->>'consent_marketing')::BOOLEAN, FALSE),
    COALESCE((NEW.raw_user_meta_data->>'consent_phone_contact')::BOOLEAN, FALSE)
  )
  ON CONFLICT (email) DO UPDATE
    SET auth_user_id = COALESCE(public.users.auth_user_id, EXCLUDED.auth_user_id),
        name = COALESCE(NULLIF(public.users.name, ''), EXCLUDED.name),
        phone = COALESCE(NULLIF(public.users.phone, ''), EXCLUDED.phone),
        updated_at = NOW()
    WHERE public.users.auth_user_id IS NULL
       OR public.users.auth_user_id = EXCLUDED.auth_user_id;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_select_own_profile" ON public.users;
CREATE POLICY "users_select_own_profile"
  ON public.users
  FOR SELECT
  TO authenticated
  USING (auth.uid() = auth_user_id);

-- No browser UPDATE/INSERT/DELETE policies are added here on purpose.
-- FastAPI uses the service key and must authorize every route from the
-- verified JWT subject before reading or mutating system state.
