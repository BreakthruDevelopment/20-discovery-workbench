-- The deterministic seed: two engagements, so the owner filter is testable.
--
-- Deterministic means byte-identical every time: fixed ids, fixed text, no timestamps, no random
-- ids, and `INSERT OR IGNORE` so seeding twice is the same database as seeding once.
--
-- What is seeded, and what is not. `engagement`, `engagement_principal` and the draft `readout`
-- shell are seeded, because they are configuration: who the engagements are and who may reach
-- them. `source_document` is NOT seeded -- it is an index over a real tree, built by
-- `store.index_sources` from the source library, so a seeded row would be a sha256 of a file that
-- may not exist (slice 20.3 commits the pack). `question`, `subagent_run` and `claim` are not
-- seeded either: they are a discovery run's output, and seeding fabricated claims and quotes would
-- put invented evidence in the product's own database, which is the one thing this app exists to
-- prevent. Tests write them through the store's accessors, which exercises the write path and the
-- access check on the way in.
--
-- Engagement ids double as source directory names (`sources/<engagement id>/`), which is why
-- `acme-p2p` matches the pack the spec names.

INSERT OR IGNORE INTO engagement (id, client, brief, sponsor_principal, state) VALUES
    (
        'acme-p2p',
        'Acme Industrial',
        'We spend too much on procure-to-pay, do something with AI.',
        'sponsor-acme',
        'open'
    ),
    (
        'northwind-ar',
        'Northwind Logistics',
        'Accounts receivable is slow and nobody agrees why. Find out where AI would pay off.',
        'sponsor-northwind',
        'open'
    );

-- Disjoint assignments: no principal reaches both engagements, which is what makes a
-- cross-engagement read testable as a refusal rather than as an accident of ordering.
INSERT OR IGNORE INTO engagement_principal (engagement_id, principal_id, role) VALUES
    ('acme-p2p',     'analyst-rao',    'analyst'),
    ('acme-p2p',     'lead-parrott',   'lead'),
    ('northwind-ar', 'analyst-shaw',   'analyst'),
    ('northwind-ar', 'lead-okafor',    'lead');

-- An empty draft readout per engagement. `coverage_json` is present and zeroed rather than absent:
-- coverage is mandatory and rendered first, so there is never a readout without it.
INSERT OR IGNORE INTO readout (
    engagement_id, id, state, maturity_json, outcomes_json, roi_json, roadmap_json, coverage_json,
    finalised_by
) VALUES
    (
        'acme-p2p', 'readout-acme-p2p', 'draft', '[]', '[]', NULL, '[]',
        '{"questions_total": 0, "answered": 0, "failed": 0, "gaps": []}', NULL
    ),
    (
        'northwind-ar', 'readout-northwind-ar', 'draft', '[]', '[]', NULL, '[]',
        '{"questions_total": 0, "answered": 0, "failed": 0, "gaps": []}', NULL
    );
