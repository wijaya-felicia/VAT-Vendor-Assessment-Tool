"""
API router for dashboard endpoints.
Provides descriptive statistics and aggregated metrics.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.dependencies.services import get_dashboard_service, get_storage_manager_cached
from src.database import get_db
from src.types.models import DashboardMetrics, VisualizationData, TrendDataPoint

dashboard_router = APIRouter()


@dashboard_router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    session_id: str,
    dashboard_service = Depends(get_dashboard_service),
    storage_manager = Depends(get_storage_manager_cached),
):
    """
    Get aggregated dashboard metrics for a session.
    
    Query Parameters:
    - session_id: The session ID from upload
    
    Returns: Aggregated metrics including total spending, averages, and per-vendor stats.
    """
    try:
        # Retrieve merged data from storage
        df = storage_manager.retrieve_data(session_id)

        if df is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )

        # Compute metrics
        metrics = dashboard_service.get_aggregated_metrics(df, session_id)
        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving metrics: {str(e)}"
        )


@dashboard_router.get("/vendors")
async def get_vendor_breakdown(
    session_id: str,
    dashboard_service = Depends(get_dashboard_service),
    storage_manager = Depends(get_storage_manager_cached),
):
    """
    Get per-vendor breakdown with statistics.
    
    Returns: List of vendors with transaction counts, spending, and key metrics.
    """
    try:
        df = storage_manager.retrieve_data(session_id)

        if df is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )

        vendor_comparison = dashboard_service.get_vendor_comparison_data(df)
        return {"session_id": session_id, "vendors": vendor_comparison}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving vendor data: {str(e)}"
        )


@dashboard_router.get("/price-trends")
async def get_price_trends(
    session_id: str,
    dashboard_service = Depends(get_dashboard_service),
    storage_manager = Depends(get_storage_manager_cached),
):
    """
    Get price discrepancy trends by vendor.
    
    Returns: Min, max, and average price discrepancy for each vendor.
    """
    try:
        df = storage_manager.retrieve_data(session_id)

        if df is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )

        trend_data = dashboard_service.get_price_trend_data(df)
        return {
            "session_id": session_id,
            "metric": "price_discrepancy",
            "unit": "currency",
            "data": trend_data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trend data: {str(e)}"
        )


@dashboard_router.get("/delay-distribution")
async def get_delay_distribution(
    session_id: str,
    dashboard_service = Depends(get_dashboard_service),
    storage_manager = Depends(get_storage_manager_cached),
):
    """
    Get delay distribution by vendor and time ranges.
    
    Returns: Histogram data showing count of shipments in each delay range.
    """
    try:
        df = storage_manager.retrieve_data(session_id)

        if df is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )

        distribution = dashboard_service.get_delay_distribution(df)
        return {
            "session_id": session_id,
            "metric": "delay",
            "unit": "days",
            "data": distribution,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving distribution data: {str(e)}"
        )


@dashboard_router.get("/performance-matrix")
async def get_performance_matrix(
    session_id: str,
    dashboard_service = Depends(get_dashboard_service),
    storage_manager = Depends(get_storage_manager_cached),
):
    """
    Get vendor performance matrix (heatmap data).
    
    Returns: Scores for price accuracy, timeliness, and combined performance.
    """
    try:
        df = storage_manager.retrieve_data(session_id)

        if df is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )

        matrix = dashboard_service.get_vendor_performance_matrix(df)
        return {
            "session_id": session_id,
            "data": matrix,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving performance matrix: {str(e)}"
        )
