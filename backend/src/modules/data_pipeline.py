import pandas as pd

class DataPipeline:

    def _is_valid_vendor(self, value):
        if pd.isna(value):
            return False
        vendor_str = str(value).strip()
        if len(vendor_str) > 0:
            return vendor_str[0].isdigit()
        return False
    
    def _is_valid_po_number(self, value):
        if pd.isna(value):
            return False
        try:
            float(str(value))
            return True
        except ValueError:
            return False
    
    def _merge_data(self, po, oc, ship):
        po_clean = po.copy()
        po_clean['po_number'] = po_clean['po_number'].astype(str)
        oc_clean = oc.copy()
        oc_clean['po_number'] = oc_clean['po_number'].astype(str)
        ship_clean = ship.copy()
        ship_clean['po_number'] = ship_clean['po_number'].astype(str)
        
        if 'product_code' in po_clean.columns:
            po_clean['product_code'] = po_clean['product_code'].astype(str)
        if 'product_code' in oc_clean.columns:
            oc_clean['product_code'] = oc_clean['product_code'].astype(str)
        
        po_clean['po_number'] = po_clean['po_number'].ffill()
        oc_clean['po_number'] = oc_clean['po_number'].ffill()
        ship_clean['po_number'] = ship_clean['po_number'].ffill()
        
        po_clean['vendor_name'] = po_clean['vendor_name'].astype(str)
        po_clean['vendor_name'] = po_clean['vendor_name'].ffill()
        
        ship_clean['vendor_name'] = ship_clean['vendor_name'].astype(str)
        ship_clean['vendor_name'] = ship_clean['vendor_name'].ffill()
        
        if 'vendor_id' in po_clean.columns:
            po_clean['vendor_id'] = po_clean['vendor_id'].astype(str)
            po_clean['vendor_id'] = po_clean['vendor_id'].ffill()
        if 'vendor_id' in ship_clean.columns:
            ship_clean['vendor_id'] = ship_clean['vendor_id'].astype(str)
            ship_clean['vendor_id'] = ship_clean['vendor_id'].ffill()
        
        po_clean = po_clean[po_clean['po_number'].apply(self._is_valid_po_number)]
        oc_clean = oc_clean[oc_clean['po_number'].apply(self._is_valid_po_number)]
        ship_clean = ship_clean[ship_clean['po_number'].apply(self._is_valid_po_number)]
        
        po_clean = po_clean[po_clean['vendor_name'].apply(self._is_valid_vendor)]
        ship_clean = ship_clean[ship_clean['vendor_name'].apply(self._is_valid_vendor)]
        
        print(f"After PO number validation: PO={len(po_clean)}, OC={len(oc_clean)}, Ship={len(ship_clean)}")
        
        po_vendors = po_clean['vendor_name'].unique()
        print(f"Vendors in PO data: {len(po_vendors)} - {po_vendors.tolist()}")
        
        merged = po_clean.merge(
            oc_clean,
            on=['po_number', 'product_code'],
            how='left',
            suffixes=('_po', '_oc')
        )
        
        print(f"After PO-OC merge (LEFT): {len(merged)} rows")
        
        merged_vendors = merged['vendor_name'].unique()
        print(f"Vendors after PO-OC merge: {len(merged_vendors)} - {merged_vendors.tolist()}")
        
        merged = merged.merge(
            ship_clean,
            on=['po_number', 'vendor_name'],
            how='left',
            suffixes=('', '_ship')
        )
        
        print(f"After Ship merge (LEFT): {len(merged)} rows")
        
        final_vendors = merged['vendor_name'].unique()
        print(f"Final vendors in merged data: {len(final_vendors)} - {final_vendors.tolist()}")
        
        return merged

    def _engineer_features(self, df):
        try:
            if 'price_per_unit_po' in df.columns and 'price_per_unit_oc' in df.columns:
                df["price_discrepancy"] = df['price_per_unit_po'] - df['price_per_unit_oc']
            else:
                df["price_discrepancy"] = 0
            
            po_date_col = 'date_po' if 'date_po' in df.columns else 'date'
            
            if po_date_col in df.columns and 'etd' in df.columns:
                try:
                    po_dates = pd.to_datetime(df[po_date_col], errors='coerce')
                    
                    if df['etd'].dtype == 'object':
                        etd_dates = pd.to_datetime(df['etd'], format='%d.%m.%y', errors='coerce')
                    else:
                        etd_dates = pd.to_datetime(df['etd'], errors='coerce')
                    
                    expected_delivery = po_dates + pd.Timedelta(days=14)
                    df["delay_days"] = (etd_dates - expected_delivery).dt.days
                    df["delay_days"] = df["delay_days"].fillna(0).astype(int)
                except Exception as date_err:
                    print(f"Date parsing warning: {date_err}")
                    df["delay_days"] = 0
            else:
                df["delay_days"] = 0
                
        except Exception as e:
            print(f"Feature engineering error: {e}")
            df["price_discrepancy"] = 0
            df["delay_days"] = 0
            
        return df

    def run_full_pipeline(self, po, oc, ship):
        df = self._merge_data(po, oc, ship)
        df = self._engineer_features(df)
        return df