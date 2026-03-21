# NexLattice IEEE Conference Paper

This folder contains an IEEE conference-style paper draft based on the **NexLattice** project. The LaTeX structure matches [conference\_101719.tex](../Conference-LaTeX-template_10-17-19/conference_101719.tex) from the IEEE conference template package (same `IEEEtran` class and conference mode).

## Contents

| File | Purpose |
|------|---------|
| `IEEEtran.cls` | IEEE document class (copied from your template folder for self-contained builds). |
| `nexlattice_paper.tex` | Main paper source. |
| `README.md` | This file. |

## Build

From this directory, with a LaTeX distribution installed (TeX Live, MiKTeX, etc.):

```bash
pdflatex nexlattice_paper.tex
pdflatex nexlattice_paper.tex
```

Run `pdflatex` twice so references and citations resolve.

## Before submission

1. **Author block** lists **Assam down town University** (Faculty of Computer Technology, Guwahati, Assam, India) and **Associate Professor** for the supervisor; **emails are omitted**. Add email or ORCID lines if your venue requires them (see IEEE template `conference_101719.tex` for the usual fourth line).
2. Follow your **venue’s** page limit, anonymization rules, and any required sections or keywords.
3. Remove or replace the **Acknowledgment** section as appropriate.
4. Add **camera-ready figures** if required (the draft uses tables only so it compiles without extra image files).
5. Verify claims in **Section Evaluation** against your own measurements; the draft distinguishes repository-stated targets from formal benchmarks.

## Source project

Implementation and detailed specs live in the sibling folder: [NexLattice-main](../NexLattice-main/).
