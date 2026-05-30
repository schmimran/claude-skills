# Dataset Schema

The normalized per-message schema emitted by `parse_mbox.py` and `parse_olm.py`. One JSON object per email. `analyze_voice.py`, `select_intentional.py`, and `verify_quotes.py` all consume this shape.

Any custom parser (e.g. for `.pst`) **must emit this exact schema** for downstream scripts to work without modification.

---

## Fields

| Field | Type | Notes |
|---|---|---|
| `source` | string | Label identifying the source archive (e.g. `Sent`, `OLM:Sent Items`) |
| `date` | string (ISO 8601) | Send datetime, e.g. `2023-04-12T14:32:00` |
| `year` | int | Year extracted from `date` |
| `era` | string | Bucketed era: `<=2016`, `2017-2020`, `2021+` (exact buckets may vary by parser) |
| `from_addr` | string | Sender address, lowercased |
| `to_primary` | string | First recipient address, lowercased |
| `to_domain` | string | Domain of `to_primary` (used for heuristic audience classification) |
| `n_recipients` | int | Total recipients (To + Cc) |
| `is_self` | bool | True if all recipients are in the owner address list |
| `from_owner` | bool or null | True if `from_addr` is in the owner list; null if no owner list was provided |
| `subject` | string | Email subject line |
| `is_reply` | bool | True if subject starts with `Re:` (case-insensitive) |
| `is_forward` | bool | True if subject starts with `Fwd:` — **OLM only**; not present in mbox rows |
| `word_count` | int | Word count of `author_text` |
| `greeting` | string | Detected greeting form (see below) |
| `signoff` | string | Detected sign-off form (see below) |
| `lowercase_open` | bool | True if `author_text` begins with a lowercase letter |
| `double_space` | bool | True if `author_text` contains `.  ` (period + two spaces) |
| `space_before_bang` | bool | True if `author_text` contains ` !` |
| `space_before_q` | bool | True if `author_text` contains ` ?` |
| `two_dot_ellipsis` | bool | True if `author_text` contains `..` but not `...` |
| `smiley` | bool | True if `author_text` contains `:-)`, `:-)`, `;-)`, or variants |
| `avg_sentence_len` | float | Average words per sentence in `author_text` |
| `fragment_present` | bool | True if any sentence is 1–3 words (a fragment) |
| `numbered_list` | bool | True if `author_text` contains a numbered list (`1.` or `1)` pattern) |
| `empty_body` | bool | True if `author_text` has zero words |
| `author_text` | string | De-quoted, de-signature'd authored text. **JSON only** — omitted from CSV. |

---

## Greeting values

| Value | Meaning |
|---|---|
| `none` | No detectable greeting |
| `name_only` | Name alone, no punctuation (e.g. `Sarah`) |
| `name_dash` | Name followed by a dash (e.g. `Sarah -`) |
| `name_colon` | Name followed by a colon (e.g. `Sarah:`) |
| `name_comma` | Name followed by a comma (e.g. `Sarah,`) |
| `name_etal` | Name followed by `et al` |
| `hi_hey` | Starts with `Hi`, `Hey`, or `Hello` |
| `dear` | Starts with `Dear` |
| `salaam` | Starts with `Salaam`, `Salam`, `Assalam`, or variant |
| `group_collective` | Starts with `All`, `Team`, `Folks`, `Everyone`, etc. |

---

## Sign-off values

| Value | Meaning |
|---|---|
| `cheers` | Contains `Cheers` |
| `thanks` | Contains `Thanks` or `Thank you` |
| `best_regards` | Contains `Best regards`, `Warm regards`, `Kind regards`, `Best`, `Regards`, or `Sincerely` |
| `name_or_none` | No detectable sign-off keyword (name only, or nothing) |

---

## Notes

- `author_text` is the most important field for qualitative analysis. It strips quoted reply chains (lines starting with `>`, `On ... wrote:`, etc.) and signature blocks, leaving only what the author wrote.
- `empty_body` is true when `author_text` has zero words — these rows should generally be excluded from voice analysis.
- The audience classification used by `analyze_voice.py` is derived from `to_domain`: if the domain is not in the webmail list (gmail.com, icloud.com, etc.), the message is classified as "business." This is heuristic — always note this caveat.
- Rows where `from_owner` is false were included in the source archive but are not authored by the owner. Most parsers filter these out when `--owner` is provided; a small number may slip through on ambiguous addresses.
