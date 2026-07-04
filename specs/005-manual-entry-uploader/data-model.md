# Data Model: Manual Entry Mapping

## Entities

### UploadedDataFrame
- **Fields**: Dynamic based on user upload.
- **Validation**: Must not be empty. Must have headers.

### ColumnMapping
- **pac_col**: String (name of column mapped to PAC)
- **car_col**: String (name of column mapped to CAR)
- **ea_col**: String (name of column mapped to EA)
- **Validation**: Users can map the same column to multiple targets if needed, or leave some targets unmapped depending on manual entry requirements.

### TargetPayload
- **PAC**: Extracted series/list
- **CAR**: Extracted series/list
- **EA**: Extracted series/list
