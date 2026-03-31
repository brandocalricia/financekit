/*
  # Add theme and accent color to user settings

  1. Modified Tables
    - `user_settings`
      - `theme` (text, default 'dark') - light or dark mode preference
      - `accent_color` (text, default '#2dd4bf') - user's chosen accent color hex

  2. Important Notes
    - Non-destructive: only adds new columns
    - Existing rows get sensible defaults
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'user_settings' AND column_name = 'theme'
  ) THEN
    ALTER TABLE user_settings ADD COLUMN theme text NOT NULL DEFAULT 'dark';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'user_settings' AND column_name = 'accent_color'
  ) THEN
    ALTER TABLE user_settings ADD COLUMN accent_color text NOT NULL DEFAULT '#2dd4bf';
  END IF;
END $$;
