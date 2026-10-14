# SPPT_Dataset

Engineering datasets for *Trustworthy LLM-Assisted Static Modeling of Hybrid
AC/DC Distribution Systems*. Four representation-level cases are provided:
IEEE123 and IEEE8500, each represented by GridLAB-D GLM and CIM RDF/XML.
GLM, not GLB, is the GridLAB-D text-model format used in the paper.

## Files and experiment boundary

Each case directory contains:

- `positive_sequence.glm` or `positive_sequence.xml`: the exact frozen,
  source-organized balanced positive-sequence AC engineering input used in
  the paper. Existing normalization and near-ideal-impedance regularization
  are retained; no new parameter tuning has been performed for publication.
- `hybrid_sppt.glm` or `hybrid_sppt.xml`: a newly exported engineering-data
  representation of that input with the saved deterministic DC augmentation
  explicitly included. Original AC bytes are unchanged. These are **SPPT
  interchange extensions**, not certified native GridLAB-D/CGMES models.
- `dc_overlay.json`: the saved augmentation recipe, attachment identities,
  controller settings, six terminal associations and provenance.
- `rich_model.json.gz`: the saved full hybrid rich engineering model from the
  terminal-semantics-v2 baseline. `S_hat` contains `N`, `D`, `T`, `delta`, `nu`,
  `iota`, `a`, `kappa`, `pi`, electrical domains and voltage bases.
- `H_src.json.gz`: the exact frozen decoded AC source snapshot supplied to
  Experiment I. Its `source_hash` is the SHA-256 of the native AC file; its
  compressed-file SHA-256 is the source-snapshot hash in `dc_overlay.json`.
- `normalization_provenance.json.gz`, `normalization_validation.json`:
  saved source-to-positive-sequence conversion records and validation.
- `baseline_validation.json`: a summary of the **previously evaluated**
  baseline's six SPPT checks and numerical residuals, not a new evaluation.

In the original trial, only the heterogeneous AC engineering input was
interpreted by the LLM. DC devices were deterministically introduced at the
rich-model boundary **before canonical projection**, not inferred by the LLM.
The new `hybrid_sppt.*` exports were not the original LLM inputs and must not be
used to imply that LLM-assisted interpretation of DC records was validated.
No API calls, new power-flow runs, experiment reruns or result modifications
were made during packaging.

## Cases

| Case directory | Rich AC nodes | Canonical AC buses | Canonical AC branches | Total active load (MW) |
|---|---:|---:|---:|---:|
| `ieee123_glm` | 1505 | 1499 | 1498 | 3.84 |
| `ieee8500_glm` | 4875 | 4837 | 4836 | 10.77317 |
| `ieee123_cim` | 130 | 124 | 126 | 3.49 |
| `ieee8500_cim` | 4876 | 4838 | 4851 | 10.77317 |

Branch counts exclude switches and the added DC branch. These are four
engineering representations from two test-system families, not four independent
physical networks. IEEE123 GLM is a transactive variant with residential loads;
it is not numerically equivalent to IEEE123 CIM. Equality of IEEE8500 total
loads likewise does not establish complete physical equivalence across formats.

## Identical deterministic DC construction rule

Every case has two DC nodes, one DC line, two VSCs and six terminals. The
source-side AC node is connected through `SPPT_VSC_1` (VDC_Q), and the AC node
with the largest aggregate active load is connected through `SPPT_VSC_2` (PQ).
Stable engineering identity is used to break load-selection ties. Attachment
identities are copied from the saved baselines, not recalculated or relocated.

| Case | Source-side AC node | Maximum-load AC node |
|---|---|---|
| IEEE123 GLM | `node_150` | `house_agg_0_A_10_node_11_102` |
| IEEE8500 GLM | `HVMV_Sub_HSB` | `SX3234149C` |
| IEEE123 CIM | `urn:uuid:8A79AEE8-7C11-47E6-A5A2-F2CB4022D9FD` | `urn:uuid:CE33CF4F-E232-49DE-A134-FCF235C69F78` |
| IEEE8500 CIM | `urn:uuid:991B8337-D7FE-40E4-B520-9073A52BFCA6` | `urn:uuid:C67D1D5C-960D-4705-9DB8-F5B236084B57` |

The DC nodes are `DC:SPPT_DC_BUS_1` and `DC:SPPT_DC_BUS_2`; the DC branch is
`SPPT_DC_LINE`. The power base is 1 MVA, DC voltage base is 10 kV (pole-to-pole),
DC resistance is 0.02 p.u. = 2 ohm, conversion efficiency is 0.99, and the
source VSC voltage reference is 1.02 p.u. Both AC reactive setpoints are zero.
`P_PQ = min(max(0.02 * P_load,total, 0.001 * S_base), 0.05 * S_base)`, giving
0.05 MW in all four cases. Positive power means injection into the corresponding
AC or DC network. AC voltage bases remain per-node line-to-line values.

## SPPT extension syntax

GLM additions use `sppt_dc_node`, `sppt_dc_line`, `sppt_vsc` and
`sppt_terminal` object classes. The RDF/XML additions use the explicitly
nonstandard `urn:sppt:dataset:v1#` namespace; original CIM100 elements and
RDF identifiers are retained unchanged. Each new record retains its rich-model
`id`. Parameters and controls use `param_` and `ctrl_` prefixes. Terminals
declare `owner`, `node` and `domain`; references are not inferred from record
positions. RDF extension objects have `urn:sppt:dataset:<id>` URIs. AC terminal
references retain their original `urn:uuid:` URI.

These classes require an SPPT-aware importer. No class definitions or executable
native simulation model are asserted here. The portable verification script
checks extension serialization against the saved rich model; it does **not**
implement or certify a full physical importer or solver.

## Verification

With Python 3 (standard library only), run from this directory:

```sh
python verify_dataset.py
```

All distributed files are listed with SHA-256 and byte sizes in `manifest.json`.
The verifier checks the four frozen inputs, exact preservation of AC bytes,
DC device parameters and control values, six terminal associations, stable
identities, source hashes, and the recorded baseline assessment. It is read-only
and makes no network requests. Baseline checks refer to balanced steady-state
analysis with the declared one-source AC and two-terminal VDC_Q/PQ topology,
not arbitrary converter controls or unbalanced/dynamic behavior.

## Sources and rights

The AC data are derived from [GRIDAPPSD/Powergrid-Models](https://github.com/GRIDAPPSD/Powergrid-Models/tree/eaa0c3dcbc607e01c3f98092e3dea18929ae4d60),
commit `eaa0c3dcbc607e01c3f98092e3dea18929ae4d60`:

- IEEE123 GLM: `models/feeders/GridLABD/IEEE/transactive123.glm`.
- IEEE8500 GLM: `archive/GLM/IEEE_8500node.glm`.
- IEEE123 CIM: `models/feeders/CIM/XML/IEEE123.xml`.
- IEEE8500 CIM: `models/feeders/CIM/XML/IEEE8500.xml`.

The upstream attribution and disclaimer are retained in `UPSTREAM_NOTICE.md`.
This package does not grant a new license over third-party source data or
imply that original IEEE feeders natively contain the authored DC overlay.
Third-party rights remain with the respective owners. API credentials, prompts,
LLM responses, machine environment files, solver binaries, manuscript PDFs and
unrelated experiment outputs are excluded.
