\set ON_ERROR_STOP on

\if :{?sandi_app}
\else
\echo 'Jalankan dengan -v sandi_app="''...''". Sandi tidak pernah ditulis di berkas ini.'
\quit 1
\endif

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hk_app') THEN
        CREATE ROLE hk_app LOGIN;
    END IF;
END
$$;

ALTER ROLE hk_app WITH PASSWORD :sandi_app;

REVOKE ALL ON SCHEMA public FROM hk_app;
GRANT USAGE ON SCHEMA public TO hk_app;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM hk_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hk_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hk_app;

