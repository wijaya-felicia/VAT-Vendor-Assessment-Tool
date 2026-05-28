from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from src.dependencies.services import get_bhm_service, get_storage_manager_cached
from src.dependencies.auth import get_current_user, get_optional_user_from_header
from src.database import get_db, BHMResult, ModelCheckpoint, VendorRanking
from src.database.models import User
from src.types.models import BHMRankingsResponse, BHMVendorDetailResponse, ModelLockRequest, ModelLockResponse

bhm_router = APIRouter()


@bhm_router.get("/rankings", response_model=BHMRankingsResponse)
async def get_vendor_rankings(
    session_id: str,
    bhm_service = Depends(get_bhm_service),
    storage_manager = Depends(get_storage_manager_cached),
    current_user: Optional[User] = Depends(get_optional_user_from_header),
    db: Session = Depends(get_db),
):

    try:
        # Retrieve merged data
        df = storage_manager.retrieve_data(session_id)

        if df is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )

        # Auto-retrieve latest locked checkpoint (only for logged-in users, filtered by user)
        prior_checkpoint = None
        
        if current_user:
            latest_checkpoint = db.query(ModelCheckpoint)\
                .filter(
                    ModelCheckpoint.is_locked == True,
                    ModelCheckpoint.locked_by_user_id == current_user.id
                )\
                .order_by(ModelCheckpoint.model_year.desc())\
                .first()
            
            if latest_checkpoint:
                prior_checkpoint = {
                    "price_posteriors": latest_checkpoint.price_accuracy_posteriors,
                    "timeliness_posteriors": latest_checkpoint.timeliness_posteriors,
                }

        rankings_response = bhm_service.fit_and_rank(df, prior_checkpoint=prior_checkpoint)
        rankings_response.session_id = session_id

        if rankings_response.convergence_status == "not_converged":
            return rankings_response 

        return rankings_response

    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"BHM service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing rankings: {str(e)}"
        )


@bhm_router.get("/vendor/{vendor_name}", response_model=BHMVendorDetailResponse)
async def get_vendor_detail(
    session_id: str,
    vendor_name: str,
    bhm_service = Depends(get_bhm_service),
    storage_manager = Depends(get_storage_manager_cached),
    current_user: Optional[User] = Depends(get_optional_user_from_header),
    db: Session = Depends(get_db),
):

    try:
        # Retrieve merged data
        df = storage_manager.retrieve_data(session_id)

        if df is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )

        # Auto-retrieve latest locked checkpoint (only for logged-in users, filtered by user)
        prior_checkpoint = None
        
        if current_user:
            latest_checkpoint = db.query(ModelCheckpoint)\
                .filter(
                    ModelCheckpoint.is_locked == True,
                    ModelCheckpoint.locked_by_user_id == current_user.id
                )\
                .order_by(ModelCheckpoint.model_year.desc())\
                .first()
            
            if latest_checkpoint:
                prior_checkpoint = {
                    "price_posteriors": latest_checkpoint.price_accuracy_posteriors,
                    "timeliness_posteriors": latest_checkpoint.timeliness_posteriors,
                }

        rankings_response = bhm_service.fit_and_rank(df, prior_checkpoint=prior_checkpoint)

        vendor_score = None
        for score in rankings_response.rankings:
            if score.vendor_name == vendor_name:
                vendor_score = score
                break

        if vendor_score is None:
            raise HTTPException(
                status_code=404,
                detail=f"Vendor '{vendor_name}' not found"
            )

        diagnostics = bhm_service.get_diagnostics()

        vendor_df = df[df["vendor_name"] == vendor_name]
        transaction_count = len(vendor_df)
        confidence = "high" if transaction_count >= 10 else ("medium" if transaction_count >= 5 else "low")

        return BHMVendorDetailResponse(
            session_id=session_id,
            vendor_name=vendor_name,
            combined_rank_score=vendor_score.combined_rank_score,
            rank=vendor_score.rank,
            price_accuracy_mean=vendor_score.price_accuracy_score,
            price_accuracy_ci_lower=vendor_score.price_accuracy_ci_lower,
            price_accuracy_ci_upper=vendor_score.price_accuracy_ci_upper,
            timeliness_mean=vendor_score.timeliness_score,
            timeliness_ci_lower=vendor_score.timeliness_ci_lower,
            timeliness_ci_upper=vendor_score.timeliness_ci_upper,
            diagnostics=diagnostics,
            transaction_count=transaction_count,
            confidence=confidence,
        )

    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"BHM service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving vendor detail: {str(e)}"
        )


@bhm_router.post("/model/lock", response_model=ModelLockResponse)
async def lock_model_as_prior(
    request: ModelLockRequest,
    current_user: User = Depends(get_current_user),
    bhm_service = Depends(get_bhm_service),
    db: Session = Depends(get_db),
):
    """Lock the current model as prior for next audit year. Only available to authenticated users."""

    try:
        checkpoint_data = bhm_service.save_posterior_checkpoint(request.model_year)

        vendor_count = len(checkpoint_data["price_posteriors"])
        now = datetime.utcnow()

        # Check if checkpoint for this year and user already exists
        existing_checkpoint = db.query(ModelCheckpoint).filter(
            ModelCheckpoint.model_year == int(request.model_year),
            ModelCheckpoint.locked_by_user_id == current_user.id
        ).first()
        
        if existing_checkpoint:
            # Update existing checkpoint
            existing_checkpoint.model_version = request.model_year
            existing_checkpoint.price_accuracy_posteriors = checkpoint_data["price_posteriors"]
            existing_checkpoint.timeliness_posteriors = checkpoint_data["timeliness_posteriors"]
            existing_checkpoint.vendor_count = vendor_count
            existing_checkpoint.description = request.description or f"Audit year {request.model_year}"
            existing_checkpoint.is_locked = True
            existing_checkpoint.locked_by_user_id = current_user.id
            existing_checkpoint.locked_at = now
            db.commit()
        else:
            # Create new checkpoint
            checkpoint = ModelCheckpoint(
                model_version=request.model_year,
                model_year=int(request.model_year),
                user_id=current_user.id,
                price_accuracy_posteriors=checkpoint_data["price_posteriors"],
                timeliness_posteriors=checkpoint_data["timeliness_posteriors"],
                vendor_count=vendor_count,
                description=request.description or f"Audit year {request.model_year}",
                is_locked=True,
                locked_by_user_id=current_user.id,
                locked_at=now,
            )
            db.add(checkpoint)
            db.commit()

        return ModelLockResponse(
            status="locked",
            model_year=request.model_year,
            locked_at=now,
            vendor_count=vendor_count,
            summary=f"Model for {request.model_year} locked as prior for next audit with {vendor_count} vendors",
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error locking model: {str(e)}"
        )
