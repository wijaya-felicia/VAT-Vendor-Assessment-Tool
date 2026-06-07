from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os
import tempfile

from src.dependencies.services import get_bhm_service, get_storage_manager_cached
from src.dependencies.auth import get_current_user, get_optional_user_from_header
from src.database import get_db, BHMResult, ModelCheckpoint, VendorRanking
from src.database.models import User, UploadRecord
from src.types.models import BHMRankingsResponse, BHMVendorDetailResponse, ModelLockRequest, ModelLockResponse
from src.services.model_cache import get_model_cache

bhm_router = APIRouter()


@bhm_router.get("/latest-session")
async def get_latest_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the user's latest upload session ID."""
    latest_upload = db.query(UploadRecord)\
        .filter(UploadRecord.user_id == current_user.id)\
        .order_by(UploadRecord.created_at.desc())\
        .first()
    
    if not latest_upload:
        raise HTTPException(
            status_code=404,
            detail="No uploads found for this user"
        )
    
    return {"session_id": latest_upload.session_id}


@bhm_router.get("/rankings", response_model=BHMRankingsResponse)
async def get_vendor_rankings(
    session_id: str,
    bhm_service = Depends(get_bhm_service),
    storage_manager = Depends(get_storage_manager_cached),
    current_user: Optional[User] = Depends(get_optional_user_from_header),
    db: Session = Depends(get_db),
):

    try:
        print(f"[RANKINGS_ENDPOINT] Request received for session: {session_id}", flush=True)
        
        # Check if results already cached for this session
        model_cache = get_model_cache()
        cached = model_cache.get(session_id)
        
        if cached:
            print(f"[RANKINGS_ENDPOINT] Using cached models for session: {session_id}", flush=True)
            bhm_service.price_idata = cached["price_idata"]
            bhm_service.timeliness_idata = cached["timeliness_idata"]
            df = storage_manager.retrieve_data(session_id)
            rankings = bhm_service.compute_vendor_scores(df)
            convergence_status, convergence_warnings = bhm_service.check_convergence()
        else:
            print(f"[RANKINGS_ENDPOINT] No cache, fitting models for session: {session_id}", flush=True)
            # Retrieve merged data
            df = storage_manager.retrieve_data(session_id)
            print(f"[RANKINGS_ENDPOINT] Retrieved data, shape: {df.shape if df is not None else 'None'}", flush=True)

            if df is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found or expired"
                )

            # Auto-retrieve latest locked checkpoint (only for logged-in users, filtered by user)
            prior_checkpoint = None
            
            if current_user:
                try:
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
                        print(f"[RANKINGS_ENDPOINT] Using prior checkpoint from user {current_user.id}", flush=True)
                except Exception as e:
                    print(f"[RANKINGS_ENDPOINT] Warning: Could not retrieve checkpoint: {e}", flush=True)
                    prior_checkpoint = None
            
            print(f"[RANKINGS_ENDPOINT] Calling fit_and_rank...", flush=True)
            rankings_response = bhm_service.fit_and_rank(df, prior_checkpoint=prior_checkpoint)
            print(f"[RANKINGS_ENDPOINT] fit_and_rank completed", flush=True)
            
            # Cache the fitted models for reuse
            model_cache.set(
                session_id,
                bhm_service.price_idata,
                bhm_service.timeliness_idata,
                bhm_service.mcmc_iterations,
                bhm_service.mcmc_chains,
                bhm_service.mcmc_tuning,
            )
            print(f"[RANKINGS_ENDPOINT] Cached models for session: {session_id}", flush=True)
            
            rankings_response.session_id = session_id
            return rankings_response

        # Cached case: return response with cached data
        rankings_response = BHMRankingsResponse(
            session_id=session_id,
            model_type="Bayesian Hierarchical Model",
            convergence_status=convergence_status,
            convergence_warnings=convergence_warnings,
            mcmc_iterations=bhm_service.mcmc_iterations,
            mcmc_chains=bhm_service.mcmc_chains,
            rankings=rankings,
            model_timestamp=datetime.utcnow(),
            posterior_version=None,
        )
        rankings_response.session_id = session_id

        if rankings_response.convergence_status == "not_converged":
            return rankings_response 

        return rankings_response

    except ImportError as e:
        print(f"[RANKINGS_ENDPOINT] ImportError: {e}", flush=True)
        raise HTTPException(
            status_code=503,
            detail=f"BHM service unavailable: {str(e)}"
        )
    except Exception as e:
        print(f"[RANKINGS_ENDPOINT] Exception: {e}", flush=True)
        import traceback
        traceback.print_exc()
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
            try:
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
            except Exception as e:
                print(f"[VENDOR_DETAIL_ENDPOINT] Warning: Could not retrieve checkpoint: {e}", flush=True)
                prior_checkpoint = None

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


@bhm_router.get("/mcmc-iterations")
async def get_mcmc_iterations(
    session_id: str,
    bhm_service = Depends(get_bhm_service),
    storage_manager = Depends(get_storage_manager_cached),
    current_user: Optional[User] = Depends(get_optional_user_from_header),
    db: Session = Depends(get_db),
):
    """Get MCMC iteration counts and diagnostics."""
    try:
        # Check cache first - avoid rerunning BHM
        model_cache = get_model_cache()
        cached = model_cache.get(session_id)
        
        if cached:
            print(f"[MCMC_ITERATIONS] Using cached models for session: {session_id}", flush=True)
            bhm_service.price_idata = cached["price_idata"]
            bhm_service.timeliness_idata = cached["timeliness_idata"]
        else:
            print(f"[MCMC_ITERATIONS] No cache, fitting models for session: {session_id}", flush=True)
            df = storage_manager.retrieve_data(session_id)
            if df is None:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Fit models if not already fitted
            prior_checkpoint = None
            if current_user:
                try:
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
                except Exception as e:
                    print(f"Warning: Could not retrieve checkpoint: {e}")
            
            _ = bhm_service.fit_and_rank(df, prior_checkpoint=prior_checkpoint)
            
            # Cache the fitted models
            model_cache.set(
                session_id,
                bhm_service.price_idata,
                bhm_service.timeliness_idata,
                bhm_service.mcmc_iterations,
                bhm_service.mcmc_chains,
                bhm_service.mcmc_tuning,
            )
            print(f"[MCMC_ITERATIONS] Cached models for session: {session_id}", flush=True)
        
        # Get iteration info from cached/fitted models
        iteration_info = bhm_service.get_mcmc_iteration_info()
        return iteration_info
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@bhm_router.get("/mcmc-plots/{metric_type}/{plot_type}")
async def get_mcmc_plot(
    session_id: str,
    metric_type: str,
    plot_type: str,
    bhm_service = Depends(get_bhm_service),
    storage_manager = Depends(get_storage_manager_cached),
    current_user: Optional[User] = Depends(get_optional_user_from_header),
    db: Session = Depends(get_db),
):
    """Get MCMC diagnostic plot images."""
    try:
        # Check cache first - avoid rerunning BHM
        model_cache = get_model_cache()
        cached = model_cache.get(session_id)
        
        print(f"[MCMC_PLOTS] Checking cache for session: {session_id}", flush=True)
        print(f"[MCMC_PLOTS] Cache hit: {cached is not None}", flush=True)
        
        if cached:
            print(f"[MCMC_PLOTS] Using cached models for session: {session_id}", flush=True)
            bhm_service.price_idata = cached["price_idata"]
            bhm_service.timeliness_idata = cached["timeliness_idata"]
            print(f"[MCMC_PLOTS] price_idata is None: {bhm_service.price_idata is None}", flush=True)
            print(f"[MCMC_PLOTS] timeliness_idata is None: {bhm_service.timeliness_idata is None}", flush=True)
        else:
            print(f"[MCMC_PLOTS] No cache, fitting models for session: {session_id}", flush=True)
            df = storage_manager.retrieve_data(session_id)
            if df is None:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Fit models if needed
            prior_checkpoint = None
            if current_user:
                try:
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
                except Exception as e:
                    print(f"Warning: Could not retrieve checkpoint: {e}")
            
            result = bhm_service.fit_and_rank(df, prior_checkpoint=prior_checkpoint)
            print(f"[MCMC_PLOTS] fit_and_rank completed", flush=True)
            print(f"[MCMC_PLOTS] After fit - price_idata is None: {bhm_service.price_idata is None}", flush=True)
            print(f"[MCMC_PLOTS] After fit - timeliness_idata is None: {bhm_service.timeliness_idata is None}", flush=True)
            
            # Cache the fitted models
            model_cache.set(
                session_id,
                bhm_service.price_idata,
                bhm_service.timeliness_idata,
                bhm_service.mcmc_iterations,
                bhm_service.mcmc_chains,
                bhm_service.mcmc_tuning,
            )
            print(f"[MCMC_PLOTS] Cached models for session: {session_id}", flush=True)
        
        # Generate plots from cached/fitted models (use platform-independent temp dir)
        plot_dir = os.path.join(tempfile.gettempdir(), f"bhm_diagnostics_{session_id}")
        print(f"[MCMC_PLOTS] Plot directory: {plot_dir}", flush=True)
        
        if bhm_service.price_idata is None and bhm_service.timeliness_idata is None:
            print(f"[MCMC_PLOTS] ERROR: Both idata are None after cache check", flush=True)
            raise HTTPException(status_code=500, detail="Models not fitted - no idata available")
        
        # Only regenerate if plots don't already exist
        all_plots_exist = True
        for pt in ["traces", "iterations_summary", "burnin_analysis"]:
            for mt in ["price", "timeliness"]:
                if not os.path.exists(os.path.join(plot_dir, f"{mt}_{pt}.png")):
                    all_plots_exist = False
                    break
            if not all_plots_exist:
                break
        
        if all_plots_exist:
            print(f"[MCMC_PLOTS] All plots already exist, skipping regeneration", flush=True)
        else:
            plot_ok = bhm_service.generate_diagnostics_plots(output_dir=plot_dir)
            if not plot_ok:
                print(f"[MCMC_PLOTS] WARNING: Plot generation returned False", flush=True)
        
        # Map plot type to filename
        plot_mapping = {
            "traces": f"{metric_type}_traces.png",
            "iterations_summary": f"{metric_type}_iterations_summary.png",
            "burnin_analysis": f"{metric_type}_burnin_analysis.png",
        }
        
        filename = plot_mapping.get(plot_type)
        if not filename:
            raise HTTPException(status_code=400, detail="Invalid plot type")
        
        plot_path = os.path.join(plot_dir, filename)
        print(f"[MCMC_PLOTS] Looking for plot at: {plot_path}", flush=True)
        print(f"[MCMC_PLOTS] File exists: {os.path.exists(plot_path)}", flush=True)
        
        if not os.path.exists(plot_path):
            # List what files are in the directory
            if os.path.exists(plot_dir):
                files_in_dir = os.listdir(plot_dir)
                print(f"[MCMC_PLOTS] Files in {plot_dir}: {files_in_dir}", flush=True)
            else:
                print(f"[MCMC_PLOTS] Plot directory does not exist: {plot_dir}", flush=True)
            raise HTTPException(status_code=404, detail=f"Plot not found: {filename}")
        
        print(f"[MCMC_PLOTS] Returning plot: {plot_path}", flush=True)
        return FileResponse(plot_path, media_type="image/png")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
