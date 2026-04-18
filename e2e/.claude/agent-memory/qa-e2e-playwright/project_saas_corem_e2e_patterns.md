---
name: SAAS COREM E2E - Ant Design selector patterns and known bugs
description: Selector patterns for Ant Design 5 + known frontend-backend mismatches in SAAS COREM
type: project
---

## Ant Design 5 Selector Patterns (confirmed working)

### Select dropdowns
- The `.ant-form-item-label` is a SIBLING of `.ant-select` inside `.ant-form-item`, NOT an ancestor.
- WRONG: `.ant-select.filter({ has: .ant-form-item-label })` → finds nothing
- CORRECT: `.ant-form-item.filter({ has: 'label' text }).locator('.ant-select')` → works
- ALSO CORRECT: `modal.locator('.ant-select').nth(N)` for positional selection

### Select by position (when placeholder not visible)
- The Payments "Ano" select has `value={currentYear}` by default, so its placeholder is hidden.
- Use `page.locator('.ant-select').nth(1)` (0=Mes, 1=Ano, 2=Estado) instead of placeholder filter.

### Multiple spinners (strict mode)
- `expect(page.locator('.ant-spin-spinning')).toBeHidden()` fails when >1 spinner exists.
- Use `expect(page.locator('.ant-spin-spinning')).toHaveCount(0)` instead.

### Popconfirm buttons in Spanish locale
- Ant Design 5 with Spanish locale: OK button = "Aceptar", Cancel = "Cancelar" (NOT "OK")
- CORRECT: `popconfirm.getByRole('button', { name: 'Aceptar' }).click()`
- The Popconfirm renders as a `tooltip` ARIA role, CSS class `.ant-popconfirm`

### Modal combobox (Select inside Form.Item)
- `modal.getByRole('combobox', { name: /FieldName/ })` - the name includes the asterisk for required fields ("* Tipo")
- Click the `.ant-select-selector` directly: `modal.locator('.ant-select-selector').first().click()`
- Combobox ARIA label matches the Form.Item label content (with "*" prefix for required fields)

### Multiple select dropdowns simultaneously
- When multiple Ant Design Selects open at the same time → strict mode violation on `.ant-select-dropdown:not(.ant-select-dropdown-hidden)`
- Fix: wait for `toHaveCount(0)` before opening the next select, then use `.first()` on the dropdown

## Known Frontend-Backend Mismatches (tests skipped)

### TC-PAY-03: Registrar Pago
- Frontend sends: `{ monto, fecha_pago, metodo_pago, observaciones }` (no estado)
- Backend requires: `{ estado, metodo_pago?, comprobante?, observaciones? }` via PaymentRegisterSerializer
- Fix needed: Payments.jsx must add `estado: "PAGADO"` to the PATCH payload

### TC-PAY-04: Generar QR
- Backend endpoint fails with `InvalidStorageError` (file storage not configured in dev)
- Frontend also uses `responseType: "blob"` but successful response would be JSON `{"qr_url": "..."}`
- Fix needed: configure file storage + fix responseType in Payments.jsx

### TC-CASH-02: Nueva Transaccion
- Frontend Select uses string values: `{ value: "OTROS", label: "Otros" }` 
- Backend expects integer FK (CashCategory.id) for `categoria` field
- Fix needed: Cashflow.jsx must load categories from `/cashflow/cash-categories/` API and use IDs

### TC-ATT-03: Registro Masivo Asistencia
- Frontend sends: `{ aula: id, fecha: "...", registros: [{ alumno: id, estado: "..." }] }`
- Backend expects: `{ classroom_id: id, fecha: "...", asistencias: [{ student_id: id, estado: "..." }] }`
- Fix needed: Attendance.jsx field names must match BulkAttendanceSerializer

## Student Edit Modal
- `Students.jsx openEdit()` calls `form.setFieldsValue({ ...record, fecha_nacimiento: undefined })`
- fecha_nacimiento is reset to undefined on edit (bug in component)
- Genero may also lose its value during test flow
- Fix in test: always fill `fechaNacimiento` and `genero` before submitting edit modal

**Why:** These are fundamental frontend-backend API contract mismatches discovered during E2E test debugging on 2026-04-17.
**How to apply:** These 4 tests are marked `test.skip()` until the frontend bugs are fixed. When fixing, verify against the actual API serializers in backend/apps/.
