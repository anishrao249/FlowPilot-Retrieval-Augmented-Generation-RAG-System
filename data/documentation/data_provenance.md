# Data Provenance

## Original Dataset

| Field | Value |
|-------|-------|
| **Name** | Customer Support Tickets |
| **Source** | Hugging Face `Tobi-Bueck/customer-support-tickets` |
| **URL** | https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets |
| **Access date** | 2026-11-18 |
| **Downloaded by** | `data/dataset.py` (`datasets.load_dataset`) |
| **Licence** | **Unverified** (private learning project) |
| **File** | `data/original/customer_support_tickets_original.csv` |
| **Encoding** | UTF-8 with BOM (`utf-8-sig`) |
| **SHA-256** | `01b44c54ee71ffe88dceea897ff0fcd705c6ff81c3bb908be4ee06d1390cc2bb` |
| **Rows** | 61,765 |
| **Columns** | 16 |

## Row-Level Notes

- **German rows (33,504):** `language` = `de`. Excluded from Collection A (English only).
- **Off-topic cohort (13,178):** All German, all missing `type`, `tag_1`-`tag_8`, `answer` and `version`. Queues are topic-classification labels (42 unique, e.g. `Pets & Animals/Pet Services`). No English rows belong to this cohort.
- **Empty bodies (2):** Unusable for NLP tasks.
- **Missing answers (13,189):** Still usable for classification.

## Integrity

- The original file must **never** be modified. SHA-256 is verified before and after every read.
- All synthetic data is labelled as such; no real personal data.