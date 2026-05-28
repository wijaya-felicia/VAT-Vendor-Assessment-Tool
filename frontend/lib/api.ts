import axios, { AxiosInstance, AxiosError } from 'axios'
import { API_BASE_URL } from './constants'
import { authService } from './auth'

export const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor: Add auth token
  client.interceptors.request.use(
    (config) => {
      const token = authService.getToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      console.log('🔵 API Request:', config.method?.toUpperCase(), config.url)
      return config
    },
    (error) => Promise.reject(error)
  )

  // Response interceptor: Handle errors
  client.interceptors.response.use(
    (response) => {
      console.log('✅ API Success:', response.status, response.config.url)
      return response
    },
    (error: AxiosError) => {
      console.error('❌ API Error:', error.response?.status, error.response?.data)
      
      // Handle 401 - Unauthorized
      if (error.response?.status === 401) {
        authService.clearToken()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }
      
      return Promise.reject(error)
    }
  )

  return client
}

export const api = createApiClient()
