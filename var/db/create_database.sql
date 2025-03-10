CREATE USER fastapitemplateuser WITH PASSWORD fastapitemplatepassword;
CREATE DATABASE fastapitemplatedb WITH OWNER fastapitemplateuser;
ALTER ROLE fastapitemplateuser SET client_encoding to 'utf-8';
ALTER ROLE fastapitemplateuser SET default_transaction_isolation TO 'read committed';
ALTER USER fastapitemplateuser createdb;
GRANT ALL PRIVILEGES on DATABASE fastapitemplatedb TO fastapitemplateuser;