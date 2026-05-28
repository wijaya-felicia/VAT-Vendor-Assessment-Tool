from src.dependencies.services import get_upload_service, get_storage_manager_cached
from src.types.models import UploadResponse, UploadErrorResponse
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pandas as pd
import uuid
from datetime import datetime
from src.database.connection import get_db
from src.services.auth import AuthService
from src.database.models import User, UploadRecord
from src.dependencies.auth import get_optional_user_from_header

upload_router = APIRouter()


@upload_router.post("/upload", response_model=UploadResponse)
async def upload_files(
    po: UploadFile = File(..., description="Purchase Order Excel file"),
    oc: UploadFile = File(..., description="Order Confirmation Excel file"),
    ship: UploadFile = File(..., description="Shipping Information Excel file"),
    db: Session = Depends(get_db),
    authorization: str | None = Header(None, alias="Authorization"),
    current_user: User | None = Depends(get_optional_user_from_header),
):

    try:
        session_id = str(uuid.uuid4())
        
        po_df = pd.read_excel(po.file)
        oc_df = pd.read_excel(oc.file)
        ship_df = pd.read_excel(ship.file)

        upload_service = get_upload_service()
        result = upload_service.upload_data(po_df, oc_df, ship_df)
        
        if result["status"] != 200:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Invalid dataset")
            )

        merged_df = result["data"]

        storage_manager = get_storage_manager_cached()
        storage_manager.save_session_data(
            session_id=session_id,
            merged_df=merged_df,
            po_row_count=len(po_df),
            oc_row_count=len(oc_df),
            ship_row_count=len(ship_df),
            metrics={},
        )

        # Save upload record to database (with user_id if authenticated)
        upload_record = UploadRecord(
            session_id=session_id,
            user_id=current_user.id if current_user else None,
            po_row_count=len(po_df),
            oc_row_count=len(oc_df),
            ship_row_count=len(ship_df),
            merged_row_count=len(merged_df),
            status="completed",
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)

        data_sample = merged_df.iloc[0].to_dict() if len(merged_df) > 0 else {}
        data_sample = {k: (None if pd.isna(v) else v) for k, v in data_sample.items()} if data_sample else {}

        return UploadResponse(
            session_id=session_id,
            status=200,
            message="Upload successful",
            row_count=len(merged_df),
            columns=merged_df.columns.tolist(),
            data_sample=data_sample
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(e)}"
        )