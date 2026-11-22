"""Readout synthesis, provenance and coverage (statement 5.6).

New files only. This package calls `workbench/core/` and never edits it: quotes are checked with
`SourceLibrary.verify_quote`, and every read and write goes through the store under the acting
principal.

The readout is a Template Method. `ReadoutTemplate.assemble` is the skeleton -- maturity, then
outcomes, then the ROI model, then the roadmap, then coverage -- and a subclass overrides those
section steps rather than the skeleton. Provenance is applied inside the skeleton, in code:

* a claim reaches synthesis only after `verify_quote` says its quote is in the document it names
* a maturity dimension with no verified claim is `unknown`, never a number and never prose
* an outcome or an ROI figure with no basis claim is dropped
* two verified claims that disagree are kept as a conflict, with both quotes
* coverage is computed from the recorded runs and rendered first

The ROI model is one method, `roi_model`. Returning None from it is the track's first named cut:
the nullable `roi` column stores null, and nothing in the schema has to change.
"""
