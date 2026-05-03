from src.dependencies.modules import get_data_pipeline
import pandas as pd
import re


class UploadService:
    def __init__(self):
        self.data_pipeline = get_data_pipeline()
        self.PO_REQUIRED = {
            "date",
            "po_number",
            "vendor_name",
            "product_code",
            "product_name",
            "quantity",
            "price_per_unit",
            "total_price"
        }

        self.OC_REQUIRED = {
            "po_number",
            "date",
            "order_confirmation_number",
            "product_code",
            "quantity",
            "price_per_unit",
            "total_price"
        }

        self.SHIP_REQUIRED = {
            "etd",
            "po_number",
            "vendor_name"
        }

    def normalize_colnames(self, df):
        df = df.copy()
        df.columns = [
            re.sub(r'\s+', '_', col.strip().lower())
            for col in df.columns
        ]
        return df
    
    def validate_colnames(self, df, required_columns, dataset_name="dataset"):
        missing = required_columns - set(df.columns)
        
        if missing:
            return False, f"{dataset_name} missing columns: {missing}"
        else:
            return True, None
    
    def upload_data(self, po, oc, ship):
        po_df = self.normalize_colnames(po)
        po_valid, po_error = self.validate_colnames(po_df, self.PO_REQUIRED, "PO Data")
        
        oc_df = self.normalize_colnames(oc)
        oc_valid, oc_error = self.validate_colnames(oc_df, self.OC_REQUIRED, "Order Confirmation Data")
        
        ship_df = self.normalize_colnames(ship)
        ship_valid, ship_error = self.validate_colnames(ship_df, self.SHIP_REQUIRED, "Shipping Data")

        if po_valid and oc_valid and ship_valid:
            merged_df = self.data_pipeline.run_full_pipeline(po_df, oc_df, ship_df)
            return {
                "data" : merged_df,
                "status" : 200
            }
        else:
            error_msg = []
            if not po_valid:
                error_msg.append(po_error)
            if not oc_valid:
                error_msg.append(oc_error)
            if not ship_valid:
                error_msg.append(ship_error)
            
            return {
                "error" : " | ".join(error_msg),
                "status" : 400
            }