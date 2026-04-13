# Knowledge Query Runbook

This runbook covers rebuilding and querying the deterministic knowledge query plane.

## Build

Command:

```powershell
python .\ops\knowledge\build_query_bundle.py
```

Expected output:

- writes `runtime/cortex/query/knowledge/bundle.json`
- reports a stable `content_digest`
- reads only promotion docs, runtime catalogs, and latest knowledge receipts

## Determinism Check

Run the build twice without changing source inputs:

```powershell
python .\ops\knowledge\build_query_bundle.py
python .\ops\knowledge\build_query_bundle.py
```

The reported `content_digest` must stay unchanged.

## Query

Command:

```powershell
python .\ops\knowledge\query_knowledge.py "verta core"
```

Optional limit:

```powershell
python .\ops\knowledge\query_knowledge.py "metadata only" --limit 10
```

## Output Discipline

- metadata-only archives return metadata fields only
- derived fields appear only when `query_policy.derived_searchable = true`
- raw imported text, extracted content, and full-text indexing are out of scope for this pass
- receipt digests and tooling digests are safe to return as provenance

## Validation

Validate the knowledge contracts, including the query bundle:

```powershell
python .\ops\knowledge\validate_knowledge_catalog.py
```

Skip query-bundle validation only for isolated repair work:

```powershell
python .\ops\knowledge\validate_knowledge_catalog.py --skip-query-bundle
```

## Failure Modes

- missing or stale `latest.json` receipts cause query-bundle validation failures
- invalid promotion docs block deterministic rebuilds
- `metadata_only` archives leaking derived fields is a contract violation
- `full_text` remains reserved and must not backdoor raw content into search
