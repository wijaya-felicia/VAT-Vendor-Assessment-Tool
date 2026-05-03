from src.dependencies.services import get_upload_service, get_storage_manager_cached
from src.types.models import UploadResponse, UploadErrorResponse
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pandas as pd
import uuid
from datetime import datetime
from src.database.connection import get_db
from src.dependencies.auth import get_optional_user_from_header
from src.database.models import User

upload_router = APIRouter()


@upload_router.post("/upload", response_model=UploadResponse)
async def upload_files(
    po: UploadFile = File(..., description="Purchase Order Excel file"),
    oc: UploadFile = File(..., description="Order Confirmation Excel file"),
    ship: UploadFile = File(..., description="Shipping Information Excel file"),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    """
    Upload three datasets (PO, OC, Ship) and merge them with feature engineering.
    
    Supports both authenticated and guest uploads:
    - With Authorization header (Bearer token): Data is saved to user account
    - Without Authorization header: Creates anonymous session (expires after configured time)
    
    Returns merged dataset with calculated metrics (price_discrepancy, delay).
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Get current user if authenticated
        current_user = await get_optional_user_from_header(authorization, db)
        
        # Read uploaded files
        po_df = pd.read_excel(po.file)
        oc_df = pd.read_excel(oc.file)
        ship_df = pd.read_excel(ship.file)
        
        # Validate and process data
        upload_service = get_upload_service()
        result = upload_service.upload_data(po_df, oc_df, ship_df)
        
        if result["status"] != 200:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Invalid dataset")
            )
        
        # Extract merged dataframe
        merged_df = result["data"]
        
        # Save session data to storage manager
        storage_manager = get_storage_manager_cached()
        storage_manager.save_session_data(
            session_id=session_id,
            merged_df=merged_df,
            po_row_count=len(po_df),
            oc_row_count=len(oc_df),
            ship_row_count=len(ship_df),
            metrics={},
            user_id=current_user.id if current_user else None,
        )
        
        # Format response
        return UploadResponse(
            session_id=session_id,
            status=200,
            message="Upload successful",
            row_count=len(merged_df),
            columns=merged_df.columns.tolist(),
            data_sample=merged_df.iloc[0].to_dict() if len(merged_df) > 0 else {}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(e)}"
        )