// 用户认证相关类型
export interface User {
  id: string
  username: string
  email: string
  full_name?: string
  is_active: boolean
  is_verified: boolean
  role: {
    name: string
    display_name: string
    permissions?: string[]
  }
  created_at: string
  last_login_at?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}