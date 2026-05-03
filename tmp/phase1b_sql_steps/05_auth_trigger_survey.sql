CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  display_name TEXT;
  survey JSONB;
BEGIN
  display_name := NULLIF(
    TRIM(
      COALESCE(NEW.raw_user_meta_data->>'name', '') || ' ' ||
      COALESCE(NEW.raw_user_meta_data->>'first_name', '') || ' ' ||
      COALESCE(NEW.raw_user_meta_data->>'last_name', '')
    ),
    ''
  );

  survey := COALESCE(NEW.raw_user_meta_data->'onboarding_survey', '{}'::jsonb);

  INSERT INTO public.users (
    auth_user_id,
    email,
    name,
    phone,
    referral_source,
    onboarding_survey,
    consent_terms,
    consent_marketing,
    consent_phone_contact
  )
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(display_name, SPLIT_PART(NEW.email, '@', 1), 'Użytkownik'),
    NULLIF(NEW.raw_user_meta_data->>'phone', ''),
    NULLIF(COALESCE(survey->>'referral_source', NEW.raw_user_meta_data->>'referral_source'), ''),
    survey,
    COALESCE((NEW.raw_user_meta_data->>'consent_terms')::BOOLEAN, FALSE),
    COALESCE((NEW.raw_user_meta_data->>'consent_marketing')::BOOLEAN, FALSE),
    COALESCE((NEW.raw_user_meta_data->>'consent_phone_contact')::BOOLEAN, FALSE)
  )
  ON CONFLICT (email) DO UPDATE
    SET auth_user_id = COALESCE(public.users.auth_user_id, EXCLUDED.auth_user_id),
        name = COALESCE(NULLIF(public.users.name, ''), EXCLUDED.name),
        phone = COALESCE(NULLIF(public.users.phone, ''), EXCLUDED.phone),
        referral_source = COALESCE(public.users.referral_source, EXCLUDED.referral_source),
        onboarding_survey = CASE
          WHEN public.users.onboarding_survey IS NULL
            OR public.users.onboarding_survey = '{}'::jsonb
          THEN EXCLUDED.onboarding_survey
          ELSE public.users.onboarding_survey
        END,
        updated_at = NOW()
    WHERE public.users.auth_user_id IS NULL
       OR public.users.auth_user_id = EXCLUDED.auth_user_id;

  RETURN NEW;
END;
$$;
