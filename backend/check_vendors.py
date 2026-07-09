import pandas as pd
from pathlib import Path

base_path = Path('sample data')
df_po = pd.read_excel(base_path / 'purchase_order.xlsx')
df_oc = pd.read_excel(base_path / 'confirmation_order.xlsx')
df_ship = pd.read_excel(base_path / 'shipping_details.xlsx')

print("=" * 80)
print("PURCHASE ORDER - All vendor_name values:")
print("=" * 80)
print(df_po['vendor_name'].value_counts(dropna=False))
print(f"\nTotal rows: {len(df_po)}")

print("\n" + "=" * 80)
print("SHIPPING - All vendor_name values:")
print("=" * 80)
print(df_ship['vendor_name'].value_counts(dropna=False))
print(f"\nTotal rows: {len(df_ship)}")

print("\n" + "=" * 80)
print("PO - First 50 rows with po_number and vendor_name:")
print("=" * 80)
print(df_po[['po_number', 'vendor_name']].head(50).to_string())

print("\n" + "=" * 80)
print("CHECKING FOR PATTERN OF VENDOR APPEARANCE:")
print("=" * 80)

print("\nVendor distribution by PO:")
po_vendor = df_po[['po_number', 'vendor_name']].dropna()
for vendor in df_po['vendor_name'].dropna().unique():
    po_count = po_vendor[po_vendor['vendor_name'] == vendor]['po_number'].nunique()
    row_count = len(df_po[df_po['vendor_name'] == vendor])
    print(f"{vendor}: {po_count} POs, {row_count} rows total")
