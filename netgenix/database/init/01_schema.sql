-- NetGenix TimescaleDB Schema
-- Network: LTZIM LTE (341 eNodeBs, 2,046 cells)
-- KPI Source: Huawei iMaster MAE-Evaluation GUI exports

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ─────────────────────────────────────────────────────────────────────────────
-- Cell-level KPI table (hypertable)
-- Covers all 30 KPI columns from the Cell Level KPIs export
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kpi_cell (
    -- Time dimension (partition key)
    time                            TIMESTAMPTZ     NOT NULL,

    -- Identity
    enodeb_name                     TEXT            NOT NULL,
    cell_name                       TEXT            NOT NULL,
    local_cell_id                   INTEGER,
    enodeb_function_name            TEXT,
    cell_fdd_tdd                    TEXT,

    -- Availability & Integrity
    integrity                       TEXT,
    radio_net_availability_rate     REAL,

    -- Access KPIs
    rrc_setup_success_rate_all      REAL,
    rrc_setup_success_rate_service  REAL,
    rrc_setup_success_rate_signal   REAL,
    erab_setup_success_rate         REAL,

    -- Retainability
    call_drop_rate                  REAL,

    -- Mobility
    ho_success_rate_intra_freq      REAL,
    ho_success_rate_s1              REAL,

    -- Paging
    paging_transfer_success_rate    REAL,

    -- Traffic volume
    total_traffic_gbit              REAL,
    dl_traffic_volume_gbit          REAL,
    ul_traffic_volume_gbit          REAL,
    l_traffic_user_avg              REAL,
    l_traffic_user_max              REAL,

    -- Throughput
    user_dl_pdcp_avg_throughput     REAL,
    user_ul_pdcp_avg_throughput     REAL,

    -- Quality
    dl_ibler                        REAL,
    ul_ibler                        REAL,
    dl_retrans_rate                 REAL,
    dl_packet_loss_rate             REAL,
    ul_packet_loss_rate             REAL,

    -- Resource utilisation
    dl_prb_usage_rate               REAL,
    ul_prb_usage_rate               REAL,
    pucch_usage_rate                REAL,
    pdcch_cce_usage_rate            REAL,

    -- Modulation / channel quality
    average_cqi                     REAL,
    average_pdsch_mcs               REAL,

    -- Latency
    data_access_time_ms             REAL,

    -- Unavailability
    total_cell_unavail_duration_s   REAL,

    -- Metadata
    granularity                     TEXT            NOT NULL DEFAULT 'daily',  -- 'daily' | 'hourly'
    data_source                     TEXT            NOT NULL DEFAULT 'csv',    -- 'csv' | 'mae_bot'

    -- Idempotent upsert key
    CONSTRAINT kpi_cell_unique UNIQUE (time, cell_name, granularity)
);

SELECT create_hypertable(
    'kpi_cell',
    'time',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

-- Indexes optimised for the two most common query patterns:
--   1. "Give me recent KPIs for site X"
--   2. "Give me the history for cell Y"
CREATE INDEX IF NOT EXISTS idx_kpi_cell_enodeb_time
    ON kpi_cell (enodeb_name, time DESC);

CREATE INDEX IF NOT EXISTS idx_kpi_cell_cell_time
    ON kpi_cell (cell_name, time DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- Whole-network aggregate KPI table (plain table — not a hypertable)
-- Source: Whole Network Main KPIs export (30 columns, no cell identity)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kpi_network (
    time                            TIMESTAMPTZ     NOT NULL,
    network_label                   TEXT            NOT NULL DEFAULT 'LTZIM',

    integrity                       TEXT,
    radio_net_availability_rate     REAL,
    rrc_setup_success_rate_all      REAL,
    rrc_setup_success_rate_service  REAL,
    rrc_setup_success_rate_signal   REAL,
    erab_setup_success_rate         REAL,
    call_drop_rate                  REAL,
    ho_success_rate_intra_freq      REAL,
    ho_success_rate_s1              REAL,
    l_traffic_user_avg              REAL,
    l_traffic_user_max              REAL,
    dl_traffic_volume_gbit          REAL,
    ul_traffic_volume_gbit          REAL,
    total_traffic_gbit              REAL,
    user_dl_pdcp_avg_throughput     REAL,
    user_ul_pdcp_avg_throughput     REAL,
    paging_transfer_success_rate    REAL,
    dl_ibler                        REAL,
    ul_ibler                        REAL,
    dl_retrans_rate                 REAL,
    dl_packet_loss_rate             REAL,
    ul_packet_loss_rate             REAL,
    dl_prb_usage_rate               REAL,
    ul_prb_usage_rate               REAL,
    pucch_usage_rate                REAL,
    pdcch_cce_usage_rate            REAL,
    average_cqi                     REAL,
    average_pdsch_mcs               REAL,

    granularity                     TEXT            NOT NULL DEFAULT 'daily',
    data_source                     TEXT            NOT NULL DEFAULT 'csv',

    CONSTRAINT kpi_network_unique UNIQUE (time, granularity)
);

CREATE INDEX IF NOT EXISTS idx_kpi_network_time
    ON kpi_network (time DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- Ingestion audit log — track each CSV / bot run
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingestion_log (
    id              SERIAL          PRIMARY KEY,
    run_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    source          TEXT            NOT NULL,   -- 'csv_initial_load' | 'mae_bot_hourly' | 'mae_bot_weekly'
    granularity     TEXT            NOT NULL,   -- 'daily' | 'hourly'
    period_start    TIMESTAMPTZ,
    period_end      TIMESTAMPTZ,
    rows_inserted   INTEGER         NOT NULL DEFAULT 0,
    rows_skipped    INTEGER         NOT NULL DEFAULT 0,
    status          TEXT            NOT NULL DEFAULT 'ok',  -- 'ok' | 'partial' | 'error'
    error_message   TEXT
);
