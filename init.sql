CREATE SCHEMA IF NOT EXISTS agents;

CREATE TABLE IF NOT EXISTS agents.log_analysis (
  id SERIAL PRIMARY KEY,
  alert_file TEXT,
  alert_id TEXT,
  alert_type TEXT,
  timestamp TIMESTAMPTZ,
  alert_description TEXT,
  sop_matches JSONB,
  similar_incidents JSONB,
  rca_output TEXT,
  recommendation_output TEXT,
  confidence_score FLOAT,
  decision_output JSONB,
  inserted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
