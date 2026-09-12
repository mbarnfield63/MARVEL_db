-- db_MARVEL schema v2
-- Executable source of truth. db_layout.txt is the dbdiagram.io mirror.
-- POC: no migration tool. On schema change, recreate the Postgres volume.
-- Applied via docker-entrypoint-initdb.d (see ticket #4).
--
-- Decisions behind this schema: schema/DECISIONS.md

-- ---------------------------------------------------------------------------
-- Reference tables
-- ---------------------------------------------------------------------------

CREATE TABLE molecules (
    id            SERIAL PRIMARY KEY,
    formula       varchar NOT NULL,              -- 'H2O'
    isotopologue  varchar NOT NULL UNIQUE,       -- ExoMol form '1H2-16O' (natural key)
    inchi_key     varchar UNIQUE,                -- nullable, hand-entered when known
    slug          varchar NOT NULL UNIQUE        -- loader-derived from isotopologue
);

CREATE TABLE marvel_versions (
    id            SERIAL PRIMARY KEY,
    version       varchar NOT NULL UNIQUE,       -- major version only: '3', '4', 'unknown'
    release_date  date                           -- nullable
);

INSERT INTO marvel_versions (version) VALUES ('3'), ('4'), ('unknown');

CREATE TABLE publications (
    id            SERIAL PRIMARY KEY,
    bibtex_key    varchar NOT NULL UNIQUE,       -- the human handle, e.g. '20FuTeCs.H2O'
    doi           varchar UNIQUE,                -- nullable (theses, old papers)
    year          smallint,
    title         text,
    authors       text,                          -- freeform
    journal       text,
    bibtex_raw    text,                           -- verbatim entry from data/refs/marvel.bib
    notes         text
);

-- Transition-origin references. Global: one row per source_tag, shared across runs.
CREATE TABLE source (
    id            SERIAL PRIMARY KEY,
    source_tag    varchar NOT NULL UNIQUE,       -- MRT tag minus trailing '.n', e.g. '32MaBa'
    doi           varchar,                        -- bib lookup on source_tag; nullable
    unit          varchar NOT NULL DEFAULT 'cm-1' -- segment file overrides if present
);

-- ---------------------------------------------------------------------------
-- Runs
-- ---------------------------------------------------------------------------

CREATE TABLE marvel_runs (
    id             SERIAL PRIMARY KEY,
    molecule_id    int NOT NULL REFERENCES molecules(id),
    version_id     int NOT NULL REFERENCES marvel_versions(id),
    publication_id int REFERENCES publications(id),   -- nullable: most runs unpublished
    dataset_hash   varchar NOT NULL,                  -- normalised sha256 of primary data file
    completeness   varchar NOT NULL
        CHECK (completeness IN ('complete', 'missing_segment', 'output_only')),
    qn_names       text[] NOT NULL,                   -- ordered QN schema for this run's JSONB keys
    description    text,                              -- manifest-optional, loader default
    loaded_at      timestamptz NOT NULL DEFAULT now(),
    load_report    jsonb,                             -- counts, warnings, version-column coverage
    UNIQUE (molecule_id, version_id, dataset_hash)
);

-- Raw files on the filesystem under data/<bibtex_key>/<molecule_slug>/.
CREATE TABLE run_files (
    id         SERIAL PRIMARY KEY,
    run_id     int NOT NULL REFERENCES marvel_runs(id) ON DELETE CASCADE,
    file_role  varchar NOT NULL
        CHECK (file_role IN ('input_transitions', 'output_levels', 'segment', 'other')),
    rel_path   varchar NOT NULL,                  -- repo-relative; becomes object-store key later
    sha256     varchar NOT NULL,                  -- true raw bytes
    byte_size  bigint  NOT NULL,
    UNIQUE (run_id, file_role)
);

-- ---------------------------------------------------------------------------
-- Solved levels + input transitions
-- ---------------------------------------------------------------------------

CREATE TABLE energy_levels (
    id               BIGSERIAL PRIMARY KEY,
    run_id           int NOT NULL REFERENCES marvel_runs(id) ON DELETE CASCADE,
    energy           double precision NOT NULL,
    uncertainty      double precision NOT NULL,
    quantum_numbers  jsonb NOT NULL,              -- {qn_name: token}, keys from marvel_runs.qn_names
    qn_key           text  NOT NULL,              -- canonical joined QN tokens; transition linking key
    symmetry         varchar,                     -- nullable; symmetry label when the level file carries one
    n_transitions    int,                         -- nullable; network node degree
    consistency_flag boolean,                     -- nullable; version-dependent
    component_id     int,                         -- nullable; spectroscopic-network component
    UNIQUE (run_id, qn_key)
);

CREATE TABLE transitions (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              int NOT NULL REFERENCES marvel_runs(id) ON DELETE CASCADE,
    source_id           int NOT NULL REFERENCES source(id),
    source_number       int NOT NULL,             -- trailing '.n' of the MRT tag; resets per source
    upper_level_id      bigint REFERENCES energy_levels(id),  -- null: endpoint state was never solved (floating SN component — MARVEL theory, not missing data)
    lower_level_id      bigint REFERENCES energy_levels(id),
    obs_freq            double precision NOT NULL, -- signed (MARVEL sign convention preserved)
    og_unc_freq         double precision,          -- as published; nullable
    used_unc_freq       double precision,          -- as used in the solve; nullable
    residual            double precision,          -- obs - calc; nullable
    consistency_flag    boolean,
    uncertainty_source  varchar,                   -- original | backfilled | user_edited (MARVEL5-style only)
    removed             boolean NOT NULL DEFAULT false,
    removed_reason      varchar,
    note                text,                      -- trailing annotation columns e.g. 'DE  BAD EHM'
    UNIQUE (run_id, source_id, source_number)
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

CREATE INDEX idx_energy_levels_run       ON energy_levels (run_id);
CREATE INDEX idx_energy_levels_qn        ON energy_levels USING gin (quantum_numbers);
CREATE INDEX idx_transitions_run         ON transitions (run_id);
CREATE INDEX idx_transitions_upper       ON transitions (upper_level_id);
CREATE INDEX idx_transitions_lower       ON transitions (lower_level_id);
CREATE INDEX idx_transitions_source      ON transitions (source_id);
