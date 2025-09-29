import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { CircularProgress, Box } from '@mui/material';

interface ProtectedRouteProps {
  children: React.ReactNode;
  adminOnly?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, adminOnly = false }) => {
  const { user, isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth);
  const location = useLocation();

  // Показываем загрузку, пока проверяется аутентификация
  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  // Если пользователь не аутентифицирован, перенаправляем на страницу входа
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Если требуются права администратора, но пользователь не админ
  if (adminOnly && user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;