# Figure Conventions

This folder standardizes where figure assets and sources are stored.

## Layout
- `docs/figures/`: rendered assets referenced by docs (`.svg`, `.png`, etc.)
- `docs/figures/src/`: editable sources that require a build step (`.tex`, `.tikz`, `.drawio`, optional `.mmd`)

## Mermaid
- Keep Mermaid diagrams inline in the relevant topic page by default (`docs/estimation/*.md`, `docs/guidance/*.md`, `docs/control/*.md`, etc.).
- Do not split Mermaid into source + rendered files unless there is a concrete output need (for example PDF/export pipelines that cannot render Mermaid).
- If a Mermaid diagram must be rendered, store the source in `docs/figures/src/*.mmd` and store the rendered output in `docs/figures/*.svg`.

## Math-heavy figures (TikZ/LaTeX)
- Keep authoring source in `docs/figures/src/`.
- Commit rendered SVGs in `docs/figures/` for direct embedding in Markdown.

## Naming
- Use lowercase kebab-case.
- Prefer `<domain>-<topic>-<kind>-vN.<ext>`.
- Examples:
  - `control-actuation-pipeline-v1.svg`
  - `guidance-los-geometry-v1.svg`
  - `src/guidance-los-geometry-v1.tex`

## Embedding
- Reference rendered assets from docs with relative links, for example:
  - `![Actuation pipeline](../figures/control-actuation-pipeline-v1.svg)`
