import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { User } from '../store/slices/authSlice';
import { Facility, Booking } from '../store/slices/facilitiesSlice';
import { Notification } from '../store/slices/notificationsSlice';

// Базовый URL для API
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Создаем экземпляр axios
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для добавления токена авторизации
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерцептор для обработки ответов
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Токен истек или недействителен
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Типы для API ответов
interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

interface RegisterRequest {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}

interface RegisterResponse {
  user: User;
  message: string;
}

// API методы для аутентификации
export const authAPI = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response: AxiosResponse<LoginResponse> = await apiClient.post('/auth/login/', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response: AxiosResponse<RegisterResponse> = await apiClient.post('/auth/register/', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout/');
    localStorage.removeItem('token');
  },

  refreshToken: async (refreshToken: string): Promise<{ access: string }> => {
    const response = await apiClient.post('/auth/token/refresh/', {
      refresh: refreshToken,
    });
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response: AxiosResponse<User> = await apiClient.get('/auth/user/');
    return response.data;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response: AxiosResponse<User> = await apiClient.patch('/auth/user/', data);
    return response.data;
  },
};

// API методы для работы с объектами
export const facilitiesAPI = {
  getAll: async (): Promise<Facility[]> => {
    const response: AxiosResponse<Facility[]> = await apiClient.get('/facilities/');
    return response.data;
  },

  getById: async (id: number): Promise<Facility> => {
    const response: AxiosResponse<Facility> = await apiClient.get(`/facilities/${id}/`);
    return response.data;
  },

  create: async (data: Omit<Facility, 'id' | 'created_at' | 'updated_at'>): Promise<Facility> => {
    const response: AxiosResponse<Facility> = await apiClient.post('/facilities/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Facility>): Promise<Facility> => {
    const response: AxiosResponse<Facility> = await apiClient.patch(`/facilities/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/facilities/${id}/`);
  },

  search: async (query: string): Promise<Facility[]> => {
    const response: AxiosResponse<Facility[]> = await apiClient.get(`/facilities/search/?q=${query}`);
    return response.data;
  },
};

// API методы для работы с бронированиями
export const bookingsAPI = {
  getAll: async (): Promise<Booking[]> => {
    const response: AxiosResponse<Booking[]> = await apiClient.get('/bookings/');
    return response.data;
  },

  getById: async (id: number): Promise<Booking> => {
    const response: AxiosResponse<Booking> = await apiClient.get(`/bookings/${id}/`);
    return response.data;
  },

  create: async (data: Omit<Booking, 'id' | 'created_at'>): Promise<Booking> => {
    const response: AxiosResponse<Booking> = await apiClient.post('/bookings/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Booking>): Promise<Booking> => {
    const response: AxiosResponse<Booking> = await apiClient.patch(`/bookings/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/bookings/${id}/`);
  },

  approve: async (id: number): Promise<Booking> => {
    const response: AxiosResponse<Booking> = await apiClient.post(`/bookings/${id}/approve/`);
    return response.data;
  },

  reject: async (id: number, reason?: string): Promise<Booking> => {
    const response: AxiosResponse<Booking> = await apiClient.post(`/bookings/${id}/reject/`, {
      reason,
    });
    return response.data;
  },

  cancel: async (id: number): Promise<Booking> => {
    const response: AxiosResponse<Booking> = await apiClient.post(`/bookings/${id}/cancel/`);
    return response.data;
  },

  getByFacility: async (facilityId: number): Promise<Booking[]> => {
    const response: AxiosResponse<Booking[]> = await apiClient.get(`/facilities/${facilityId}/bookings/`);
    return response.data;
  },

  getMyBookings: async (): Promise<Booking[]> => {
    const response: AxiosResponse<Booking[]> = await apiClient.get('/bookings/my/');
    return response.data;
  },
};

// API методы для работы с уведомлениями
export const notificationsAPI = {
  getAll: async (): Promise<Notification[]> => {
    const response: AxiosResponse<Notification[]> = await apiClient.get('/notifications/');
    return response.data;
  },

  markAsRead: async (id: number): Promise<Notification> => {
    const response: AxiosResponse<Notification> = await apiClient.patch(`/notifications/${id}/`, {
      is_read: true,
    });
    return response.data;
  },

  markAllAsRead: async (): Promise<void> => {
    await apiClient.post('/notifications/mark-all-read/');
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/notifications/${id}/`);
  },

  getUnreadCount: async (): Promise<{ count: number }> => {
    const response = await apiClient.get('/notifications/unread-count/');
    return response.data;
  },
};

// API методы для статистики и отчетов
export const statsAPI = {
  getDashboardStats: async (): Promise<{
    total_facilities: number;
    active_bookings: number;
    pending_bookings: number;
    total_users: number;
  }> => {
    const response = await apiClient.get('/stats/dashboard/');
    return response.data;
  },

  getFacilityUsage: async (facilityId?: number): Promise<any> => {
    const url = facilityId ? `/stats/facility-usage/${facilityId}/` : '/stats/facility-usage/';
    const response = await apiClient.get(url);
    return response.data;
  },

  getBookingTrends: async (period: 'week' | 'month' | 'year' = 'month'): Promise<any> => {
    const response = await apiClient.get(`/stats/booking-trends/?period=${period}`);
    return response.data;
  },
};

export default apiClient;