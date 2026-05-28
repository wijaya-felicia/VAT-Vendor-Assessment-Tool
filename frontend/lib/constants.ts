export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const API_ENDPOINTS = {
  AUTH: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    PROFILE: '/auth/profile',
    REFRESH: '/auth/refresh',
  },
  UPLOAD: '/upload',
  DASHBOARD: {
    METRICS: '/dashboard/metrics',
    VENDORS: '/dashboard/vendors',
    PRICE_TRENDS: '/dashboard/price-trends',
    DELAY_DISTRIBUTION: '/dashboard/delay-distribution',
    PERFORMANCE_MATRIX: '/dashboard/performance-matrix',
  },
  BHM: {
    RANKINGS: '/bhm/rankings',
    VENDOR_DETAIL: '/bhm/vendor',
    LOCK_MODEL: '/bhm/model/lock',
    LATEST_SESSION: '/bhm/latest-session',
  },
}
