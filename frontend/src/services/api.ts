import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { User } from '../store/slices/authSlice';
import { Facility, Booking } from '../store/slices/facilitiesSlice';
import { Notification } from '../store/slices/notificationsSlice';

// Типы для дефектов и задач
export interface Defect {
  id: number;
  title: string;
  description: string;
  facility: number;
  facility_name?: string;
  status: 'new' | 'in_progress' | 'testing' | 'resolved' | 'closed' | 'rejected';
  severity: 'low' | 'medium' | 'high' | 'critical';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  reported_by: number;
  reported_by_name?: string;
  assigned_to?: number;
  assigned_to_name?: string;
  location?: string;
  estimated_cost?: number;
  actual_cost?: number;
  due_date?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
  is_overdue: boolean;
}

export interface Task {
  id: number;
  title: string;
  description: string;
  project: number;
  project_name?: string;
  facility?: number;
  facility_name?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'overdue' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_to?: number;
  assigned_to_name?: string;
  created_by: number;
  created_by_name?: string;
  due_date?: string;
  completed_at?: string;
  estimated_hours?: number;
  actual_hours?: number;
  created_at: string;
  updated_at: string;
  is_overdue: boolean;
  progress_percentage: number;
}

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
  email: string;
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
  password_confirm: string;
  role?: string;
  phone?: string;
  position?: string;
  department?: string;
}

interface RegisterResponse {
  user: User;
  message: string;
}

// API методы для аутентификации
export const authAPI = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response: AxiosResponse<LoginResponse> = await apiClient.post('/auth/token/', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response: AxiosResponse<RegisterResponse> = await apiClient.post('/auth/users/', data);
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
    const response: AxiosResponse<User> = await apiClient.get('/auth/users/me/');
    return response.data;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response: AxiosResponse<User> = await apiClient.patch('/auth/users/me/', data);
    return response.data;
  },

  changePassword: async (data: { current_password: string; new_password: string }): Promise<{ message: string }> => {
    const response = await apiClient.post('/auth/users/change_password/', {
      old_password: data.current_password,
      new_password: data.new_password,
      new_password_confirm: data.new_password,
    });
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

  getAllBookings: async (): Promise<Booking[]> => {
    const response: AxiosResponse<Booking[]> = await apiClient.get('/bookings/all/');
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

  updateBookingStatus: async (id: number, status: string): Promise<Booking> => {
    const response: AxiosResponse<Booking> = await apiClient.patch(`/bookings/${id}/`, { status });
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
    total_defects: number;
    active_tasks: number;
    total_users: number;
    critical_defects: number;
    overdue_tasks: number;
    active_bookings?: number;
    pending_bookings?: number;
  }> => {
    const response = await apiClient.get('/reports/api/stats/dashboard/');
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

// API методы для работы с дефектами
export const defectsAPI = {
  getAll: async (params?: {
    status?: string;
    severity?: string;
    priority?: string;
    facility?: number;
    assigned_to?: number;
    search?: string;
    ordering?: string;
  }): Promise<{ results: Defect[]; count: number }> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const response = await apiClient.get(`/defects/api/defects/?${queryParams.toString()}`);
    return response.data;
  },

  getById: async (id: number): Promise<Defect> => {
    const response: AxiosResponse<Defect> = await apiClient.get(`/defects/api/defects/${id}/`);
    return response.data;
  },

  create: async (data: Omit<Defect, 'id' | 'created_at' | 'updated_at' | 'is_overdue' | 'reported_by' | 'facility_name' | 'reported_by_name' | 'assigned_to_name'>): Promise<Defect> => {
    const response: AxiosResponse<Defect> = await apiClient.post('/defects/api/defects/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Defect>): Promise<Defect> => {
    const response: AxiosResponse<Defect> = await apiClient.patch(`/defects/api/defects/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/defects/api/defects/${id}/`);
  },

  updateStatus: async (id: number, status: Defect['status']): Promise<Defect> => {
    const response: AxiosResponse<Defect> = await apiClient.patch(`/defects/api/defects/${id}/update_status/`, { status });
    return response.data;
  },

  assign: async (id: number, assigned_to: number): Promise<Defect> => {
    const response: AxiosResponse<Defect> = await apiClient.patch(`/defects/api/defects/${id}/assign/`, { assigned_to });
    return response.data;
  },

  getMyDefects: async (): Promise<Defect[]> => {
    const response: AxiosResponse<Defect[]> = await apiClient.get('/defects/api/defects/my_defects/');
    return response.data;
  },

  getOverdue: async (): Promise<Defect[]> => {
    const response: AxiosResponse<Defect[]> = await apiClient.get('/defects/api/defects/overdue/');
    return response.data;
  },
};

// API методы для работы с задачами
export const tasksAPI = {
  getAll: async (params?: {
    status?: string;
    priority?: string;
    project?: number;
    facility?: number;
    assigned_to?: number;
    search?: string;
    ordering?: string;
  }): Promise<{ results: Task[]; count: number }> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const response = await apiClient.get(`/projects/api/tasks/?${queryParams.toString()}`);
    return response.data;
  },

  getById: async (id: number): Promise<Task> => {
    const response: AxiosResponse<Task> = await apiClient.get(`/projects/api/tasks/${id}/`);
    return response.data;
  },

  create: async (data: Omit<Task, 'id' | 'created_at' | 'updated_at' | 'is_overdue' | 'progress_percentage' | 'created_by' | 'project_name' | 'facility_name' | 'assigned_to_name' | 'created_by_name'>): Promise<Task> => {
    const response: AxiosResponse<Task> = await apiClient.post('/projects/api/tasks/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Task>): Promise<Task> => {
    const response: AxiosResponse<Task> = await apiClient.patch(`/projects/api/tasks/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/projects/api/tasks/${id}/`);
  },

  updateStatus: async (id: number, status: Task['status']): Promise<Task> => {
    const response: AxiosResponse<Task> = await apiClient.patch(`/projects/api/tasks/${id}/update_status/`, { status });
    return response.data;
  },

  assign: async (id: number, assigned_to: number): Promise<Task> => {
    const response: AxiosResponse<Task> = await apiClient.patch(`/projects/api/tasks/${id}/assign/`, { assigned_to });
    return response.data;
  },

  getMyTasks: async (): Promise<Task[]> => {
    const response: AxiosResponse<Task[]> = await apiClient.get('/projects/api/tasks/my_tasks/');
    return response.data;
  },

  getOverdue: async (): Promise<Task[]> => {
    const response: AxiosResponse<Task[]> = await apiClient.get('/projects/api/tasks/overdue/');
    return response.data;
  },

  getByProject: async (projectId: number): Promise<Task[]> => {
    const response: AxiosResponse<Task[]> = await apiClient.get(`/projects/api/tasks/by_project/?project_id=${projectId}`);
    return response.data;
  },
};

export default apiClient;