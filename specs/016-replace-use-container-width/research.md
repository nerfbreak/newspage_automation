# Research: Streamlit Layout Width Deprecation Migration

## Decisions & Findings

### 1. Migration from `use_container_width` to `width`
- **Decision**: Replace all occurrences of `use_container_width=True` with `width='stretch'`, and `use_container_width=False` with `width='content'`.
- **Rationale**: Streamlit's official documentation states that `use_container_width` is deprecated and will be removed after December 31, 2025. The new `width` parameter with string values `'stretch'` and `'content'` is the designated replacement.
- **Alternatives Considered**: None, as this is a strict library-enforced deprecation.

### 2. Supported Streamlit Version
- **Decision**: Use the currently installed Streamlit version in the environment.
- **Rationale**: The currently running version of Streamlit already supports `width='stretch'` natively, as demonstrated by the successful migration of dashboard charts and page buttons on June 27, 2026.
