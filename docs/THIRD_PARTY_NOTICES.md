# Third-party software and data notices

## Current repository notices

The Git repository does not contain a local `biosteam/` or `thermosteam/` source tree. GreenHub installs BioSTEAM and ThermoSTEAM as Python dependencies. The root `LICENSE.txt` and `frontend/LICENSE.txt` retain the University of Illinois/NCSA BioSTEAM notice and a historical MIT notice labelled for BioSTEAM versions 0.1–0.9; both files now say explicitly that these upstream texts are not a GreenHub project license. The repository does not currently identify a separate GreenHub copyright holder or grant a GreenHub-specific source-code license.

The stale `PKG-INFO`, `MANIFEST.in`, and BioSTEAM-specific `README.rst` package metadata have been removed because there is no corresponding BioSTEAM package source or `setup.py` in this Git repository. The two license files are retained; removing or replacing third-party license text without an ownership review would be unsafe.

The project also contains a saved Spaak Circular Solutions website reference bundle under `docs/spaak-brand-reference/assets/`. GreenHub's frontend currently serves a subset of its Spaak logo, font, and illustration files from `frontend/public/assets/spaak/`; no separate license or redistribution grant for those brand assets is recorded in the repository. The saved bundle also includes third-party scripts and browser-extension files that are not used by the application. These materials are not covered by the BioSTEAM notices or any GreenHub license.

## Release review still required

- Confirm who owns the GreenHub-specific Python and frontend code and select the intended license for that code.
- Confirm whether the existing BioSTEAM and ThermoSTEAM notices cover only upstream components and how their conditions apply to GreenHub use and distribution. Keep the full notices when redistributing those components.
- Complete a license and notice inventory for the runtime and development Python dependencies in `requirements.txt` and `requirements-dev.txt`, plus the frontend dependency graph in `frontend/pnpm-lock.yaml`. Preserve third-party notices for any binary or source bundles distributed with GreenHub.
- Obtain written permission for the Spaak logo, fonts, and other brand assets used by the UI, or replace them with assets whose GreenHub redistribution rights are established. Decide whether the unused website snapshot and third-party scripts should be retained in any handover or release archive.
- Check dataset and workbook redistribution rights source by source. Citations and evidence registers establish provenance, but do not by themselves grant redistribution permission. Do not include confidential or restricted source files in a public release.

These checks have not been completed for the entire dependency graph or research-data collection. Treat the GreenHub code license and data redistribution scope as unresolved release gates; do not infer that the current BioSTEAM license covers all project files.

### Workspace metadata scan (2026-11-25)

The existing CPython 3.12 workspace environment contained 105 installed distributions; 104 exposed a license field or classifier in package metadata. The installed frontend package tree contained 390 package instances (including peer-context duplicates) covering 145 package names; all exposed a `license` field in their `package.json`. This is a metadata-presence check only: it does not verify license identifiers, required attribution text, all optional or platform-specific lockfile entries, or whether package contents are redistributed. Corepack could not retrieve the pinned pnpm 11.16.0 package during this session because DNS resolution for `registry.npmjs.org` failed, so a clean lockfile-derived package inventory could not be generated. The scan does not close the dependency-license review gate.
