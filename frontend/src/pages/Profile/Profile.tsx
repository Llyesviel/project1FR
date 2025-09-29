import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Avatar,
  Divider,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Work as WorkIcon,
  EventNote as EventNoteIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store/store';
import { updateUser } from '../../store/slices/authSlice';
import { useQuery, useMutation } from 'react-query';
import { authAPI, bookingsAPI } from '../../services/api';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';

const profileValidationSchema = Yup.object({
  first_name: Yup.string().required('Имя обязательно'),
  last_name: Yup.string().required('Фамилия обязательна'),
  email: Yup.string().email('Неверный формат email').required('Email обязателен'),
  phone: Yup.string(),
  department: Yup.string(),
});

const passwordValidationSchema = Yup.object({
  current_password: Yup.string().required('Введите текущий пароль'),
  new_password: Yup.string()
    .min(8, 'Пароль должен содержать минимум 8 символов')
    .required('Введите новый пароль'),
  confirm_password: Yup.string()
    .oneOf([Yup.ref('new_password')], 'Пароли не совпадают')
    .required('Подтвердите новый пароль'),
});

const Profile: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const dispatch = useDispatch();
  
  const [isEditing, setIsEditing] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);

  // Получение истории бронирований пользователя
  const {
    data: userBookings,
    isLoading: bookingsLoading,
  } = useQuery('userBookings', bookingsAPI.getMyBookings);

  // Мутация для обновления профиля
  const updateProfileMutation = useMutation(authAPI.updateProfile, {
    onSuccess: (data) => {
      dispatch(updateUser(data));
      setIsEditing(false);
    },
  });

  // Мутация для смены пароля
  const changePasswordMutation = useMutation(authAPI.changePassword, {
    onSuccess: () => {
      setPasswordDialogOpen(false);
    },
  });

  const handleProfileSubmit = (values: any) => {
    updateProfileMutation.mutate(values);
  };

  const handlePasswordSubmit = (values: any) => {
    changePasswordMutation.mutate({
      current_password: values.current_password,
      new_password: values.new_password,
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'success';
      case 'pending': return 'warning';
      case 'rejected': return 'error';
      case 'cancelled': return 'default';
      default: return 'default';
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

  const getBookingStats = () => {
    if (!userBookings) return { total: 0, approved: 0, pending: 0, rejected: 0 };
    
    return {
      total: userBookings.length,
      approved: userBookings.filter(b => b.status === 'approved').length,
      pending: userBookings.filter(b => b.status === 'pending').length,
      rejected: userBookings.filter(b => b.status === 'rejected').length,
    };
  };

  const stats = getBookingStats();

  if (!user) {
    return (
      <Alert severity="error">
        Пользователь не найден
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Профиль пользователя
      </Typography>

      <Grid container spacing={3}>
        {/* Основная информация */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6">
                  Личная информация
                </Typography>
                {!isEditing ? (
                  <Button
                    startIcon={<EditIcon />}
                    onClick={() => setIsEditing(true)}
                  >
                    Редактировать
                  </Button>
                ) : (
                  <Button
                    startIcon={<CancelIcon />}
                    onClick={() => setIsEditing(false)}
                    color="secondary"
                  >
                    Отмена
                  </Button>
                )}
              </Box>

              {updateProfileMutation.error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  Ошибка обновления профиля
                </Alert>
              )}

              {updateProfileMutation.isSuccess && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  Профиль успешно обновлен
                </Alert>
              )}

              <Formik
                initialValues={{
                  first_name: user.first_name || '',
                  last_name: user.last_name || '',
                  email: user.email || '',
                  phone: user.phone || '',
                  department: user.department || '',
                }}
                validationSchema={profileValidationSchema}
                onSubmit={handleProfileSubmit}
                enableReinitialize
              >
                {({ errors, touched }) => (
                  <Form>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Field
                          as={TextField}
                          name="first_name"
                          label="Имя"
                          fullWidth
                          disabled={!isEditing}
                          error={touched.first_name && !!errors.first_name}
                          helperText={touched.first_name && errors.first_name}
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Field
                          as={TextField}
                          name="last_name"
                          label="Фамилия"
                          fullWidth
                          disabled={!isEditing}
                          error={touched.last_name && !!errors.last_name}
                          helperText={touched.last_name && errors.last_name}
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <Field
                          as={TextField}
                          name="email"
                          label="Email"
                          type="email"
                          fullWidth
                          disabled={!isEditing}
                          error={touched.email && !!errors.email}
                          helperText={touched.email && errors.email}
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Field
                          as={TextField}
                          name="phone"
                          label="Телефон"
                          fullWidth
                          disabled={!isEditing}
                          error={touched.phone && !!errors.phone}
                          helperText={touched.phone && errors.phone}
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Field
                          as={TextField}
                          name="department"
                          label="Отдел"
                          fullWidth
                          disabled={!isEditing}
                          error={touched.department && !!errors.department}
                          helperText={touched.department && errors.department}
                        />
                      </Grid>
                    </Grid>

                    {isEditing && (
                      <Box mt={3} display="flex" gap={2}>
                        <Button
                          type="submit"
                          variant="contained"
                          startIcon={<SaveIcon />}
                          disabled={updateProfileMutation.isLoading}
                        >
                          {updateProfileMutation.isLoading ? (
                            <CircularProgress size={20} />
                          ) : (
                            'Сохранить'
                          )}
                        </Button>
                      </Box>
                    )}
                  </Form>
                )}
              </Formik>
            </CardContent>
          </Card>
        </Grid>

        {/* Боковая панель */}
        <Grid item xs={12} md={4}>
          {/* Аватар и основная информация */}
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{
                  width: 100,
                  height: 100,
                  mx: 'auto',
                  mb: 2,
                  bgcolor: 'primary.main',
                  fontSize: '2rem',
                }}
              >
                {user.first_name?.[0] || user.username?.[0] || 'U'}
              </Avatar>
              <Typography variant="h6" gutterBottom>
                {user.first_name && user.last_name
                  ? `${user.first_name} ${user.last_name}`
                  : user.username}
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                {user.role === 'admin' ? 'Администратор' : 'Пользователь'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Регистрация: {new Date(user.date_joined).toLocaleDateString('ru-RU')}
              </Typography>
            </CardContent>
          </Card>

          {/* Статистика бронирований */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Статистика бронирований
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <EventNoteIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Всего бронирований"
                    secondary={stats.total}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Подтверждено"
                    secondary={
                      <Chip
                        label={stats.approved}
                        color="success"
                        size="small"
                      />
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Ожидает подтверждения"
                    secondary={
                      <Chip
                        label={stats.pending}
                        color="warning"
                        size="small"
                      />
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Отклонено"
                    secondary={
                      <Chip
                        label={stats.rejected}
                        color="error"
                        size="small"
                      />
                    }
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          {/* Безопасность */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Безопасность
              </Typography>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<SecurityIcon />}
                onClick={() => setPasswordDialogOpen(true)}
              >
                Изменить пароль
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* История бронирований */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Последние бронирования
              </Typography>
              {bookingsLoading ? (
                <CircularProgress />
              ) : userBookings && userBookings.length > 0 ? (
                <List>
                  {userBookings.slice(0, 5).map((booking, index) => (
                    <React.Fragment key={booking.id}>
                      <ListItem>
                        <ListItemText
                          primary={`Объект #${booking.facility}`}
                          secondary={
                            <>
                              <Typography variant="body2" color="textSecondary">
                                {new Date(booking.start_time).toLocaleDateString('ru-RU')} - {booking.purpose}
                              </Typography>
                            </>
                          }
                        />
                        <Chip
                          label={getStatusText(booking.status)}
                          color={getStatusColor(booking.status) as any}
                          size="small"
                        />
                      </ListItem>
                      {index < Math.min(userBookings.length - 1, 4) && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary">
                  Нет бронирований
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Диалог смены пароля */}
      <Dialog open={passwordDialogOpen} onClose={() => setPasswordDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Изменить пароль</DialogTitle>
        <Formik
          initialValues={{
            current_password: '',
            new_password: '',
            confirm_password: '',
          }}
          validationSchema={passwordValidationSchema}
          onSubmit={handlePasswordSubmit}
        >
          {({ errors, touched }) => (
            <Form>
              <DialogContent>
                {changePasswordMutation.error && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    Ошибка смены пароля
                  </Alert>
                )}
                
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Field
                      as={TextField}
                      name="current_password"
                      label="Текущий пароль"
                      type="password"
                      fullWidth
                      error={touched.current_password && !!errors.current_password}
                      helperText={touched.current_password && errors.current_password}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Field
                      as={TextField}
                      name="new_password"
                      label="Новый пароль"
                      type="password"
                      fullWidth
                      error={touched.new_password && !!errors.new_password}
                      helperText={touched.new_password && errors.new_password}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Field
                      as={TextField}
                      name="confirm_password"
                      label="Подтвердите новый пароль"
                      type="password"
                      fullWidth
                      error={touched.confirm_password && !!errors.confirm_password}
                      helperText={touched.confirm_password && errors.confirm_password}
                    />
                  </Grid>
                </Grid>
              </DialogContent>
              <DialogActions>
                <Button onClick={() => setPasswordDialogOpen(false)}>
                  Отмена
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={changePasswordMutation.isLoading}
                >
                  {changePasswordMutation.isLoading ? (
                    <CircularProgress size={20} />
                  ) : (
                    'Изменить пароль'
                  )}
                </Button>
              </DialogActions>
            </Form>
          )}
        </Formik>
      </Dialog>
    </Box>
  );
};

export default Profile;