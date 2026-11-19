# Schema Report

## Column Definitions

| # | Column | Non-empty (all) | Empty (all) | % empty | Non-empty (en) | Empty (en) | % empty (en) |
|---|--------|-----------------|-------------|---------|----------------|------------|--------------|
| 1 | `subject` | 56,466 | 5,299 | 8.58% | 24,622 | 3,639 | 12.88% |
| 2 | `body` | 61,763 | 2 | 0.00% | 28,260 | 1 | 0.00% |
| 3 | `answer` | 48,576 | 13,189 | 21.35% | 28,255 | 6 | 0.02% |
| 4 | `type` | 48,587 | 13,178 | 21.34% | 28,261 | 0 | 0.00% |
| 5 | `queue` | 61,765 | 0 | 0.00% | 28,261 | 0 | 0.00% |
| 6 | `priority` | 61,765 | 0 | 0.00% | 28,261 | 0 | 0.00% |
| 7 | `language` | 61,765 | 0 | 0.00% | 28,261 | 0 | 0.00% |
| 8 | `version` | 28,587 | 33,178 | 53.72% | 16,338 | 11,923 | 42.19% |
| 9 | `tag_1` | 48,587 | 13,178 | 21.34% | 28,261 | 0 | 0.00% |
| 10 | `tag_2` | 48,528 | 13,237 | 21.43% | 28,245 | 16 | 0.06% |
| 11 | `tag_3` | 48,356 | 13,409 | 21.71% | 28,148 | 113 | 0.40% |
| 12 | `tag_4` | 43,990 | 17,775 | 28.78% | 25,677 | 2,584 | 9.14% |
| 13 | `tag_5` | 27,636 | 34,129 | 55.26% | 16,301 | 11,960 | 42.32% |
| 14 | `tag_6` | 13,225 | 48,540 | 78.59% | 7,908 | 20,353 | 72.02% |
| 15 | `tag_7` | 5,968 | 55,797 | 90.34% | 3,699 | 24,562 | 86.91% |
| 16 | `tag_8` | 2,472 | 59,293 | 96.00% | 1,608 | 26,653 | 94.31% |

## Notes

- All columns are text (string) in the CSV.
- No column uniquely identifies a row.
- No customer, order or product identifiers exist.
- `queue` has 52 unique values overall but only 10 for English rows.
- `type` has 4 unique non-empty values: Incident (19,444), Request (13,950), Problem (10,196), Change (4,997).
- `priority` has 5 unique values overall, 3 for English.
- `version` has 3 non-empty values: 400.0 (18,599), 52.0 (9,119), 51.0 (869). Meaning unverified.