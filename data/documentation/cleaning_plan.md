# Cleaning Plan (Proposed — Not Yet Applied)

> These rules are proposals from Stage 1 inspection. They will be
> applied only in Stage 2 after user approval.

## Scope

Input: `data/original/customer_support_tickets_original.csv` (61,765 rows, 16 columns).

Outputs:
- `data/analysis/source_tickets_analysis.csv`
- `data/processed/source_tickets_cleaned.csv`
- `data/processed/excluded_records.csv`
- `data/processed/transformation_log.csv`

### Rule 1: Exclude German rows

- **What:** Remove all rows where `language` = `de`.
- **Detail:** 33,504 rows excluded with reason `non_english`.
- **Note:** 28,261 rows remain.

### Rule 2: Exclude empty-body rows

- **What:** Remove English rows where `body` is empty or whitespace-only.
- **Detail:** 1 English row(s) excluded with reason `empty_body`.
- **Note:** 28,260 English rows remain after this step.

### Rule 3: Assign stable ticket IDs

- **What:** Each row gets `ticket_id` = `SRC-` + zero-padded 1-based row position (e.g. `SRC-000001` for row 1).
- **Detail:** IDs are assigned before filtering, so excluded rows also get IDs.
- **Note:** IDs are deterministic — same on every rerun.

### Rule 4: Convert `<br>` to newlines in `body_clean`

- **What:** Replace `<br>`, `<br/>`, `<br />` with `\n`, then trim whitespace.
- **Detail:** Affects 1,385 body rows with 5,909 `<br>` occurrences.
- **Note:** This is a derived column; the original `body` is never modified.

### Rule 5: Keep missing subjects — do NOT fill

- **What:** 3,639 English rows have empty subjects.
- **Detail:** Set `has_subject = False` in the analysis file.
- **Note:** Per rules: never fill a missing subject with invented text.

### Rule 6: Keep missing answers — do NOT fill

- **What:** 6 English rows have empty answers.
- **Detail:** Set `has_answer = False` in the analysis file.
- **Note:** These rows are still usable for queue/priority classification.

### Rule 7: Assign duplicate-body groups

- **What:** Compute normalised body hash. Assign `dup_group_id` to groups.
- **Detail:** English: 4,595 groups, 9,201 rows, 139 groups with label conflicts.
- **Note:** Flag `dup_conflict_flag = True` for conflict groups. Keep all rows in same split.

### Rule 8: Flag placeholders

- **What:** Set `has_placeholders = True` for rows with `<name>`, `<tel_num>`, `<acc_num>` or `[Name]`-style tokens in the body.
- **Detail:** These are intentional anonymisation markers.
- **Note:** Not errors — kept as-is.

### Rule 9: Compute word count

- **What:** `word_count` = number of whitespace-separated tokens in `body`.
- **Detail:** English: min=1, max=272, mean=55.4, median=54.

### Rule 10: Keep `version` — do not use as feature

- **What:** Copy `version` as-is. Do not treat as classifier input.
- **Detail:** 3 non-empty values, 16,338 English rows with version.
- **Note:** Meaning unknown until verified.

## Output Columns for `source_tickets_analysis.csv`

```
ticket_id, src_row_number, body_hash, dup_group_id, dup_conflict_flag,
has_subject, has_answer, word_count, has_placeholders, body_clean
```

## Verification After Cleaning

- `len(cleaned) + len(excluded) == 61,765`
- Every excluded row has a reason
- Every operation logged in `transformation_log.csv`
- SHA-256 of original file unchanged