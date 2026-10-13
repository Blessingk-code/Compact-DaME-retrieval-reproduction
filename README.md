# Compact-DaME-retrieval-reproduction
This package recalculates a few key results from the exploratory retrieval pilot in the manuscript. It includes small derived analysis datasets and one Python script. It does not redistribute original metadata, enriched metadata, source geospatial datasets, raw observations, embeddings or model weights.

## Results covered

- Complete primary nDCG@10 comparison, including the family bootstrap interval and exact family sign-flip p-value
- Family means and task counts corresponding to manuscript Table 3
- Eleven outcome-selected illustrative questions corresponding to Table 4
- Primary nDCG at 1, 3, 5 and 10, and paraphrase nDCG@10 corresponding to Table 5
- Primary Hit@5 and Hit@10 counts as a supporting check

All 49 evaluated needs and both formulations are retained to reproduce the complete benchmark. The eleven examples are selected after observing improvement and are not an independent validation set.

## Run

Use Python 3.10 or later,

```bash
python -m pip install -r requirements.txt
python scripts/reproduce_pilot.py
```

Results appear in `outputs/`. The script checks packaged input hashes, rebuilds dataset rankings from saved candidate cosine scores and calculates nDCG, Recall and Hit. It uses 20000 family bootstrap resamples with seed 20261009 and all 64 sign assignments for the six family differences. The main output should reproduce original nDCG@10 0.8777432751, enriched 0.9188722546, change 0.0411289794, interval [-0.0258516743, 0.1138693807] and exact family p 0.4375. These round to the reported manuscript values.

This is saved-score reproduction. It does not rerun the embedding model, regenerate enrichment or independently re-audit the source relevance judgments. The 209-pair MPNet/BGE/E5 correspondence analysis is outside this compact package. Reproducing that analysis requires its original texts, record-level scores and verified run configuration.

## Files

| File | Purpose |
| --- | --- |
| data/questions.csv | All 98 scored formulations, corresponding to 49 evaluated needs, with family and topic labels. |
| data/relevance.csv | Previously established source-checked relevance for the evaluated needs and 67 candidate records. -1 marks an unresolved candidate mapping, which is excluded for that need in both conditions. |
| data/candidate_scores.csv | Saved original and enriched candidate scores. These are numerical outputs, not metadata records or source observations. |
| scripts/reproduce_pilot.py | Rebuilds rankings, recomputes metrics and uncertainty, and extracts the eleven illustrative cases. |
| reference/family_ndcg_changes.csv | Saved family results used to verify Table 3. |
| reference/cutoff_summary.csv | Saved cutoff results used to verify Table 5. |
| reference/retrieval_configuration.json | Recovered final E5 pilot settings, for interpretation of the saved scores. |
| requirements.txt | NumPy dependency for the reproduction script. |
| README.md | Scope, commands and file descriptions. |

The outputs include `family_results.csv`, `cutoff_results.csv`, `paired_ndcg_results.csv`, `illustrative_cases.csv`, `binary_hits.csv`, `query_metrics.csv`, `rankings.csv` and `verification.json`.

## Input access and redistribution

Original metadata are publicly accessible through Fairdata Metax, https://metax.fairdata.fi/v3/docs/, with discovery through Etsin, https://etsin.fairdata.fi/. Source geospatial resources and producer documentation are accessible through Paituli, https://paituli.csc.fi/. Enriched metadata may be requested from the corresponding author, subject to applicable provider licensing and redistribution conditions. This package does not assert a blanket legal prohibition on redistribution.

DaME source code is identified at https://github.com/Blessingk-code/DaME. Record the specific software revision when rebuilding enrichment. A current repository checkout is not necessarily identical to the study version.

Upload the extracted contents as a compact supplement or repository folder. Update the manuscript availability statement with the final repository or permanent release URL when it exists. Do not describe this as reproduction of all analyses in the paper.
