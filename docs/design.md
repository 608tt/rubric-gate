# Design and limits

Hard rules define acceptance. Soft rules contribute to a weighted satisfaction
score without vetoing a document. This prevents many easy checks from hiding a
single important failure, while preserving useful partial feedback.

Reports contain the document basename, content hash, rule outcomes and concise
rule evidence. They do not upload text or contact a model. HTML escapes names,
rule IDs and evidence. Failure details can contain configured strings; keep
private requirements out of public reports.

This is a lexical validator, not a semantic evaluator. It cannot distinguish
an affirmed fact from a negated one, validate source authorities, detect every
invented fact or estimate style fidelity. Keep human review for those tasks.
The included tests use controlled mutations to verify software behavior; they
are not a benchmark of model quality or real-world accuracy.

Rules are trusted local configuration. Python regular expressions can have
pathological runtimes; do not run untrusted regex specs. Limits of 500 rules and
200,000 characters bound input size but do not guarantee a regex timeout.

Future work: scoped checks, a complete Markdown adapter, stable structured
fact extractors and optional model-evaluation adapters with separate reporting.
