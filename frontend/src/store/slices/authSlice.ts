import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'ADMIN' | 'MANAGER' | 'EXECUTOR' | 'VIEWER' | 'ENGINEER' | 'EXECUTIVE' | 'CUSTOMER';
  phone?: string;
  department?: string;
  position?: string;
  avatar?: string;
  is_active: boolean;
  date_joined: string;
  // Role checking properties
  is_admin: boolean;
  is_manager: boolean;
  is_executor: boolean;
  is_engineer: boolean;
  is_executive: boolean;
  is_customer: boolean;
  // Permission checking properties
  can_create_defects: boolean;
  can_assign_defects: boolean;
  can_assign_tasks: boolean;
  can_control_deadlines: boolean;
  can_generate_reports: boolean;
  can_update_info: boolean;
  can_view_progress: boolean;
  can_view_reports: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false, // Изначально false, будет установлено в true после проверки токена
  isLoading: !!localStorage.getItem('token'), // Показываем загрузку если есть токен для проверки
  error: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.isLoading = false;
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.isAuthenticated = true;
      state.error = null;
      localStorage.setItem('token', action.payload.token);
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
      state.isAuthenticated = false;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.error = null;
      localStorage.removeItem('token');
    },
    clearError: (state) => {
      state.error = null;
    },
    updateUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
    },
    registerStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    registerSuccess: (state, action: PayloadAction<{ user: User; token?: string }>) => {
      state.isLoading = false;
      state.user = action.payload.user;
      if (action.payload.token) {
        state.token = action.payload.token;
        state.isAuthenticated = true;
        localStorage.setItem('token', action.payload.token);
      }
      state.error = null;
    },
    registerFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
      state.isAuthenticated = false;
    },
    // Token verification actions
    verifyTokenStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    verifyTokenSuccess: (state, action: PayloadAction<User>) => {
      state.isLoading = false;
      state.user = action.payload;
      state.isAuthenticated = true;
      state.error = null;
    },
    verifyTokenFailure: (state) => {
      state.isLoading = false;
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.error = null;
      localStorage.removeItem('token');
    },
  },
});

export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  clearError,
  updateUser,
  registerStart,
  registerSuccess,
  registerFailure,
  verifyTokenStart,
  verifyTokenSuccess,
  verifyTokenFailure,
} = authSlice.actions;

export default authSlice.reducer;