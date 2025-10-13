import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
  fallbackPath?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles = [],
  requiredPermissions = [],
  fallbackPath = '/login'
}) => {
  const location = useLocation();
  const { user, isAuthenticated } = useSelector((state: RootState) => state.auth);

  // Если пользователь не аутентифицирован
  if (!isAuthenticated || !user) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />;
  }

  // Проверка ролей
  if (requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.some(role => {
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
    });

    if (!hasRequiredRole) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  // Проверка разрешений
  if (requiredPermissions.length > 0) {
    const hasRequiredPermission = requiredPermissions.every(permission => {
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
    });

    if (!hasRequiredPermission) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;