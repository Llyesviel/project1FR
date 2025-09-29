import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Business as BusinessIcon,
  EventNote as EventNoteIcon,
  PendingActions as PendingIcon,
  People as PeopleIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { statsAPI, facilitiesAPI, bookingsAPI } from '../../services/api';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="h6">
            {title}
          </Typography>
          <Typography variant="h4" component="h2">
            {value}
          </Typography>
        </Box>
        <Box
          sx={{
            backgroundColor: color,
            borderRadius: '50%',
            width: 60,
            height: 60,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
          }}
        >
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const Dashboard: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);

  // Запросы для получения статистики
  const {
    data: dashboardStats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery('dashboardStats', statsAPI.getDashboardStats, {
    refetchInterval: 30000, // Обновляем каждые 30 секунд
  });

  const {
    data: recentFacilities,
    isLoading: facilitiesLoading,
  } = useQuery('recentFacilities', facilitiesAPI.getAll);

  const {
    data: myBookings,
    isLoading: bookingsLoading,
  } = useQuery('myBookings', bookingsAPI.getMyBookings);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Доброе утро';
    if (hour < 18) return 'Добрый день';
    return 'Добрый вечер';
  };

  const getRecentBookings = () => {
    if (!myBookings) return [];
    return myBookings
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5);
  };

  const getUpcomingBookings = () => {
    if (!myBookings) return [];
    const now = new Date();
    return myBookings
      .filter(booking => new Date(booking.start_time) > now && booking.status === 'approved')
      .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
      .slice(0, 3);
  };

  if (statsLoading || facilitiesLoading || bookingsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (statsError) {
    return (
      <Alert severity="error">
        Ошибка загрузки данных панели управления
      </Alert>
    );
  }

  return (
    <Box>
      {/* Приветствие */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          {getGreeting()}, {user?.first_name || user?.username}!
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Добро пожаловать в систему управления объектами
        </Typography>
      </Box>

      {/* Статистические карточки */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Всего объектов"
            value={dashboardStats?.total_facilities || 0}
            icon={<BusinessIcon />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Активные бронирования"
            value={dashboardStats?.active_bookings || 0}
            icon={<EventNoteIcon />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Ожидают подтверждения"
            value={dashboardStats?.pending_bookings || 0}
            icon={<PendingIcon />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Всего пользователей"
            value={dashboardStats?.total_users || 0}
            icon={<PeopleIcon />}
            color="#9c27b0"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Предстоящие бронирования */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '400px' }}>
            <Typography variant="h6" gutterBottom>
              Предстоящие бронирования
            </Typography>
            {getUpcomingBookings().length === 0 ? (
              <Typography color="textSecondary" sx={{ mt: 2 }}>
                Нет предстоящих бронирований
              </Typography>
            ) : (
              <Box sx={{ mt: 2 }}>
                {getUpcomingBookings().map((booking) => {
                  const facility = recentFacilities?.find(f => f.id === booking.facility);
                  return (
                    <Box
                      key={booking.id}
                      sx={{
                        p: 2,
                        mb: 2,
                        border: '1px solid #e0e0e0',
                        borderRadius: 1,
                      }}
                    >
                      <Typography variant="subtitle1" fontWeight="bold">
                        {facility?.name || `Объект #${booking.facility}`}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {new Date(booking.start_time).toLocaleString('ru-RU')} - 
                        {new Date(booking.end_time).toLocaleString('ru-RU')}
                      </Typography>
                      <Typography variant="body2">
                        {booking.purpose}
                      </Typography>
                    </Box>
                  );
                })}
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Последние бронирования */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '400px' }}>
            <Typography variant="h6" gutterBottom>
              Последние бронирования
            </Typography>
            {getRecentBookings().length === 0 ? (
              <Typography color="textSecondary" sx={{ mt: 2 }}>
                Нет бронирований
              </Typography>
            ) : (
              <Box sx={{ mt: 2 }}>
                {getRecentBookings().map((booking) => {
                  const facility = recentFacilities?.find(f => f.id === booking.facility);
                  const getStatusColor = (status: string) => {
                    switch (status) {
                      case 'approved': return '#2e7d32';
                      case 'pending': return '#ed6c02';
                      case 'rejected': return '#d32f2f';
                      case 'cancelled': return '#757575';
                      default: return '#757575';
                    }
                  };

                  const getStatusText = (status: string) => {
                    switch (status) {
                      case 'approved': return 'Подтверждено';
                      case 'pending': return 'Ожидает';
                      case 'rejected': return 'Отклонено';
                      case 'cancelled': return 'Отменено';
                      default: return status;
                    }
                  };

                  return (
                    <Box
                      key={booking.id}
                      sx={{
                        p: 2,
                        mb: 2,
                        border: '1px solid #e0e0e0',
                        borderRadius: 1,
                      }}
                    >
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle1" fontWeight="bold">
                          {facility?.name || `Объект #${booking.facility}`}
                        </Typography>
                        <Typography
                          variant="caption"
                          sx={{
                            color: getStatusColor(booking.status),
                            fontWeight: 'bold',
                          }}
                        >
                          {getStatusText(booking.status)}
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="textSecondary">
                        {new Date(booking.start_time).toLocaleDateString('ru-RU')}
                      </Typography>
                      <Typography variant="body2">
                        {booking.purpose}
                      </Typography>
                    </Box>
                  );
                })}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;