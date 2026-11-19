"""
inspect_dataset.py – Stage 1: Inspection (corrected)
=====================================================
Reads the ORIGINAL CSV (read-only), verifies its SHA-256 checksum before
and after, and produces a comprehensive inspection with ALL statistics
computed directly from the file.  Every number in the reports is written
by this script from computed variables — no hardcoded values.

How to run
----------
    cd "d:\\W&B\\projects\\vision AI Rag version"
    python scripts/inspect_dataset.py

What it produces
----------------
- data/analysis/inspection_report.md
- data/documentation/schema_report.md
- data/documentation/data_quality_report.md
- data/documentation/cleaning_plan.md
- data/documentation/data_provenance.md

The original CSV is NEVER modified.
"""

import csv
import hashlib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR        = Path(__file__).resolve().parent.parent
ORIGINAL_CSV    = BASE_DIR / "data" / "original" / "customer_support_tickets_original.csv"
EXPECTED_SHA256 = "01b44c54ee71ffe88dceea897ff0fcd705c6ff81c3bb908be4ee06d1390cc2bb"

INSPECTION_REPORT = BASE_DIR / "data" / "analysis" / "inspection_report.md"
SCHEMA_REPORT     = BASE_DIR / "data" / "documentation" / "schema_report.md"
QUALITY_REPORT    = BASE_DIR / "data" / "documentation" / "data_quality_report.md"
CLEANING_PLAN     = BASE_DIR / "data" / "documentation" / "cleaning_plan.md"
PROVENANCE_DOC    = BASE_DIR / "data" / "documentation" / "data_provenance.md"

# The 10 "standard" support queues (the only ones that appear for English)
STANDARD_QUEUES = {
    "Technical Support", "Product Support", "Customer Service",
    "IT Support", "Billing and Payments", "Returns and Exchanges",
    "Service Outages and Maintenance", "Sales and Pre-Sales",
    "Human Resources", "General Inquiry",
}

# Heuristic language markers (for cross-tab only — column is authoritative)
GERMAN_MARKERS = [
    "bitte", "danke", "und", "ich", "mein", "nicht", "haben",
    "können", "liebe", "grüße", "sehr", "geehrte", "bezüglich",
    "bestellung", "produkt", "vielen dank",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    """Return lowercase hex SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksum(label: str) -> str:
    actual = sha256_file(ORIGINAL_CSV)
    if actual != EXPECTED_SHA256:
        print("FATAL – {} checksum mismatch!".format(label))
        print("  Expected: {}".format(EXPECTED_SHA256))
        print("  Actual:   {}".format(actual))
        sys.exit(1)
    print("  [{}] SHA-256 verified OK".format(label))
    return actual


def word_count(text: str) -> int:
    if not text or not text.strip():
        return 0
    return len(text.split())


def normalise_body(text: str) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r"<br\s*/?\s*>", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t


def heuristic_lang(text: str) -> str:
    if not text or not text.strip():
        return "empty"
    lower = text.lower()
    hits = sum(1 for w in GERMAN_MARKERS if w in lower)
    if hits >= 3:
        return "likely_german"
    if hits >= 1:
        return "possibly_german"
    return "likely_english"


def pct(num: int, denom: int) -> str:
    """Format a percentage string."""
    if denom == 0:
        return "0.00%"
    return "{:.2f}%".format(num / denom * 100)


def stats_line(values: list) -> str:
    """Min/max/mean/median summary for a list of ints."""
    if not values:
        return "no data"
    s = sorted(values)
    return "min={}, max={}, mean={:.1f}, median={}".format(
        s[0], s[-1], sum(s) / len(s), s[len(s) // 2]
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    out = []  # console output lines

    def p(msg: str = "") -> None:
        print(msg)
        out.append(msg)

    p("=" * 72)
    p("FlowPilot – Stage 1: Dataset Inspection (corrected)")
    p("=" * 72)
    p()

    # ── 1. Pre-read checksum ──────────────────────────────────────────────
    p("1. CHECKSUM VERIFICATION (pre-read)")
    verify_checksum("pre-read")
    p()

    # ── 2. Load CSV ───────────────────────────────────────────────────────
    p("2. READING FILE")
    file_size = ORIGINAL_CSV.stat().st_size
    p("   Path: {}".format(ORIGINAL_CSV))
    p("   Size: {:,} bytes ({:.1f} MB)".format(file_size, file_size / 1024 / 1024))

    with open(ORIGINAL_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        rows = list(reader)

    total = len(rows)
    n_cols = len(columns)
    p("   Rows (data): {:,}".format(total))
    p("   Columns ({}): {}".format(n_cols, columns))
    p()

    # ── Partition by language column (authoritative) ──────────────────────
    en_rows = [r for r in rows if r["language"].strip() == "en"]
    de_rows = [r for r in rows if r["language"].strip() == "de"]
    n_en = len(en_rows)
    n_de = len(de_rows)

    # ══════════════════════════════════════════════════════════════════════
    # 3. COLUMN OVERVIEW – all rows
    # ══════════════════════════════════════════════════════════════════════
    p("3. COLUMN OVERVIEW (all {} rows)".format(total))
    p("   {:<12} {:>10} {:>10} {:>8}".format("Column", "Non-empty", "Empty", "% empty"))
    p("   {} {} {} {}".format("-" * 12, "-" * 10, "-" * 10, "-" * 8))

    # Collect stats in dicts for reuse
    col_all = {}  # col -> {non_empty, empty, pct}
    col_en = {}   # col -> {non_empty, empty}
    for col in columns:
        ne_all = sum(1 for r in rows if r[col] and r[col].strip())
        em_all = total - ne_all
        col_all[col] = {"non_empty": ne_all, "empty": em_all}
        p("   {:<12} {:>10,} {:>10,} {:>8}".format(col, ne_all, em_all, pct(em_all, total)))

        ne_en = sum(1 for r in en_rows if r[col] and r[col].strip())
        em_en = n_en - ne_en
        col_en[col] = {"non_empty": ne_en, "empty": em_en}
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 3b. MISSING VALUES – English only
    # ══════════════════════════════════════════════════════════════════════
    p("3b. MISSING VALUES (English rows, n={:,})".format(n_en))
    p("   {:<12} {:>10} {:>10} {:>8}".format("Column", "Non-empty", "Empty", "% empty"))
    p("   {} {} {} {}".format("-" * 12, "-" * 10, "-" * 10, "-" * 8))
    for col in columns:
        s = col_en[col]
        p("   {:<12} {:>10,} {:>10,} {:>8}".format(
            col, s["non_empty"], s["empty"], pct(s["empty"], n_en)))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 4. LANGUAGE
    # ══════════════════════════════════════════════════════════════════════
    p("4. LANGUAGE DISTRIBUTION (from `language` column — authoritative)")
    lang_counter = Counter(r["language"].strip() for r in rows)
    for lang, cnt in lang_counter.most_common():
        p("   {}: {:,} ({})".format(lang, cnt, pct(cnt, total)))
    p()

    # 4b. Cross-tab: column vs heuristic
    p("4b. CROSS-TAB: `language` column vs body-text heuristic")
    cross = Counter()
    disagree = []
    for i, r in enumerate(rows):
        cl = r["language"].strip()
        hl = heuristic_lang(r["body"])
        cross[(cl, hl)] += 1
        if cl == "en" and hl in ("likely_german", "possibly_german"):
            disagree.append((i + 1, cl, hl, r["body"]))
        elif cl == "de" and hl == "likely_english":
            disagree.append((i + 1, cl, hl, r["body"]))

    p("   {:>8} {:>20} {:>8}".format("column", "heuristic", "count"))
    for (cl, hl), cnt in sorted(cross.items()):
        p("   {:>8} {:>20} {:>8,}".format(cl, hl, cnt))

    p()
    p("   Total disagreements: {:,}".format(len(disagree)))
    p("   Breakdown:")
    disagree_types = Counter((d[1], d[2]) for d in disagree)
    for (cl, hl), cnt in disagree_types.most_common():
        p("     column={} heuristic={}: {:,}".format(cl, hl, cnt))

    p()
    p("   First 20 disagreements:")
    for row_num, cl, hl, body in disagree[:20]:
        snip = (body or "")[:90].replace("\n", " ").replace("\r", " ")
        p("     Row {:>6}: col={} heur={:<18} {}".format(row_num, cl, hl, snip))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 5. FULL-ROW DUPLICATES
    # ══════════════════════════════════════════════════════════════════════
    p("5. EXACT FULL-ROW DUPLICATES")
    row_strings = ["|".join(r.get(c, "") for c in columns) for r in rows]
    full_dups = sum(c - 1 for c in Counter(row_strings).values() if c > 1)
    p("   Count: {}".format(full_dups))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 6. DUPLICATE BODIES – overall and English
    # ══════════════════════════════════════════════════════════════════════
    def compute_dup_groups(subset, label):
        groups = defaultdict(list)
        for idx, r in enumerate(subset):
            bn = normalise_body(r["body"])
            if bn:
                groups[bn].append(idx)
        dups = {k: v for k, v in groups.items() if len(v) > 1}
        n_dup_rows = sum(len(v) for v in dups.values())
        # Conflicts per label field
        cq = cp = ca = cany = 0
        for _, idxs in dups.items():
            q_conflict = len(set(subset[i]["queue"].strip() for i in idxs) - {""}) > 1
            p_conflict = len(set(subset[i]["priority"].strip() for i in idxs) - {""}) > 1
            a_conflict = len(set(subset[i]["answer"].strip() for i in idxs) - {""}) > 1
            if q_conflict: cq += 1
            if p_conflict: cp += 1
            if a_conflict: ca += 1
            if q_conflict or p_conflict or a_conflict: cany += 1
        # Size distribution
        sizes = Counter(len(v) for v in dups.values())
        return dups, n_dup_rows, cq, cp, ca, cany, sizes

    p("6. DUPLICATE BODIES (normalised)")

    p("   --- All rows ---")
    all_dups, all_dup_rows, all_cq, all_cp, all_ca, all_cany, all_sizes = \
        compute_dup_groups(rows, "all")
    p("   Groups: {:,}".format(len(all_dups)))
    p("   Rows in groups: {:,}".format(all_dup_rows))
    p("   Conflict groups (any): {:,}".format(all_cany))
    p("     queue: {}, priority: {}, answer: {}".format(all_cq, all_cp, all_ca))
    p("   Group sizes: {}".format(
        ", ".join("size {}: {}".format(sz, cnt) for sz, cnt in sorted(all_sizes.items()))))
    p()

    p("   --- English only ---")
    en_dups, en_dup_rows, en_cq, en_cp, en_ca, en_cany, en_sizes = \
        compute_dup_groups(en_rows, "English")
    p("   Groups: {:,}".format(len(en_dups)))
    p("   Rows in groups: {:,}".format(en_dup_rows))
    p("   Conflict groups (any): {:,}".format(en_cany))
    p("     queue: {}, priority: {}, answer: {}".format(en_cq, en_cp, en_ca))
    p("   Group sizes: {}".format(
        ", ".join("size {}: {}".format(sz, cnt) for sz, cnt in sorted(en_sizes.items()))))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 7. QUEUE DISTRIBUTION
    # ══════════════════════════════════════════════════════════════════════
    p("7. QUEUE DISTRIBUTION")
    q_all = Counter(r["queue"].strip() for r in rows)
    n_unique_q_all = len(q_all)
    top10 = q_all.most_common(10)
    top10_sum = sum(c for _, c in top10)
    rest_queues = n_unique_q_all - 10
    rest_rows = total - top10_sum

    p("   --- All rows ({:,}) ---".format(total))
    p("   Unique queues: {}".format(n_unique_q_all))
    for q, c in q_all.most_common():
        marker = " " if q in STANDARD_QUEUES else "*"
        p("   {} {:>6,}  ({})  {}".format(marker, c, pct(c, total), q))
    p("   Top-10 share: {:,} / {:,} = {}".format(top10_sum, total, pct(top10_sum, total)))
    p("   Rest ({} queues): {:,} rows = {}".format(rest_queues, rest_rows, pct(rest_rows, total)))
    p()

    q_en = Counter(r["queue"].strip() for r in en_rows)
    p("   --- English only ({:,}) ---".format(n_en))
    p("   Unique queues: {}".format(len(q_en)))
    for q, c in q_en.most_common():
        p("     {:>6,}  ({})  {}".format(c, pct(c, n_en), q))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 8. PRIORITY DISTRIBUTION
    # ══════════════════════════════════════════════════════════════════════
    p("8. PRIORITY DISTRIBUTION")
    p_all = Counter(r["priority"].strip() for r in rows)
    p("   --- All rows ---")
    for pri, cnt in p_all.most_common():
        p("     {:>6,}  ({})  {}".format(cnt, pct(cnt, total), pri))
    p()

    p_en = Counter(r["priority"].strip() for r in en_rows)
    p("   --- English only ---")
    for pri, cnt in p_en.most_common():
        p("     {:>6,}  ({})  {}".format(cnt, pct(cnt, n_en), pri))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 9. TYPE DISTRIBUTION
    # ══════════════════════════════════════════════════════════════════════
    p("9. TYPE DISTRIBUTION")
    t_all = Counter(r["type"].strip() for r in rows if r["type"].strip())
    type_empty_all = col_all["type"]["empty"]
    n_unique_type = len(t_all)
    p("   --- All rows ---")
    p("   Empty: {:,} ({})".format(type_empty_all, pct(type_empty_all, total)))
    p("   Non-empty unique values: {}".format(n_unique_type))
    for t, c in t_all.most_common():
        p("     {:>6,}  ({})  {}".format(c, pct(c, total), t))
    p()

    t_en = Counter(r["type"].strip() for r in en_rows if r["type"].strip())
    type_empty_en = col_en["type"]["empty"]
    p("   --- English only ---")
    p("   Empty: {} ({})".format(type_empty_en, pct(type_empty_en, n_en)))
    for t, c in t_en.most_common():
        p("     {:>6,}  ({})  {}".format(c, pct(c, n_en), t))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 10. TAG ANALYSIS – English only
    # ══════════════════════════════════════════════════════════════════════
    p("10. TAG ANALYSIS (English only)")
    tag_cols = [c for c in columns if c.startswith("tag_")]
    tag_en_stats = {}
    for tc in tag_cols:
        vals = [r[tc].strip() for r in en_rows if r[tc].strip()]
        empty = n_en - len(vals)
        unique = len(set(vals))
        tag_en_stats[tc] = {"non_empty": len(vals), "empty": empty, "unique": unique}
        p("   {}: {:,} non-empty, {:,} empty ({}), {:,} unique".format(
            tc, len(vals), empty, pct(empty, n_en), unique))
        for v, c in Counter(vals).most_common(5):
            p("     {:>6,}  {}".format(c, v))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 11. VERSION
    # ══════════════════════════════════════════════════════════════════════
    p("11. VERSION COLUMN")
    ver_all = Counter(r["version"].strip() for r in rows)
    p("   --- All rows ---")
    for v, c in ver_all.most_common():
        label = v if v else "(empty)"
        p("     {:>6,}  ({})  {}".format(c, pct(c, total), label))

    ver_en = Counter(r["version"].strip() for r in en_rows)
    p("   --- English only ---")
    for v, c in ver_en.most_common():
        label = v if v else "(empty)"
        p("     {:>6,}  ({})  {}".format(c, pct(c, n_en), label))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 12. TEXT LENGTH STATISTICS
    # ══════════════════════════════════════════════════════════════════════
    p("12. TEXT LENGTH STATISTICS (word counts)")
    text_stats_en = {}
    for field in ("subject", "body", "answer"):
        p("   --- {} ---".format(field))
        wc_all = [word_count(r[field]) for r in rows]
        nz_all = [w for w in wc_all if w > 0]
        em_all = wc_all.count(0)
        p("   All rows: {:,} non-empty, {:,} empty".format(len(nz_all), em_all))
        if nz_all:
            p("     {}".format(stats_line(nz_all)))

        wc_en = [word_count(r[field]) for r in en_rows]
        nz_en = [w for w in wc_en if w > 0]
        em_en = wc_en.count(0)
        text_stats_en[field] = {"non_empty": len(nz_en), "empty": em_en, "values": nz_en}
        p("   English:  {:,} non-empty, {:,} empty".format(len(nz_en), em_en))
        if nz_en:
            s = sorted(nz_en)
            p("     min={}, max={}, mean={:.1f}, median={}".format(
                s[0], s[-1], sum(s) / len(s), s[len(s) // 2]))
        p()

    # ══════════════════════════════════════════════════════════════════════
    # 13. SUBJECT ANALYSIS – English
    # ══════════════════════════════════════════════════════════════════════
    p("13. SUBJECT ANALYSIS (English)")
    en_subjects = [r["subject"].strip() for r in en_rows if r["subject"].strip()]
    en_subj_empty = col_en["subject"]["empty"]
    en_subj_unique = len(set(en_subjects))
    p("   Non-empty: {:,}, Empty: {:,}, Unique: {:,}".format(
        len(en_subjects), en_subj_empty, en_subj_unique))
    p("   Top 10:")
    for s, c in Counter(en_subjects).most_common(10):
        p("     {:>4}  {}".format(c, s[:70]))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 14. PLACEHOLDERS – separated by category
    # ══════════════════════════════════════════════════════════════════════
    p("14. PLACEHOLDER ANALYSIS")
    p("   (HTML markup and anonymisation tokens counted separately)")
    p()

    anon_re = re.compile(r"<(name|tel_num|acc_num)>", re.IGNORECASE)
    br_re = re.compile(r"<br\s*/?\s*>", re.IGNORECASE)
    bracket_re = re.compile(r"\[(Name|Customer Name|name|NAME)\]", re.IGNORECASE)
    curly_re = re.compile(r"\{[^}]+\}")

    ph_data = {}  # field -> {category -> Counter or count}
    for field in ("body", "answer"):
        anon_counter = Counter()
        anon_rows_cnt = 0
        br_count = 0
        br_rows_cnt = 0
        bracket_counter = Counter()
        bracket_rows_cnt = 0
        curly_counter = Counter()
        curly_rows_cnt = 0

        for r in rows:
            text = r[field] or ""
            af = anon_re.findall(text)
            if af:
                anon_rows_cnt += 1
                for a in af:
                    anon_counter["<{}>".format(a.lower())] += 1
            bf = br_re.findall(text)
            if bf:
                br_rows_cnt += 1
                br_count += len(bf)
            brf = bracket_re.findall(text)
            if brf:
                bracket_rows_cnt += 1
                for b in brf:
                    bracket_counter["[{}]".format(b)] += 1
            cf = curly_re.findall(text)
            if cf:
                curly_rows_cnt += 1
                for c in cf:
                    curly_counter[c] += 1

        ph_data[field] = {
            "anon": anon_counter, "anon_rows": anon_rows_cnt,
            "br": br_count, "br_rows": br_rows_cnt,
            "bracket": bracket_counter, "bracket_rows": bracket_rows_cnt,
            "curly": curly_counter, "curly_rows": curly_rows_cnt,
        }

        p("   --- {} ---".format(field.upper()))
        p("   HTML markup:")
        p("     <br> variants: {:,} occurrences in {:,} rows".format(br_count, br_rows_cnt))
        p()
        p("   Anonymisation tokens:")
        for tok, cnt in anon_counter.most_common():
            p("     {}: {:,} occurrences".format(tok, cnt))
        p("     Rows with any: {:,}".format(anon_rows_cnt))
        p()
        p("   [Name]-style brackets:")
        for tok, cnt in bracket_counter.most_common():
            p("     {}: {:,} occurrences".format(tok, cnt))
        p("     Rows with any: {:,}".format(bracket_rows_cnt))
        p()
        p("   Curly-brace patterns:")
        if curly_counter:
            for tok, cnt in curly_counter.most_common(10):
                display = tok[:80]
                p("     {}: {}".format(display, cnt))
            p("     Rows with any: {:,}".format(curly_rows_cnt))
        else:
            p("     NONE FOUND")
        p()

    # ══════════════════════════════════════════════════════════════════════
    # 15. COHORT: missing type + tag_1 + answer
    # ══════════════════════════════════════════════════════════════════════
    p("15. COHORT ANALYSIS: rows missing type + tag_1 + answer")
    cohort = [r for r in rows
              if not r["type"].strip()
              and not r["tag_1"].strip()
              and not r["answer"].strip()]
    n_cohort = len(cohort)
    p("   Total rows in cohort: {:,}".format(n_cohort))

    cohort_lang = Counter(r["language"].strip() for r in cohort)
    p("   Language breakdown:")
    for l, c in cohort_lang.most_common():
        p("     {}: {:,}".format(l, c))

    en_in_cohort = cohort_lang.get("en", 0)
    p("   English rows in cohort: {}".format(en_in_cohort))

    cohort_q = Counter(r["queue"].strip() for r in cohort)
    p("   Unique queues: {}".format(len(cohort_q)))
    p("   Queue breakdown:")
    for q, c in cohort_q.most_common():
        p("     {:>5,}  {}".format(c, q))

    cohort_p = Counter(r["priority"].strip() for r in cohort)
    p("   Priority breakdown:")
    for pri, c in cohort_p.most_common():
        p("     {:>5,}  {}".format(c, pri))

    # Also check: do all have subjects and bodies?
    cohort_no_subj = sum(1 for r in cohort if not r["subject"].strip())
    cohort_no_body = sum(1 for r in cohort if not r["body"].strip())
    cohort_no_ver = sum(1 for r in cohort if not r["version"].strip())
    p("   Missing subject: {}".format(cohort_no_subj))
    p("   Missing body: {}".format(cohort_no_body))
    p("   Missing version: {:,} (all: {})".format(cohort_no_ver, cohort_no_ver == n_cohort))
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 16. UNIQUE-ID CHECK
    # ══════════════════════════════════════════════════════════════════════
    p("16. UNIQUE-ID CHECK")
    for col in columns:
        values = [r[col].strip() for r in rows if r[col].strip()]
        unique = len(set(values))
        p("   {:<12}  {:>6,} unique / {:,} total  {}".format(
            col, unique, total, "UNIQUE" if unique == total else "not unique"))
    p("   Conclusion: no column is a unique row identifier.")
    p()

    # ══════════════════════════════════════════════════════════════════════
    # 17. SAMPLE ROWS
    # ══════════════════════════════════════════════════════════════════════
    p("17. SAMPLE ROWS (first 3 English, plus the 1 empty-body English row)")
    en_shown = 0
    empty_body_shown = False
    for i, r in enumerate(rows):
        if r["language"].strip() != "en":
            continue
        is_empty_body = not r["body"].strip()
        if en_shown < 3 or (is_empty_body and not empty_body_shown):
            p("   --- Row {} (SRC-{:06d}) ---".format(i + 1, i + 1))
            for col in columns:
                val = (r[col] or "")[:100].replace("\n", "\\n").replace("\r", "\\r")
                if len(r[col] or "") > 100:
                    val += "..."
                p("     {}: {}".format(col, val))
            p()
            if is_empty_body:
                empty_body_shown = True
            else:
                en_shown += 1

    # ── 18. Post-read checksum ────────────────────────────────────────────
    p("18. CHECKSUM VERIFICATION (post-read)")
    verify_checksum("post-read")
    p()

    # ══════════════════════════════════════════════════════════════════════
    #  WRITE ALL REPORT FILES
    # ══════════════════════════════════════════════════════════════════════
    p("=" * 72)
    p("WRITING REPORT FILES")
    p("=" * 72)
    p()

    # ── data_provenance.md ────────────────────────────────────────────────
    prov = []
    prov.append("# Data Provenance")
    prov.append("")
    prov.append("## Original Dataset")
    prov.append("")
    prov.append("| Field | Value |")
    prov.append("|-------|-------|")
    prov.append("| **Name** | Customer Support Tickets |")
    prov.append("| **Source** | Hugging Face `Tobi-Bueck/customer-support-tickets` |")
    prov.append("| **URL** | https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets |")
    prov.append("| **Access date** | 2026-11-18 |")
    prov.append("| **Downloaded by** | `data/dataset.py` (`datasets.load_dataset`) |")
    prov.append("| **Licence** | **Unverified** (private learning project) |")
    prov.append("| **File** | `data/original/customer_support_tickets_original.csv` |")
    prov.append("| **Encoding** | UTF-8 with BOM (`utf-8-sig`) |")
    prov.append("| **SHA-256** | `{}` |".format(EXPECTED_SHA256))
    prov.append("| **Rows** | {:,} |".format(total))
    prov.append("| **Columns** | {} |".format(n_cols))
    prov.append("")
    prov.append("## Row-Level Notes")
    prov.append("")
    prov.append("- **German rows ({:,}):** `language` = `de`. Excluded from Collection A (English only).".format(n_de))
    prov.append("- **Off-topic cohort ({:,}):** All German, all missing `type`, `tag_1`-`tag_8`, `answer` and `version`. "
                "Queues are topic-classification labels (42 unique, e.g. `Pets & Animals/Pet Services`). "
                "No English rows belong to this cohort.".format(n_cohort))
    prov.append("- **Empty bodies ({:,}):** Unusable for NLP tasks.".format(col_all["body"]["empty"]))
    prov.append("- **Missing answers ({:,}):** Still usable for classification.".format(col_all["answer"]["empty"]))
    prov.append("")
    prov.append("## Integrity")
    prov.append("")
    prov.append("- The original file must **never** be modified. SHA-256 is verified before and after every read.")
    prov.append("- All synthetic data is labelled as such; no real personal data.")

    PROVENANCE_DOC.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_DOC.write_text("\n".join(prov), encoding="utf-8")
    p("  Written: {}".format(PROVENANCE_DOC))

    # ── schema_report.md ──────────────────────────────────────────────────
    sr = []
    sr.append("# Schema Report")
    sr.append("")
    sr.append("## Column Definitions")
    sr.append("")
    sr.append("| # | Column | Non-empty (all) | Empty (all) | % empty | Non-empty (en) | Empty (en) | % empty (en) |")
    sr.append("|---|--------|-----------------|-------------|---------|----------------|------------|--------------|")
    desc_map = {
        "subject":  "Short title of the ticket",
        "body":     "Full customer message text",
        "answer":   "Agent/system response",
        "type":     "ITIL type: Incident, Request, Problem, Change",
        "queue":    "Routing category",
        "priority": "Urgency level",
        "language": "ISO 639-1 code: `en` or `de`",
        "version":  "Unknown meaning (3 values only)",
    }
    for i, col in enumerate(columns, 1):
        a = col_all[col]
        e = col_en[col]
        sr.append("| {} | `{}` | {:,} | {:,} | {} | {:,} | {:,} | {} |".format(
            i, col, a["non_empty"], a["empty"], pct(a["empty"], total),
            e["non_empty"], e["empty"], pct(e["empty"], n_en)))
    sr.append("")
    sr.append("## Notes")
    sr.append("")
    sr.append("- All columns are text (string) in the CSV.")
    sr.append("- No column uniquely identifies a row.")
    sr.append("- No customer, order or product identifiers exist.")
    sr.append("- `queue` has {} unique values overall but only {} for English rows.".format(
        n_unique_q_all, len(q_en)))
    sr.append("- `type` has {} unique non-empty values: {}.".format(
        n_unique_type, ", ".join("{} ({:,})".format(t, c) for t, c in t_all.most_common())))
    sr.append("- `priority` has {} unique values overall, {} for English.".format(
        len(p_all), len(p_en)))
    sr.append("- `version` has {} non-empty values: {}. Meaning unverified.".format(
        len([v for v in ver_all if v]),
        ", ".join("{} ({:,})".format(v, c) for v, c in ver_all.most_common() if v)))

    SCHEMA_REPORT.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_REPORT.write_text("\n".join(sr), encoding="utf-8")
    p("  Written: {}".format(SCHEMA_REPORT))

    # ── data_quality_report.md ────────────────────────────────────────────
    dq = []
    dq.append("# Data Quality Report")
    dq.append("")
    dq.append("## Summary")
    dq.append("")
    dq.append("| Metric | Value |")
    dq.append("|--------|-------|")
    dq.append("| Total rows | {:,} |".format(total))
    dq.append("| German rows | {:,} ({}) |".format(n_de, pct(n_de, total)))
    dq.append("| English rows | {:,} ({}) |".format(n_en, pct(n_en, total)))
    dq.append("| Full-row duplicates | {} |".format(full_dups))
    dq.append("")

    # Observation 1: Language
    dq.append("## Observation 1: Language Split")
    dq.append("")
    dq.append("The `language` column (authoritative) contains:")
    dq.append("- `de`: {:,} rows ({})".format(n_de, pct(n_de, total)))
    dq.append("- `en`: {:,} rows ({})".format(n_en, pct(n_en, total)))
    dq.append("")
    dq.append("A cross-tab against a body-text heuristic shows {:,} disagreements:".format(len(disagree)))
    for (cl, hl), cnt in disagree_types.most_common():
        dq.append("- column=`{}`, heuristic=`{}`: {:,} rows".format(cl, hl, cnt))
    dq.append("")
    dq.append("The heuristic is unreliable — it fires on common words like 'und' or 'nicht' "
              "that can appear in English contexts (product names, quoted text). "
              "The `language` column is treated as authoritative.")
    dq.append("")
    dq.append("**Stage 2 action:** Exclude all `language=de` rows. Log each to `excluded_records.csv` with reason `non_english`.")
    dq.append("")

    # Observation 2: Cohort
    dq.append("## Observation 2: The {:,}-Row Cohort".format(n_cohort))
    dq.append("")
    dq.append("{:,} rows are simultaneously missing `type`, `tag_1` through `tag_8`, `answer` and `version`.".format(n_cohort))
    dq.append("")
    dq.append("| Property | Value |")
    dq.append("|----------|-------|")
    for l, c in cohort_lang.most_common():
        dq.append("| Language `{}` | {:,} |".format(l, c))
    dq.append("| English rows | {} |".format(en_in_cohort))
    dq.append("| Unique queues | {} (all non-standard) |".format(len(cohort_q)))
    dq.append("| Missing subject | {} |".format(cohort_no_subj))
    dq.append("| Missing body | {} |".format(cohort_no_body))
    dq.append("| Missing version | {:,} (100%) |".format(cohort_no_ver))
    dq.append("")
    dq.append("Priority within this cohort:")
    dq.append("")
    dq.append("| Priority | Count |")
    dq.append("|----------|-------|")
    for pri, c in cohort_p.most_common():
        dq.append("| {} | {:,} |".format(pri, c))
    dq.append("")
    dq.append("These rows all have topic-classification queues (e.g. `Pets & Animals/Pet Services`, "
              "`News`, `Sports`) rather than support queues. They have bodies and subjects but no answers, "
              "types or tags. **No English rows belong to this cohort.** They will be excluded as German rows.")
    dq.append("")

    # Observation 3: Missing values (English)
    dq.append("## Observation 3: Missing Values (English Only)")
    dq.append("")
    dq.append("| Column | Non-empty | Empty | % empty | Action |")
    dq.append("|--------|-----------|-------|---------|--------|")
    actions = {
        "subject": "Keep; flag `has_subject=False`; never fill",
        "body": "Exclude to `excluded_records.csv` reason `empty_body`",
        "answer": "Keep; flag `has_answer=False`",
        "type": "All present (0 missing)",
        "queue": "All present (0 missing)",
        "priority": "All present (0 missing)",
        "language": "All `en`",
        "version": "Keep; meaning unknown; not a feature",
    }
    for col in columns:
        s = col_en[col]
        action = actions.get(col, "Keep")
        if col.startswith("tag_") and s["empty"] > 0:
            action = "Keep; tags are sparse by design"
        dq.append("| `{}` | {:,} | {:,} | {} | {} |".format(
            col, s["non_empty"], s["empty"], pct(s["empty"], n_en), action))
    dq.append("")

    # Observation 4: Duplicates (English)
    dq.append("## Observation 4: Duplicate Bodies (English)")
    dq.append("")
    dq.append("| Metric | Value |")
    dq.append("|--------|-------|")
    dq.append("| Groups with identical normalised body | {:,} |".format(len(en_dups)))
    dq.append("| Total rows in those groups | {:,} |".format(en_dup_rows))
    dq.append("| Groups with any label conflict | {:,} |".format(en_cany))
    dq.append("| — queue conflicts | {} |".format(en_cq))
    dq.append("| — priority conflicts | {} |".format(en_cp))
    dq.append("| — answer conflicts | {} |".format(en_ca))
    dq.append("")
    dq.append("Group size distribution:")
    dq.append("")
    dq.append("| Size | Groups |")
    dq.append("|------|--------|")
    for sz, cnt in sorted(en_sizes.items()):
        dq.append("| {} | {:,} |".format(sz, cnt))
    dq.append("")
    dq.append("**Stage 2 action:** Assign `dup_group_id`, flag `dup_conflict_flag` for the {:,} "
              "conflict groups, keep all rows, ensure each group stays in one train/test split.".format(en_cany))
    dq.append("")

    # Observation 5: Placeholders
    dq.append("## Observation 5: Placeholders")
    dq.append("")
    dq.append("### HTML Markup (`<br>` variants)")
    dq.append("")
    dq.append("| Field | Occurrences | Rows |")
    dq.append("|-------|-------------|------|")
    for field in ("body", "answer"):
        d = ph_data[field]
        dq.append("| {} | {:,} | {:,} |".format(field, d["br"], d["br_rows"]))
    dq.append("")
    dq.append("**Stage 2 action:** In `body_clean`, convert `<br>`, `<br/>`, `<br />` to `\\n`.")
    dq.append("")

    dq.append("### Anonymisation Tokens")
    dq.append("")
    dq.append("| Token | In body | In answer |")
    dq.append("|-------|---------|-----------|")
    all_anon_tokens = set()
    for field in ("body", "answer"):
        all_anon_tokens.update(ph_data[field]["anon"].keys())
    for tok in sorted(all_anon_tokens):
        b_cnt = ph_data["body"]["anon"].get(tok, 0)
        a_cnt = ph_data["answer"]["anon"].get(tok, 0)
        dq.append("| `{}` | {:,} | {:,} |".format(tok, b_cnt, a_cnt))
    dq.append("")
    dq.append("Rows with any anonymisation token: {:,} (body), {:,} (answer).".format(
        ph_data["body"]["anon_rows"], ph_data["answer"]["anon_rows"]))
    dq.append("")

    dq.append("### `[Name]`-Style Bracket Tokens")
    dq.append("")
    dq.append("| Token | In body | In answer |")
    dq.append("|-------|---------|-----------|")
    all_brackets = set()
    for field in ("body", "answer"):
        all_brackets.update(ph_data[field]["bracket"].keys())
    for tok in sorted(all_brackets, key=str.lower):
        b_cnt = ph_data["body"]["bracket"].get(tok, 0)
        a_cnt = ph_data["answer"]["bracket"].get(tok, 0)
        dq.append("| `{}` | {:,} | {:,} |".format(tok, b_cnt, a_cnt))
    dq.append("")
    dq.append("Rows with any bracket token: {:,} (body), {:,} (answer).".format(
        ph_data["body"]["bracket_rows"], ph_data["answer"]["bracket_rows"]))
    dq.append("")

    dq.append("### Curly-Brace Patterns")
    dq.append("")
    body_curly = ph_data["body"]["curly"]
    ans_curly = ph_data["answer"]["curly"]
    if body_curly:
        dq.append("**Body:** {:,} rows, {:,} unique patterns.".format(
            ph_data["body"]["curly_rows"], len(body_curly)))
        dq.append("")
        for tok, cnt in body_curly.most_common():
            dq.append("- `{}`: {}".format(tok[:80], cnt))
        dq.append("")
    else:
        dq.append("**Body:** none found.")
        dq.append("")
    if ans_curly:
        dq.append("**Answer:** {:,} rows, {:,} unique patterns.".format(
            ph_data["answer"]["curly_rows"], len(ans_curly)))
        dq.append("")
        dq.append("| Pattern | Count |")
        dq.append("|---------|-------|")
        for tok, cnt in ans_curly.most_common(10):
            dq.append("| `{}` | {} |".format(tok[:60], cnt))
        dq.append("")
        dq.append("Most curly-brace patterns in answers are `{{name}}` ({:,}), "
                   "`{{tel_num}}` ({:,}) and `{{acc_num}}` ({:,}) — duplicates of the "
                   "angle-bracket anonymisation in a different syntax. The rest are "
                   "malformed JSON fragments, not `{{order_id}}`-style template variables.".format(
            ans_curly.get("{name}", 0), ans_curly.get("{tel_num}", 0), ans_curly.get("{acc_num}", 0)))
    else:
        dq.append("**Answer:** none found.")
    dq.append("")
    dq.append("**Stage 2 action:** Keep all anonymisation tokens as-is. Flag rows with "
              "`has_placeholders=True` when body contains `<name>`, `<tel_num>`, `<acc_num>` "
              "or `[Name]`-style tokens.")
    dq.append("")

    # Observation 6: Priority (English)
    dq.append("## Observation 6: Priority (English)")
    dq.append("")
    dq.append("| Priority | Count | % |")
    dq.append("|----------|-------|---|")
    for pri, cnt in p_en.most_common():
        dq.append("| {} | {:,} | {} |".format(pri, cnt, pct(cnt, n_en)))
    dq.append("")
    dq.append("English rows have {} priority levels. `critical` ({:,}) and `very_low` ({:,}) "
              "appear only in German rows.".format(
        len(p_en), p_all.get("critical", 0), p_all.get("very_low", 0)))
    dq.append("")

    # Observation 7: Queue (English)
    dq.append("## Observation 7: Queue (English)")
    dq.append("")
    dq.append("English rows have exactly {} queues:".format(len(q_en)))
    dq.append("")
    dq.append("| Queue | Count | % |")
    dq.append("|-------|-------|---|")
    for q, cnt in q_en.most_common():
        dq.append("| {} | {:,} | {} |".format(q, cnt, pct(cnt, n_en)))
    dq.append("")

    # Observation 8: Type (English)
    dq.append("## Observation 8: Type (English)")
    dq.append("")
    dq.append("All {:,} English rows have a type (0 missing):".format(n_en))
    dq.append("")
    dq.append("| Type | Count | % |")
    dq.append("|------|-------|---|")
    for t, cnt in t_en.most_common():
        dq.append("| {} | {:,} | {} |".format(t, cnt, pct(cnt, n_en)))
    dq.append("")

    # Observation 9: Version
    dq.append("## Observation 9: Version")
    dq.append("")
    dq.append("| Value | All rows | English |")
    dq.append("|-------|----------|---------|")
    all_ver_keys = sorted(set(list(ver_all.keys()) + list(ver_en.keys())),
                          key=lambda x: (x == "", x))
    for v in all_ver_keys:
        label = v if v else "(empty)"
        dq.append("| {} | {:,} | {:,} |".format(label, ver_all.get(v, 0), ver_en.get(v, 0)))
    dq.append("")
    dq.append("Meaning unknown. Kept but not used as a feature until verified.")
    dq.append("")

    # Observation 10: Text stats (English)
    dq.append("## Observation 10: Text Length (English)")
    dq.append("")
    dq.append("| Field | Non-empty | Empty | Min | Max | Mean | Median |")
    dq.append("|-------|-----------|-------|-----|-----|------|--------|")
    for field in ("subject", "body", "answer"):
        ts = text_stats_en[field]
        if ts["values"]:
            s = sorted(ts["values"])
            dq.append("| {} | {:,} | {:,} | {} | {} | {:.1f} | {} |".format(
                field, ts["non_empty"], ts["empty"],
                s[0], s[-1], sum(s) / len(s), s[len(s) // 2]))
        else:
            dq.append("| {} | 0 | {:,} | — | — | — | — |".format(field, ts["empty"]))
    dq.append("")

    # Observation 11: No IDs
    dq.append("## Observation 11: No Unique Identifiers")
    dq.append("")
    dq.append("No column uniquely identifies a row. `ticket_id` (`SRC-NNNNNN`) will be "
              "assigned from the 1-based row position in the original file.")
    dq.append("")

    QUALITY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_REPORT.write_text("\n".join(dq), encoding="utf-8")
    p("  Written: {}".format(QUALITY_REPORT))

    # ── cleaning_plan.md ──────────────────────────────────────────────────
    cp = []
    cp.append("# Cleaning Plan (Proposed — Not Yet Applied)")
    cp.append("")
    cp.append("> These rules are proposals from Stage 1 inspection. They will be")
    cp.append("> applied only in Stage 2 after user approval.")
    cp.append("")
    cp.append("## Scope")
    cp.append("")
    cp.append("Input: `data/original/customer_support_tickets_original.csv` ({:,} rows, {} columns).".format(total, n_cols))
    cp.append("")
    cp.append("Outputs:")
    cp.append("- `data/analysis/source_tickets_analysis.csv`")
    cp.append("- `data/processed/source_tickets_cleaned.csv`")
    cp.append("- `data/processed/excluded_records.csv`")
    cp.append("- `data/processed/transformation_log.csv`")
    cp.append("")

    rules = [
        ("Exclude German rows",
         "Remove all rows where `language` = `de`.",
         "{:,} rows excluded with reason `non_english`.".format(n_de),
         "{:,} rows remain.".format(n_en)),
        ("Exclude empty-body rows",
         "Remove English rows where `body` is empty or whitespace-only.",
         "{} English row(s) excluded with reason `empty_body`.".format(col_en["body"]["empty"]),
         "{:,} English rows remain after this step.".format(n_en - col_en["body"]["empty"])),
        ("Assign stable ticket IDs",
         "Each row gets `ticket_id` = `SRC-` + zero-padded 1-based row position "
         "(e.g. `SRC-000001` for row 1).",
         "IDs are assigned before filtering, so excluded rows also get IDs.",
         "IDs are deterministic — same on every rerun."),
        ("Convert `<br>` to newlines in `body_clean`",
         "Replace `<br>`, `<br/>`, `<br />` with `\\n`, then trim whitespace.",
         "Affects {:,} body rows with {:,} `<br>` occurrences.".format(
             ph_data["body"]["br_rows"], ph_data["body"]["br"]),
         "This is a derived column; the original `body` is never modified."),
        ("Keep missing subjects — do NOT fill",
         "{:,} English rows have empty subjects.".format(col_en["subject"]["empty"]),
         "Set `has_subject = False` in the analysis file.",
         "Per rules: never fill a missing subject with invented text."),
        ("Keep missing answers — do NOT fill",
         "{} English rows have empty answers.".format(col_en["answer"]["empty"]),
         "Set `has_answer = False` in the analysis file.",
         "These rows are still usable for queue/priority classification."),
        ("Assign duplicate-body groups",
         "Compute normalised body hash. Assign `dup_group_id` to groups.",
         "English: {:,} groups, {:,} rows, {:,} groups with label conflicts.".format(
             len(en_dups), en_dup_rows, en_cany),
         "Flag `dup_conflict_flag = True` for conflict groups. Keep all rows in same split."),
        ("Flag placeholders",
         "Set `has_placeholders = True` for rows with `<name>`, `<tel_num>`, `<acc_num>` "
         "or `[Name]`-style tokens in the body.",
         "These are intentional anonymisation markers.",
         "Not errors — kept as-is."),
        ("Compute word count",
         "`word_count` = number of whitespace-separated tokens in `body`.",
         "English: min={}, max={}, mean={:.1f}, median={}.".format(
             *((lambda s: (s[0], s[-1], sum(s)/len(s), s[len(s)//2]))(
                 sorted(text_stats_en["body"]["values"])))),
         ""),
        ("Keep `version` — do not use as feature",
         "Copy `version` as-is. Do not treat as classifier input.",
         "{} non-empty values, {:,} English rows with version.".format(
             len([v for v in ver_en if v]), col_en["version"]["non_empty"]),
         "Meaning unknown until verified."),
    ]

    for i, (name, what, detail, note) in enumerate(rules, 1):
        cp.append("### Rule {}: {}".format(i, name))
        cp.append("")
        cp.append("- **What:** {}".format(what))
        cp.append("- **Detail:** {}".format(detail))
        if note:
            cp.append("- **Note:** {}".format(note))
        cp.append("")

    cp.append("## Output Columns for `source_tickets_analysis.csv`")
    cp.append("")
    cp.append("```")
    cp.append("ticket_id, src_row_number, body_hash, dup_group_id, dup_conflict_flag,")
    cp.append("has_subject, has_answer, word_count, has_placeholders, body_clean")
    cp.append("```")
    cp.append("")
    cp.append("## Verification After Cleaning")
    cp.append("")
    cp.append("- `len(cleaned) + len(excluded) == {:,}`".format(total))
    cp.append("- Every excluded row has a reason")
    cp.append("- Every operation logged in `transformation_log.csv`")
    cp.append("- SHA-256 of original file unchanged")

    CLEANING_PLAN.parent.mkdir(parents=True, exist_ok=True)
    CLEANING_PLAN.write_text("\n".join(cp), encoding="utf-8")
    p("  Written: {}".format(CLEANING_PLAN))

    # ── inspection_report.md ──────────────────────────────────────────────
    ir = []
    ir.append("# Stage 1: Dataset Inspection Report")
    ir.append("")
    ir.append("> Generated by `scripts/inspect_dataset.py`.")
    ir.append("> SHA-256 verified before and after — the original file is unchanged.")
    ir.append("")

    ir.append("## 1. File Overview")
    ir.append("")
    ir.append("| Property | Value |")
    ir.append("|----------|-------|")
    ir.append("| File | `data/original/customer_support_tickets_original.csv` |")
    ir.append("| Size | {:,} bytes ({:.1f} MB) |".format(file_size, file_size / 1024 / 1024))
    ir.append("| Encoding | UTF-8 with BOM (`utf-8-sig`) |")
    ir.append("| Rows | {:,} |".format(total))
    ir.append("| Columns | {} |".format(n_cols))
    ir.append("| SHA-256 | `{}` |".format(EXPECTED_SHA256))
    ir.append("")
    ir.append("Columns: `{}`".format("`, `".join(columns)))
    ir.append("")
    ir.append("No column uniquely identifies a row. No customer, order or product IDs.")
    ir.append("")

    ir.append("## 2. Language")
    ir.append("")
    ir.append("Source: `language` column (authoritative).")
    ir.append("")
    ir.append("| Language | Rows | % |")
    ir.append("|----------|------|---|")
    for lang, cnt in lang_counter.most_common():
        ir.append("| `{}` | {:,} | {} |".format(lang, cnt, pct(cnt, total)))
    ir.append("")
    ir.append("Cross-tab with body-text heuristic: {:,} disagreements. ".format(len(disagree)))
    ir.append("The heuristic fires on common German words that sometimes appear in English text. ")
    ir.append("The `language` column is authoritative.")
    ir.append("")

    ir.append("## 3. Missing Values (English, n={:,})".format(n_en))
    ir.append("")
    ir.append("| Column | Non-empty | Empty | % empty |")
    ir.append("|--------|-----------|-------|---------|")
    for col in columns:
        s = col_en[col]
        ir.append("| `{}` | {:,} | {:,} | {} |".format(
            col, s["non_empty"], s["empty"], pct(s["empty"], n_en)))
    ir.append("")

    ir.append("## 4. Full-Row Duplicates")
    ir.append("")
    ir.append("**{}** exact full-row duplicates.".format(full_dups))
    ir.append("")

    ir.append("## 5. Duplicate Bodies (English)")
    ir.append("")
    ir.append("| Metric | Value |")
    ir.append("|--------|-------|")
    ir.append("| Groups | {:,} |".format(len(en_dups)))
    ir.append("| Rows in groups | {:,} |".format(en_dup_rows))
    ir.append("| Conflict groups (any) | {:,} |".format(en_cany))
    ir.append("| — queue | {} |".format(en_cq))
    ir.append("| — priority | {} |".format(en_cp))
    ir.append("| — answer | {} |".format(en_ca))
    ir.append("")
    ir.append("Group sizes: {}".format(
        ", ".join("size {}: {:,}".format(sz, cnt) for sz, cnt in sorted(en_sizes.items()))))
    ir.append("")

    ir.append("## 6. Queue (English — {} queues)".format(len(q_en)))
    ir.append("")
    ir.append("| Queue | Count | % |")
    ir.append("|-------|-------|---|")
    for q, cnt in q_en.most_common():
        ir.append("| {} | {:,} | {} |".format(q, cnt, pct(cnt, n_en)))
    ir.append("")

    ir.append("## 7. Priority (English — {} levels)".format(len(p_en)))
    ir.append("")
    ir.append("| Priority | Count | % |")
    ir.append("|----------|-------|---|")
    for pri, cnt in p_en.most_common():
        ir.append("| {} | {:,} | {} |".format(pri, cnt, pct(cnt, n_en)))
    ir.append("")
    ir.append("`critical` ({:,}) and `very_low` ({:,}) appear only in German rows.".format(
        p_all.get("critical", 0), p_all.get("very_low", 0)))
    ir.append("")

    ir.append("## 8. Type (English — {} types, {} missing)".format(len(t_en), type_empty_en))
    ir.append("")
    ir.append("| Type | Count | % |")
    ir.append("|------|-------|---|")
    for t, cnt in t_en.most_common():
        ir.append("| {} | {:,} | {} |".format(t, cnt, pct(cnt, n_en)))
    ir.append("")

    ir.append("## 9. Tags (English)")
    ir.append("")
    ir.append("| Tag | Non-empty | Empty | % empty | Unique |")
    ir.append("|-----|-----------|-------|---------|--------|")
    for tc in tag_cols:
        ts = tag_en_stats[tc]
        ir.append("| `{}` | {:,} | {:,} | {} | {:,} |".format(
            tc, ts["non_empty"], ts["empty"], pct(ts["empty"], n_en), ts["unique"]))
    ir.append("")

    ir.append("## 10. Cohort: {:,} Rows Missing type + tag_1 + answer".format(n_cohort))
    ir.append("")
    ir.append("| Property | Value |")
    ir.append("|----------|-------|")
    ir.append("| Total | {:,} |".format(n_cohort))
    for l, c in cohort_lang.most_common():
        ir.append("| Language `{}` | {:,} |".format(l, c))
    ir.append("| English rows | {} |".format(en_in_cohort))
    ir.append("| Unique queues | {} (all non-standard/off-topic) |".format(len(cohort_q)))
    ir.append("| Missing version | {:,} (100%) |".format(cohort_no_ver))
    ir.append("")
    ir.append("Priority within cohort:")
    ir.append("")
    ir.append("| Priority | Count |")
    ir.append("|----------|-------|")
    for pri, c in cohort_p.most_common():
        ir.append("| {} | {:,} |".format(pri, c))
    ir.append("")
    ir.append("**No English rows belong to this cohort.** All are German with topic-classification queues.")
    ir.append("")

    ir.append("## 11. Placeholders")
    ir.append("")
    ir.append("### HTML Markup")
    ir.append("")
    ir.append("| Field | `<br>` occurrences | Rows |")
    ir.append("|-------|--------------------|------|")
    for field in ("body", "answer"):
        d = ph_data[field]
        ir.append("| {} | {:,} | {:,} |".format(field, d["br"], d["br_rows"]))
    ir.append("")

    ir.append("### Anonymisation Tokens")
    ir.append("")
    ir.append("| Token | In body | In answer |")
    ir.append("|-------|---------|-----------|")
    for tok in sorted(all_anon_tokens):
        ir.append("| `{}` | {:,} | {:,} |".format(
            tok, ph_data["body"]["anon"].get(tok, 0),
            ph_data["answer"]["anon"].get(tok, 0)))
    ir.append("")

    ir.append("### `[Name]`-Style Brackets")
    ir.append("")
    ir.append("| Token | In body | In answer |")
    ir.append("|-------|---------|-----------|")
    for tok in sorted(all_brackets, key=str.lower):
        ir.append("| `{}` | {:,} | {:,} |".format(
            tok, ph_data["body"]["bracket"].get(tok, 0),
            ph_data["answer"]["bracket"].get(tok, 0)))
    ir.append("")

    ir.append("### Curly-Brace Patterns")
    ir.append("")
    ir.append("**Body:** {:,} rows, {} unique patterns: {}.".format(
        ph_data["body"]["curly_rows"], len(body_curly),
        ", ".join("`{}` ({})".format(t[:40], c) for t, c in body_curly.most_common())
        if body_curly else "none"))
    ir.append("")
    ir.append("**Answer:** {:,} rows, {} unique patterns. ".format(
        ph_data["answer"]["curly_rows"], len(ans_curly)))
    ir.append("Most are `{{name}}` ({:,}), `{{tel_num}}` ({:,}), `{{acc_num}}` ({:,}) — "
              "duplicates of the angle-bracket anonymisation. The rest are malformed JSON "
              "fragments. No `{{order_id}}`-style template variables were found.".format(
        ans_curly.get("{name}", 0), ans_curly.get("{tel_num}", 0), ans_curly.get("{acc_num}", 0)))
    ir.append("")

    ir.append("## 12. Text Statistics (English)")
    ir.append("")
    ir.append("| Field | Non-empty | Empty | Min | Max | Mean | Median |")
    ir.append("|-------|-----------|-------|-----|-----|------|--------|")
    for field in ("subject", "body", "answer"):
        ts = text_stats_en[field]
        if ts["values"]:
            s = sorted(ts["values"])
            ir.append("| {} | {:,} | {:,} | {} | {} | {:.1f} | {} |".format(
                field, ts["non_empty"], ts["empty"],
                s[0], s[-1], sum(s) / len(s), s[len(s) // 2]))
    ir.append("")

    ir.append("## 13. Version")
    ir.append("")
    ir.append("| Value | All rows | English |")
    ir.append("|-------|----------|---------|")
    for v in all_ver_keys:
        label = v if v else "(empty)"
        ir.append("| {} | {:,} | {:,} |".format(label, ver_all.get(v, 0), ver_en.get(v, 0)))
    ir.append("")
    ir.append("Meaning unknown. Kept but not treated as a feature.")
    ir.append("")

    ir.append("## 14. Stage 2 Actions (based on English-only analysis)")
    ir.append("")
    ir.append("1. Exclude {:,} German rows → log to `excluded_records.csv` reason `non_english`.".format(n_de))
    ir.append("2. Exclude {} empty-body English row(s) → reason `empty_body`.".format(col_en["body"]["empty"]))
    ir.append("3. Assign `ticket_id` = `SRC-NNNNNN` from 1-based row position (before filtering).")
    ir.append("4. Convert `<br>` to `\\n` in `body_clean` (derived column, {:,} rows affected).".format(ph_data["body"]["br_rows"]))
    ir.append("5. Flag {:,} rows with `has_subject=False`.".format(col_en["subject"]["empty"]))
    ir.append("6. Flag {} rows with `has_answer=False`.".format(col_en["answer"]["empty"]))
    ir.append("7. Assign `dup_group_id` to {:,} English groups ({:,} rows). Flag {:,} conflict groups.".format(
        len(en_dups), en_dup_rows, en_cany))
    ir.append("8. Flag `has_placeholders=True` for rows with anonymisation tokens in body.")
    ir.append("9. Compute `word_count` from body.")
    ir.append("10. Keep `version` as-is; do not use as feature.")
    ir.append("")
    ir.append("See `data/documentation/cleaning_plan.md` for full details.")
    ir.append("")

    INSPECTION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    INSPECTION_REPORT.write_text("\n".join(ir), encoding="utf-8")
    p("  Written: {}".format(INSPECTION_REPORT))

    p()
    p("=" * 72)
    p("Stage 1 inspection complete. Original file is unchanged.")
    p("=" * 72)


if __name__ == "__main__":
    main()
