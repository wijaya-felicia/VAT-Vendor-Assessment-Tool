import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, '.')

from src.modules.data_pipeline import DataPipeline

base_path = Path('sample data')
df_po = pd.read_excel(base_path / 'purchase_order.xlsx')
df_oc = pd.read_excel(base_path / 'confirmation_order.xlsx')
df_ship = pd.read_excel(base_path / 'shipping_details.xlsx')

pipeline = DataPipeline()
merged = pipeline.run_full_pipeline(df_po, df_oc, df_ship)

print(f"\nMerged data shape: {merged.shape}")
print(f"\nVendors in merged data: {merged['vendor_name'].nunique()}")
print(f"Vendors: {merged['vendor_name'].unique()}")
print(f"\nVendor value counts:")
print(merged['vendor_name'].value_counts(dropna=False))
print(f"\nRows with NaN vendor_name: {merged['vendor_name'].isna().sum()}")
print(f"Rows with NaN price_discrepancy: {merged['price_discrepancy'].isna().sum()}")
print(f"Rows with NaN delay_days: {merged['delay_days'].isna().sum()}")

# Check what happens when we dropna on all three
print("\n\n=== FILTERING ANALYSIS ===")
df_test = merged.dropna(subset=['vendor_name', 'price_discrepancy', 'delay_days'])
print(f"After dropna on (vendor_name, price_discrepancy, delay_days): {len(df_test)} rows")
print(f"Vendors remaining: {df_test['vendor_name'].nunique()}")
print(f"Vendors: {df_test['vendor_name'].unique()}")
print(f"Vendor value counts:")
print(df_test['vendor_name'].value_counts())
