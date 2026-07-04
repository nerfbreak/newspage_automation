# Research: Manual Entry File Uploader

## 1. File Parsing (CSV, XLSX, XLS)
**Decision**: Use pandas built-in functions pd.read_csv() and pd.read_excel().
**Rationale**: pandas is already available in the Streamlit environment and provides robust, battle-tested parsing for all requested formats. .xls support might require xlrd, but pandas abstracts this.
**Alternatives considered**: Python's built-in csv module (too verbose for Excel), openpyxl (too low-level).

## 2. Streamlit Uploader Component
**Decision**: Use st.file_uploader(type=['csv', 'xlsx', 'xls']).
**Rationale**: Native, secure, and automatically handles in-memory file buffers without saving to disk.

## 3. UI Column Mapping
**Decision**: Use st.selectbox for PAC, CAR, and EA, populated with the uploaded DataFrame's columns.
**Rationale**: Clear and standard way for users to map dynamic columns to static expected targets.
