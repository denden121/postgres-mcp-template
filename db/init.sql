BEGIN;
REVOKE ALL ON DATABASE sales FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
CREATE ROLE data_owner NOLOGIN;
CREATE ROLE mcp_reader LOGIN PASSWORD 'local_reader_demo'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
GRANT CONNECT ON DATABASE sales TO mcp_reader;
ALTER ROLE mcp_reader SET statement_timeout = '2s';
ALTER ROLE mcp_reader SET default_transaction_read_only = on;
CREATE SCHEMA private AUTHORIZATION data_owner;
CREATE SCHEMA api AUTHORIZATION data_owner;
SET ROLE data_owner;
CREATE TABLE private.sales (
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sold_on date NOT NULL,
  product text NOT NULL,
  amount numeric(12,2) NOT NULL,
  customer_email text NOT NULL
);
INSERT INTO private.sales(sold_on, product, amount, customer_email) VALUES
 ('2026-10-01','Python',1000,'alice@example.test'),
 ('2026-10-02','SQL',1500,'bob@example.test'),
 ('2026-10-03','Python',1000,'carol@example.test'),
 ('2026-10-04','JavaScript',2000,'dave@example.test');
CREATE FUNCTION api.sales_summary(date, date)
RETURNS TABLE(orders bigint, revenue numeric)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
BEGIN
 IF $1 IS NULL OR $2 IS NULL OR $2 < $1 OR $2 - $1 > 90 THEN
   RAISE EXCEPTION 'Invalid date range';
 END IF;
 RETURN QUERY SELECT count(*), coalesce(sum(s.amount),0)
 FROM private.sales s WHERE s.sold_on BETWEEN $1 AND $2;
END $$;
CREATE FUNCTION api.top_products(date, date, integer)
RETURNS TABLE(product text, revenue numeric)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
BEGIN
 IF $1 IS NULL OR $2 IS NULL OR $2 < $1 OR $2 - $1 > 90
 OR $3 IS NULL OR $3 < 1 OR $3 > 10 THEN
   RAISE EXCEPTION 'Invalid parameters';
 END IF;
 RETURN QUERY SELECT s.product, sum(s.amount) AS revenue
 FROM private.sales s WHERE s.sold_on BETWEEN $1 AND $2
 GROUP BY s.product ORDER BY revenue DESC, s.product LIMIT $3;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA api FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA api REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
GRANT USAGE ON SCHEMA api TO mcp_reader;
GRANT EXECUTE ON FUNCTION api.sales_summary(date,date), api.top_products(date,date,integer) TO mcp_reader;
RESET ROLE;
COMMIT;
