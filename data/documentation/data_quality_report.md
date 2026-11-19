# Data Quality Report

## Summary

| Metric | Value |
|--------|-------|
| Total rows | 61,765 |
| German rows | 33,504 (54.24%) |
| English rows | 28,261 (45.76%) |
| Full-row duplicates | 0 |

## Observation 1: Language Split

The `language` column (authoritative) contains:
- `de`: 33,504 rows (54.24%)
- `en`: 28,261 rows (45.76%)

A cross-tab against a body-text heuristic shows 11,682 disagreements:
- column=`en`, heuristic=`possibly_german`: 6,606 rows
- column=`de`, heuristic=`likely_english`: 5,074 rows
- column=`en`, heuristic=`likely_german`: 2 rows

The heuristic is unreliable — it fires on common words like 'und' or 'nicht' that can appear in English contexts (product names, quoted text). The `language` column is treated as authoritative.

**Stage 2 action:** Exclude all `language=de` rows. Log each to `excluded_records.csv` with reason `non_english`.

## Observation 2: The 13,178-Row Cohort

13,178 rows are simultaneously missing `type`, `tag_1` through `tag_8`, `answer` and `version`.

| Property | Value |
|----------|-------|
| Language `de` | 13,178 |
| English rows | 0 |
| Unique queues | 42 (all non-standard) |
| Missing subject | 0 |
| Missing body | 0 |
| Missing version | 13,178 (100%) |

Priority within this cohort:

| Priority | Count |
|----------|-------|
| medium | 3,719 |
| high | 2,946 |
| low | 2,816 |
| critical | 1,914 |
| very_low | 1,783 |

These rows all have topic-classification queues (e.g. `Pets & Animals/Pet Services`, `News`, `Sports`) rather than support queues. They have bodies and subjects but no answers, types or tags. **No English rows belong to this cohort.** They will be excluded as German rows.

## Observation 3: Missing Values (English Only)

| Column | Non-empty | Empty | % empty | Action |
|--------|-----------|-------|---------|--------|
| `subject` | 24,622 | 3,639 | 12.88% | Keep; flag `has_subject=False`; never fill |
| `body` | 28,260 | 1 | 0.00% | Exclude to `excluded_records.csv` reason `empty_body` |
| `answer` | 28,255 | 6 | 0.02% | Keep; flag `has_answer=False` |
| `type` | 28,261 | 0 | 0.00% | All present (0 missing) |
| `queue` | 28,261 | 0 | 0.00% | All present (0 missing) |
| `priority` | 28,261 | 0 | 0.00% | All present (0 missing) |
| `language` | 28,261 | 0 | 0.00% | All `en` |
| `version` | 16,338 | 11,923 | 42.19% | Keep; meaning unknown; not a feature |
| `tag_1` | 28,261 | 0 | 0.00% | Keep |
| `tag_2` | 28,245 | 16 | 0.06% | Keep; tags are sparse by design |
| `tag_3` | 28,148 | 113 | 0.40% | Keep; tags are sparse by design |
| `tag_4` | 25,677 | 2,584 | 9.14% | Keep; tags are sparse by design |
| `tag_5` | 16,301 | 11,960 | 42.32% | Keep; tags are sparse by design |
| `tag_6` | 7,908 | 20,353 | 72.02% | Keep; tags are sparse by design |
| `tag_7` | 3,699 | 24,562 | 86.91% | Keep; tags are sparse by design |
| `tag_8` | 1,608 | 26,653 | 94.31% | Keep; tags are sparse by design |

## Observation 4: Duplicate Bodies (English)

| Metric | Value |
|--------|-------|
| Groups with identical normalised body | 4,595 |
| Total rows in those groups | 9,201 |
| Groups with any label conflict | 139 |
| — queue conflicts | 10 |
| — priority conflicts | 9 |
| — answer conflicts | 139 |

Group size distribution:

| Size | Groups |
|------|--------|
| 2 | 4,588 |
| 3 | 3 |
| 4 | 4 |

**Stage 2 action:** Assign `dup_group_id`, flag `dup_conflict_flag` for the 139 conflict groups, keep all rows, ensure each group stays in one train/test split.

## Observation 5: Placeholders

### HTML Markup (`<br>` variants)

| Field | Occurrences | Rows |
|-------|-------------|------|
| body | 5,909 | 1,385 |
| answer | 1,285 | 371 |

**Stage 2 action:** In `body_clean`, convert `<br>`, `<br/>`, `<br />` to `\n`.

### Anonymisation Tokens

| Token | In body | In answer |
|-------|---------|-----------|
| `<acc_num>` | 187 | 4,784 |
| `<name>` | 5,031 | 10,577 |
| `<tel_num>` | 722 | 18,138 |

Rows with any anonymisation token: 5,756 (body), 22,787 (answer).

### `[Name]`-Style Bracket Tokens

| Token | In body | In answer |
|-------|---------|-----------|
| `[customer name]` | 0 | 3 |
| `[Customer Name]` | 5 | 27 |
| `[NAME]` | 0 | 2 |
| `[Name]` | 69 | 4,588 |
| `[name]` | 4 | 1,461 |

Rows with any bracket token: 78 (body), 6,061 (answer).

### Curly-Brace Patterns

**Body:** 2 rows, 2 unique patterns.

- `{our product}`: 1
- `{CoStar}`: 1

**Answer:** 210 rows, 8 unique patterns.

| Pattern | Count |
|---------|-------|
| `{name}` | 193 |
| `{tel_num}` | 71 |
| `{acc_num}` | 18 |
| `{\"name}` | 7 |
| `{\"name\": \"[Name]\", \"message\": \"We take the security i` | 2 |
| `{\"name\": \"Customer Support\", \"message\": \"Thank you fo` | 2 |
| `{\"received\": \"I have received your request regarding the ` | 1 |
| `{Name}` | 1 |

Most curly-brace patterns in answers are `{name}` (193), `{tel_num}` (71) and `{acc_num}` (18) — duplicates of the angle-bracket anonymisation in a different syntax. The rest are malformed JSON fragments, not `{order_id}`-style template variables.

**Stage 2 action:** Keep all anonymisation tokens as-is. Flag rows with `has_placeholders=True` when body contains `<name>`, `<tel_num>`, `<acc_num>` or `[Name]`-style tokens.

## Observation 6: Priority (English)

| Priority | Count | % |
|----------|-------|---|
| medium | 11,570 | 40.94% |
| high | 10,917 | 38.63% |
| low | 5,774 | 20.43% |

English rows have 3 priority levels. `critical` (1,914) and `very_low` (1,783) appear only in German rows.

## Observation 7: Queue (English)

English rows have exactly 10 queues:

| Queue | Count | % |
|-------|-------|---|
| Technical Support | 8,149 | 28.83% |
| Product Support | 5,305 | 18.77% |
| Customer Service | 4,269 | 15.11% |
| IT Support | 3,333 | 11.79% |
| Billing and Payments | 2,897 | 10.25% |
| Returns and Exchanges | 1,402 | 4.96% |
| Service Outages and Maintenance | 1,106 | 3.91% |
| Sales and Pre-Sales | 843 | 2.98% |
| Human Resources | 553 | 1.96% |
| General Inquiry | 404 | 1.43% |

## Observation 8: Type (English)

All 28,261 English rows have a type (0 missing):

| Type | Count | % |
|------|-------|---|
| Incident | 11,213 | 39.68% |
| Request | 8,163 | 28.88% |
| Problem | 5,895 | 20.86% |
| Change | 2,990 | 10.58% |

## Observation 9: Version

| Value | All rows | English |
|-------|----------|---------|
| 400.0 | 18,599 | 10,441 |
| 51.0 | 869 | 551 |
| 52.0 | 9,119 | 5,346 |
| (empty) | 33,178 | 11,923 |

Meaning unknown. Kept but not used as a feature until verified.

## Observation 10: Text Length (English)

| Field | Non-empty | Empty | Min | Max | Mean | Median |
|-------|-----------|-------|-----|-----|------|--------|
| subject | 24,622 | 3,639 | 1 | 37 | 5.8 | 5 |
| body | 28,260 | 1 | 1 | 272 | 55.4 | 54 |
| answer | 28,255 | 6 | 1 | 222 | 58.3 | 59 |

## Observation 11: No Unique Identifiers

No column uniquely identifies a row. `ticket_id` (`SRC-NNNNNN`) will be assigned from the 1-based row position in the original file.
