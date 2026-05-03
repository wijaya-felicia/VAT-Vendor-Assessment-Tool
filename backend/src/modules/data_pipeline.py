import pandas as pd

class DataPipeline:
    """
    Merge strategy using po_number + product_code as primary key:
    1. Fill forward po_number (handles Excel multi-line format)
    2. Filter to keep only numeric po_numbers (excludes metadata like 'JKT/AIR')
    3. PO (primary) + OC (confirm order) on: po_number, product_code
    4. Result + Ship (tracking) on: po_number, vendor_name
    """
    
    def _is_valid_po_number(self, value):
        """Check if value is a valid PO number (numeric string)"""
        if pd.isna(value):
            return False
        try:
            # Try to convert to float - if it works, it's numeric
            float(str(value))
            return True
        except ValueError:
            return False
    
    def _merge_data(self, po, oc, ship):
        """
        Merge PO, OC, and Ship using po_number as the unique identifier.
        Handles Excel format with metadata rows mixed in.
        """
        # Fill forward po_number for multi-line orders using ffill (not deprecated)
        po_clean = po.copy()
        po_clean['po_number'] = po_clean['po_number'].ffill()
        
        oc_clean = oc.copy()
        oc_clean['po_number'] = oc_clean['po_number'].ffill()
        
        ship_clean = ship.copy()
        ship_clean['po_number'] = ship_clean['po_number'].ffill()
        
        # Filter to keep only valid (numeric) po_numbers
        # This removes metadata rows like 'JKT/AIR', 'AIR', etc.
        po_clean = po_clean[po_clean['po_number'].apply(self._is_valid_po_number)]
        oc_clean = oc_clean[oc_clean['po_number'].apply(self._is_valid_po_number)]
        ship_clean = ship_clean[ship_clean['po_number'].apply(self._is_valid_po_number)]
        
        print(f"Data after fill-forward and validation: PO={len(po_clean)}, OC={len(oc_clean)}, Ship={len(ship_clean)}")
        
        # Merge PO and OC on po_number and product_code
        merged = po_clean.merge(
            oc_clean,
            on=['po_number', 'product_code'],
            how='inner',
            suffixes=('_po', '_oc')
        )
        
        print(f"After PO-OC merge: {len(merged)} rows")
        
        # Merge with Ship on po_number and vendor_name
        merged = merged.merge(
            ship_clean,
            on=['po_number', 'vendor_name'],
            how='left',
            suffixes=('', '_ship')
        )
        
        print(f"After Ship merge: {len(merged)} rows")
        
        return merged

    def _engineer_features(self, df):
        """Calculate price discrepancy and delivery delay"""
        try:
            # Price discrepancy: difference between PO and OC price
            po_price = df.get('price_per_unit_po', df.get('price_per_unit', None))
            oc_price = df.get('price_per_unit_oc', df.get('price_per_unit', None))
            
            if po_price is not None and oc_price is not None:
                df["price_discrepancy"] = po_price - oc_price
            else:
                df["price_discrepancy"] = 0
            
            # Delivery delay: difference between actual ETD and expected ETD
            # Expected ETD = 14 days after PO date
            po_date_col = 'date_po' if 'date_po' in df.columns else 'date'
            
            if po_date_col in df.columns and 'etd' in df.columns:
                try:
                    # Parse PO date (should already be datetime from Excel)
                    po_dates = pd.to_datetime(df[po_date_col], errors='coerce')
                    
                    # Parse ETD date (European format: DD.MM.YY)
                    etd_dates = pd.to_datetime(df['etd'], format='%d.%m.%y', errors='coerce')
                    
                    # Calculate expected delivery (14 days after PO)
                    expected_delivery = po_dates + pd.Timedelta(days=14)
                    
                    # Calculate delay
                    df["delay_days"] = (etd_dates - expected_delivery).dt.days
                    
                    # Handle any parsing errors by setting to 0
                    df["delay_days"] = df["delay_days"].fillna(0).astype(int)
                except Exception as date_err:
                    print(f"Date parsing warning: {date_err}")
                    df["delay_days"] = 0
            else:
                df["delay_days"] = 0
                
        except Exception as e:
            print(f"Feature engineering warning: {e}")
            df["price_discrepancy"] = 0
            df["delay_days"] = 0
            
        return df

    def run_full_pipeline(self, po, oc, ship):
        """Execute the full merge and feature engineering pipeline"""
        df = self._merge_data(po, oc, ship)
        df = self._engineer_features(df)
        return df