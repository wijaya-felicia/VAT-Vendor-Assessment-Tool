import { create } from 'zustand'
import { authService } from '@/lib/auth'
import type { UserProfile } from '@/types/api'

interface AuthState {
  user: UserProfile | null
  token: string | null
  isLoading: boolean
  setUser: (user: UserProfile, token: string) => void
  logout: () => void
  checkAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: true,

  setUser: (user, token) => {
    authService.saveUser(user)
    authService.saveToken(token)
    set({ user, token, isLoading: false })
  },

  logout: () => {
    authService.clearToken()
    set({ user: null, token: null, isLoading: false })
  },

  checkAuth: () => {
    const token = authService.getToken()
    const user = authService.getUser()
    set({ user, token, isLoading: false })
  },
}))
