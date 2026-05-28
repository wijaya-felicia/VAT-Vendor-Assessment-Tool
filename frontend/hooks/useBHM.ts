import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { API_ENDPOINTS } from '@/lib/constants'
import type { BHMRankingsResponse, BHMVendorDetailResponse, ModelLockResponse } from '@/types/api'

export const useBHMRankings = (sessionId: string | null) => {
  return useQuery({
    queryKey: ['bhm-rankings', sessionId],
    queryFn: async () => {
      const response = await api.get<BHMRankingsResponse>(
        API_ENDPOINTS.BHM.RANKINGS,
        { params: { session_id: sessionId } }
      )
      return response.data
    },
    enabled: !!sessionId,
    retry: 1,
  })
}

export const useBHMVendorDetail = (sessionId: string | null, vendorName: string | null) => {
  return useQuery({
    queryKey: ['bhm-vendor-detail', sessionId, vendorName],
    queryFn: async () => {
      const response = await api.get<BHMVendorDetailResponse>(
        `${API_ENDPOINTS.BHM.VENDOR_DETAIL}/${vendorName}`,
        { params: { session_id: sessionId } }
      )
      return response.data
    },
    enabled: !!sessionId && !!vendorName,
    retry: 1,
  })
}

export const useLockModel = () => {
  return useMutation({
    mutationFn: async (modelYear: string) => {
      const response = await api.post<ModelLockResponse>(
        API_ENDPOINTS.BHM.LOCK_MODEL,
        { model_year: modelYear, description: `Audit year ${modelYear}` }
      )
      return response.data
    },
  })
}
