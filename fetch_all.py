"""
fetch_all.py — CLI Data Refresh Script for Wazifa Saathi.

Reads official scholarship URLs from `data/sources.json`, sequentially fetches
each page (with a polite 1-second delay between requests), extracts structured
JSON using `extract.extract_from_url`, validates against the Section 5 schema,
merges with `data/scholarships.seed.json`, and writes `data/scholarships.json`.

Usage:
    python fetch_all.py
    python fetch_all.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

from extract import ExtractionError, extract_from_url, validate_scholarship_schema

BASE_DIR = Path(__file__).resolve().parent
SOURCES_PATH = BASE_DIR / "data" / "sources.json"
SEED_PATH = BASE_DIR / "data" / "scholarships.seed.json"
OUTPUT_PATH = BASE_DIR / "data" / "scholarships.json"


def load_json_list(path: Path) -> list[dict[str, Any]]:
    """Safely load a JSON list from disk, returning an empty list if missing."""
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as exc:
        print(f"[WARN] Could not read {path}: {exc}", file=sys.stderr)
        return []


def merge_with_seed(
    extracted_list: list[dict[str, Any]],
    seed_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Merge freshly extracted scholarships with `scholarships.seed.json`.

    Merge policy (Section 10):
      - If a seed entry has `fetched_by == "manual"` AND `last_verified` is set
        (i.e. hand-verified by the maintainer, or a `demo_` entry), the verified
        manual fields in the seed entry take precedence.
      - If an extracted entry matches a seed entry by `source_url` or `id` where
        the seed entry was unverified (`last_verified` is null), the extracted
        record updates the seed entry while keeping stable seed `id` and `documents`
        if the extraction missed them.
      - Unverified seed entries that were not fetched (or failed during fetch) are
        retained so the catalogue remains complete.
    """
    merged_by_id: dict[str, dict[str, Any]] = {}
    url_to_seed_id: dict[str, str] = {}

    for seed in seed_list:
        sid = str(seed.get("id") or "").strip()
        if not sid or sid.startswith("demo_"):
            continue
        merged_by_id[sid] = dict(seed)
        s_url = str(seed.get("source_url") or "").strip().rstrip("/").lower()
        if s_url:
            url_to_seed_id[s_url] = sid

    for ext in extracted_list:
        ext_id = str(ext.get("id") or "").strip()
        ext_url = str(ext.get("source_url") or "").strip().rstrip("/").lower()

        matched_id = None
        if ext_id in merged_by_id:
            matched_id = ext_id
        elif ext_url and ext_url in url_to_seed_id:
            matched_id = url_to_seed_id[ext_url]

        if matched_id:
            seed_entry = merged_by_id[matched_id]
            is_verified_manual = (
                seed_entry.get("fetched_by") == "manual"
                and bool(seed_entry.get("last_verified"))
            )
            if is_verified_manual:
                # Seed wins for verified manual entries
                continue

            # Otherwise, merge AI extraction over unverified seed entry
            updated = dict(ext)
            updated["id"] = matched_id
            if not updated.get("documents") and seed_entry.get("documents"):
                updated["documents"] = seed_entry["documents"]
            if not updated.get("apply_url") and seed_entry.get("apply_url"):
                updated["apply_url"] = seed_entry["apply_url"]
            merged_by_id[matched_id] = updated
        else:
            merged_by_id[ext_id] = dict(ext)

    return list(merged_by_id.values())


def refresh_scholarships(
    dry_run: bool = False,
    progress_callback: Any = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Run the scholarship fetch and extraction pipeline.

    Can be called from CLI or Streamlit UI.
    """
    sources = load_json_list(SOURCES_PATH)
    seed_entries = load_json_list(SEED_PATH)
    today_iso = date.today().isoformat()

    extracted_records: list[dict[str, Any]] = []
    ok_count = 0
    failed_count = 0
    missing_deadline_count = 0
    failure_logs: list[tuple[str, str]] = []

    for idx, src in enumerate(sources):
        url = str(src.get("url") or "").strip()
        hint = str(src.get("hint") or "").strip() or None
        if not url:
            continue

        if progress_callback:
            progress_callback(idx + 1, len(sources), hint or url)

        print(f"[{idx + 1}/{len(sources)}] Fetching: {url} ({hint or 'no hint'}) ...", flush=True)
        try:
            record = extract_from_url(url=url, today=today_iso, hint=hint)
            validated = validate_scholarship_schema(
                raw=record,
                source_url=url,
                today=today_iso,
                fetched_by="ai_extraction",
            )
            extracted_records.append(validated)
            ok_count += 1
            if not validated.get("deadline_iso"):
                missing_deadline_count += 1
                dl_status = "MISSING DEADLINE (null)"
            else:
                dl_status = f"deadline={validated['deadline_iso']}"
            print(f"    -> OK: {validated['name']} [{dl_status}]", flush=True)
        except ExtractionError as exc:
            failed_count += 1
            reason = str(exc)
            failure_logs.append((url, reason))
            print(f"    -> SKIPPED: {reason}", flush=True)
        except Exception as exc:
            failed_count += 1
            reason = f"Unexpected error: {exc}"
            failure_logs.append((url, reason))
            print(f"    -> SKIPPED: {reason}", flush=True)

        if idx < len(sources) - 1:
            time.sleep(1.0)

    merged = merge_with_seed(extracted_records, seed_entries)

    stats = {
        "sources_count": len(sources),
        "ok_count": ok_count,
        "failed_count": failed_count,
        "missing_deadline_count": missing_deadline_count,
        "merged_count": len(merged),
        "failure_logs": failure_logs,
    }

    if not dry_run:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_PATH.open("w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"\n[SUCCESS] Wrote {len(merged)} records to {OUTPUT_PATH}")

    return merged, stats


def main() -> int:
    """Run the CLI scholarship fetch and extraction pipeline."""
    parser = argparse.ArgumentParser(
        description="Refresh data/scholarships.json from official URLs in data/sources.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and extract URLs without writing changes to data/scholarships.json",
    )
    args = parser.parse_args()

    sources = load_json_list(SOURCES_PATH)
    seed_entries = load_json_list(SEED_PATH)
    today_iso = date.today().isoformat()

    print("=" * 68)
    print(f"Wazifa Saathi — Data Refresh CLI ({today_iso})")
    print(f"Sources loaded: {len(sources)} | Seed entries: {len(seed_entries)}")
    if args.dry_run:
        print("Mode: DRY RUN (data/scholarships.json will NOT be modified)")
    print("=" * 68)

    merged, stats = refresh_scholarships(dry_run=args.dry_run)
    total_missing_deadlines = sum(1 for item in merged if not item.get("deadline_iso"))

    print("\n" + "=" * 68)
    print("SUMMARY TABLE")
    print("-" * 68)
    print(f"  {'Metric':<38} | {'Count':>10}")
    print("-" * 68)
    print(f"  {'URLs attempted':<38} | {stats['sources_count']:>10}")
    print(f"  {'OK (extracted & validated)':<38} | {stats['ok_count']:>10}")
    print(f"  {'Failed / Skipped':<38} | {stats['failed_count']:>10}")
    print(f"  {'Extracted with missing deadline':<38} | {stats['missing_deadline_count']:>10}")
    print(f"  {'Total merged records (with seed)':<38} | {stats['merged_count']:>10}")
    print(f"  {'Total records missing deadline':<38} | {total_missing_deadlines:>10}")
    print("=" * 68)

    if stats["failure_logs"]:
        print("\nFailure Log (skipped safely):")
        for failed_url, reason in stats["failure_logs"]:
            print(f"  - {failed_url}\n    Reason: {reason}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
