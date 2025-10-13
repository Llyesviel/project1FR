import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Box, CircularProgress } from '@mui/material';
import { RootState } from './store/store';
import { verifyToken } from './store/thunks/authThunks';
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import UnifiedDashboard from './pages/Dashboard/UnifiedDashboard';
import ParcelTracking from './pages/Dashboard/ParcelTracking';
import Facilities from './pages/Facilities/Facilities';
import Bookings from './pages/Bookings/Bookings';
import Profile from './pages/Profile/Profile';
import PersonalAccount from './pages/Profile/PersonalAccount';
import CreateProject from './pages/Projects/CreateProject';
import CreateTask from './pages/Tasks/CreateTask';
import CreateReport from './pages/Reports/CreateReport';
import CreateDefect from './pages/Defects/CreateDefect';
import Unauthorized from './pages/Unauthorized';
import NotFound from './pages/NotFound/NotFound';

// Компонент для выбора правильного дашборда в зависимости от роли
const RoleDashboard: React.FC = () => {
  const { user, isLoading } = useSelector((state: RootState) => state.auth);
  
  // Показываем загрузку пока проверяется аутентификация
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (!user) return <Navigate to="/login" replace />;
  
  // Используем единый компонент для всех ролей
  return <UnifiedDashboard />;
};

const App: React.FC = () => {
  const dispatch = useDispatch();
  const { isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth);

  // Verify token on app startup
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      dispatch(verifyToken() as any);
    }
  }, [dispatch]);

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Routes>
        {/* Публичные маршруты */}
        <Route 
          path="/login" 
          element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" replace />} 
        />
        <Route 
          path="/register" 
          element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" replace />} 
        />
        
        {/* Защищенные маршруты */}
        <Route 
          path="/*" 
          element={
            isAuthenticated ? (
              <Layout>
                <Routes>
                  <Route path="/dashboard" element={<RoleDashboard />} />
                  
                  {/* Роль-специфичные дашборды - теперь все используют UnifiedDashboard */}
                  <Route 
                    path="/manager-dashboard" 
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                        <UnifiedDashboard />
                      </ProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/engineer-dashboard" 
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN', 'ENGINEER']}>
                        <UnifiedDashboard />
                      </ProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/executive-dashboard" 
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN', 'EXECUTIVE']}>
                        <UnifiedDashboard />
                      </ProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/customer-dashboard" 
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN', 'CUSTOMER']}>
                        <UnifiedDashboard />
                      </ProtectedRoute>
                    } 
                  />
                  
                  <Route path="/facilities" element={<Facilities />} />
                  <Route path="/bookings" element={<Bookings />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/account" element={<PersonalAccount />} />
                  
                  {/* Creation pages */}
                  <Route path="/create-project" element={<CreateProject />} />
                  <Route path="/create-task" element={<CreateTask />} />
                  <Route path="/create-report" element={<CreateReport />} />
                  <Route path="/create-defect" element={<CreateDefect />} />
                  
                  <Route path="/unauthorized" element={<Unauthorized />} />
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Layout>
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />
      </Routes>
    </Box>
  );
};

export default App;