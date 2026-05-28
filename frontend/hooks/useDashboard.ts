import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { API_ENDPOINTS } from '@/lib/constants'
import type { DashboardMetrics, PriceTrendData, PerformanceMatrixData } from '@/types/api'

export const useDashboardMetrics = (sessionId: string | null) => {
  return useQuery({
    queryKey: ['dashboard-metrics', sessionId],
    queryFn: async () => {
      const response = await api.get<DashboardMetrics>(API_ENDPOINTS.DASHBOARD.METRICS, {
        params: { session_id: sessionId },
      })
      return response.data
    },
    enabled: !!sessionId,
    retry: 2,
  })
}

export const usePriceTrends = (sessionId: string | null) => {
  return useQuery({
    queryKey: ['price-trends', sessionId],
    queryFn: async () => {
      const response = await api.get<{ data: PriceTrendData[] }>(
        API_ENDPOINTS.DASHBOARD.PRICE_TRENDS,
        { params: { session_id: sessionId } }
      )
      return response.data.data
    },
    enabled: !!sessionId,
    retry: 2,
  })
}

export const usePerformanceMatrix = (sessionId: string | null) => {
  return useQuery({
    queryKey: ['performance-matrix', sessionId],
    queryFn: async () => {
      const response = await api.get<{ data: PerformanceMatrixData[] }>(
        API_ENDPOINTS.DASHBOARD.PERFORMANCE_MATRIX,
        { params: { session_id: sessionId } }
      )
      return response.data.data
    },
    enabled: !!sessionId,
    retry: 2,
  })
}

export const useDelayDistribution = (sessionId: string | null) => {
  return useQuery({
    queryKey: ['delay-distribution', sessionId],
    queryFn: async () => {
      const response = await api.get<{ data: any[] }>(
        API_ENDPOINTS.DASHBOARD.DELAY_DISTRIBUTION,
        { params: { session_id: sessionId } }
      )
      return response.data.data
    },
    enabled: !!sessionId,
    retry: 2,
  })
}
