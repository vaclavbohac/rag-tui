# Document.metadata is opaque to the TUI

The TUI never renders or interprets `Document.metadata` — it is a free-form
bag for the Pipeline author's own bookkeeping (ids, embeddings, provenance).
Anything display-worthy gets a first-class field instead, as `source`,
`score`, and `badges` do. We rejected the alternative of documented magic
keys (rendering `metadata["badge"]` in the panel title) because one magic key
invites more, typos fail silently, and metadata would grow an undocumented
stealth API. If a new display need appears, add a field — do not start
reading metadata.
