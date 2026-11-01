# Gold set

The gold set is the only honest way to report extraction quality. Label it by
reading the proof first, then compare with the tool; never copy predictions into
the gold file.

## Schema

```yaml
proofs:
  - proof_chunk: shuxia-p0313-1053
    target_id: shuxia:定理9.2.2
    used:
      - shuxia:定义9.2.1
      - shuxia:定理7.1.2
```

- `proof_chunk`: the proof chunk being labeled.
- `target_id`: the theorem/lemma/corollary/proposition node the proof belongs to.
- `used`: every definition and theorem-family node actually used by the proof.

## Status

`demo_gold.yaml` labels the synthetic demo corpus and is used by the demo CI
check. `textbook_starter.yaml` is intentionally empty. The v0.1 acceptance
target is 30 proofs (10 per main textbook), stratified by chapter and proof
length. The harness and schema are ready; the labels must be added by a human.
Do not fabricate labels to satisfy a metric.
