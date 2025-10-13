import { useSelector } from 'react-redux';
import { useMemo } from 'react';
import { RootState } from '../store/store';
import { User } from '../store/slices/authSlice';

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  // Role checking methods
  isAdmin: () => boolean;
  isManager: () => boolean;
  isExecutor: () => boolean;
  isEngineer: () => boolean;
  isExecutive: () => boolean;
  isCustomer: () => boolean;
  // Permission checking methods
  canCreateDefects: () => boolean;
  canAssignDefects: () => boolean;
  canAssignTasks: () => boolean;
  canControlDeadlines: () => boolean;
  canGenerateReports: () => boolean;
  canUpdateInfo: () => boolean;
  canViewProgress: () => boolean;
  canViewReports: () => boolean;
  // Utility methods
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
}

export const useAuth = (): UseAuthReturn => {
  const { user, isAuthenticated, isLoading, error } = useSelector(
    (state: RootState) => state.auth
  );

  return useMemo(() => {
    // Role checking methods
    const isAdmin = () => user?.is_admin || false;
    const isManager = () => user?.is_manager || false;
    const isExecutor = () => user?.is_executor || false;
    const isEngineer = () => user?.is_engineer || false;
    const isExecutive = () => user?.is_executive || false;
    const isCustomer = () => user?.is_customer || false;

    // Permission checking methods
    const canCreateDefects = () => user?.can_create_defects || false;
    const canAssignDefects = () => user?.can_assign_defects || false;
    const canAssignTasks = () => user?.can_assign_tasks || false;
    const canControlDeadlines = () => user?.can_control_deadlines || false;
    const canGenerateReports = () => user?.can_generate_reports || false;
    const canUpdateInfo = () => user?.can_update_info || false;
    const canViewProgress = () => user?.can_view_progress || false;
    const canViewReports = () => user?.can_view_reports || false;

    // Utility methods
    const hasRole = (role: string): boolean => {
      if (!user) return false;
      
      switch (role) {
        case 'ADMIN':
          return user.is_admin;
        case 'MANAGER':
          return user.is_manager;
        case 'EXECUTOR':
          return user.is_executor;
        case 'ENGINEER':
          return user.is_engineer;
        case 'EXECUTIVE':
          return user.is_executive;
        case 'CUSTOMER':
          return user.is_customer;
        default:
          return user.role === role;
      }
    };

    const hasPermission = (permission: string): boolean => {
      if (!user) return false;
      
      switch (permission) {
        case 'can_create_defects':
          return user.can_create_defects;
        case 'can_assign_defects':
          return user.can_assign_defects;
        case 'can_assign_tasks':
          return user.can_assign_tasks;
        case 'can_control_deadlines':
          return user.can_control_deadlines;
        case 'can_generate_reports':
          return user.can_generate_reports;
        case 'can_update_info':
          return user.can_update_info;
        case 'can_view_progress':
          return user.can_view_progress;
        case 'can_view_reports':
          return user.can_view_reports;
        default:
          return false;
      }
    };

    const hasAnyRole = (roles: string[]): boolean => {
      return roles.some(role => hasRole(role));
    };

    const hasAllPermissions = (permissions: string[]): boolean => {
      return permissions.every(permission => hasPermission(permission));
    };

    return {
      user,
      isAuthenticated,
      isLoading,
      error,
      isAdmin,
      isManager,
      isExecutor,
      isEngineer,
      isExecutive,
      isCustomer,
      canCreateDefects,
      canAssignDefects,
      canAssignTasks,
      canControlDeadlines,
      canGenerateReports,
      canUpdateInfo,
      canViewProgress,
      canViewReports,
      hasRole,
      hasPermission,
      hasAnyRole,
      hasAllPermissions,
    };
  }, [user, isAuthenticated, isLoading, error]);
};