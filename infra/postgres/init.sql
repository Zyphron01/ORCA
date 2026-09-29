-- ORCA PostgreSQL Initialization Script
-- Runs once when the PostgreSQL container is first created.

-- Enable PostGIS spatial extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector for embedding storage (Phase 4+)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Verify PostGIS
SELECT PostGIS_Full_Version();
