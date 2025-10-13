import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  CircularProgress,
  Alert,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ru } from 'date-fns/locale';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { bookingsAPI, facilitiesAPI } from '../../services/api';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { Booking } from '../../store/slices/facilitiesSlice';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const bookingValidationSchema = Yup.object({
  facility: Yup.number().required('Выберите объект'),
  start_time: Yup.date().required('Выберите время начала'),
  end_time: Yup.date()
    .required('Выберите время окончания')
    .min(Yup.ref('start_time'), 'Время окончания должно быть позже времени начала'),
  purpose: Yup.string().required('Укажите цель бронирования'),
});

const Bookings: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const queryClient = useQueryClient();
  
  const [tabValue, setTabValue] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Получение данных
  const {
    data: bookings,
    isLoading: bookingsLoading,
    error: bookingsError,
  } = useQuery('bookings', 
    user?.role === 'ADMIN' ? bookingsAPI.getAll : bookingsAPI.getMyBookings
  );

  const {
    data: facilities,
    isLoading: facilitiesLoading,
  } = useQuery('facilities', facilitiesAPI.getAll);

  // Мутации
  const createMutation = useMutation(bookingsAPI.create, {
    onSuccess: () => {
      queryClient.invalidateQueries('bookings');
      setDialogOpen(false);
      setSelectedBooking(null);
    },
  });

  const updateMutation = useMutation(
    ({ id, data }: { id: number; data: any }) => bookingsAPI.update(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bookings');
        setDialogOpen(false);
        setSelectedBooking(null);
        setIsEditing(false);
      },
    }
  );

  const deleteMutation = useMutation(bookingsAPI.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries('bookings');
    },
  });

  const approveMutation = useMutation(bookingsAPI.approve, {
    onSuccess: () => {
      queryClient.invalidateQueries('bookings');
    },
  });

  const rejectMutation = useMutation(bookingsAPI.reject, {
    onSuccess: () => {
      queryClient.invalidateQueries('bookings');
    },
  });

  // Фильтрация бронирований по статусу
  const getFilteredBookings = (status?: string) => {
    if (!bookings) return [];
    if (!status) return bookings;
    return bookings.filter(booking => booking.status === status);
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

  const handleCreate = () => {
    setSelectedBooking(null);
    setIsEditing(false);
    setDialogOpen(true);
  };

  const handleEdit = (booking: Booking) => {
    setSelectedBooking(booking);
    setIsEditing(true);
    setDialogOpen(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Вы уверены, что хотите удалить это бронирование?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleApprove = (id: number) => {
    approveMutation.mutate(id);
  };

  const handleReject = (id: number) => {
    if (window.confirm('Вы уверены, что хотите отклонить это бронирование?')) {
      rejectMutation.mutate(id);
    }
  };

  const handleSubmit = (values: any) => {
    if (isEditing && selectedBooking) {
      updateMutation.mutate({ id: selectedBooking.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const renderBookingsTable = (bookingsList: Booking[]) => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Объект</TableCell>
            <TableCell>Время начала</TableCell>
            <TableCell>Время окончания</TableCell>
            <TableCell>Цель</TableCell>
            <TableCell>Статус</TableCell>
            {user?.role === 'ADMIN' && <TableCell>Пользователь</TableCell>}
            <TableCell>Действия</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {bookingsList.map((booking) => {
            const facility = facilities?.find(f => f.id === booking.facility);
            return (
              <TableRow key={booking.id}>
                <TableCell>{facility?.name || `Объект #${booking.facility}`}</TableCell>
                <TableCell>
                  {new Date(booking.start_time).toLocaleString('ru-RU')}
                </TableCell>
                <TableCell>
                  {new Date(booking.end_time).toLocaleString('ru-RU')}
                </TableCell>
                <TableCell>{booking.purpose}</TableCell>
                <TableCell>
                  <Chip
                    label={getStatusText(booking.status)}
                    color={getStatusColor(booking.status) as any}
                    size="small"
                  />
                </TableCell>
                {user?.role === 'ADMIN' && (
                  <TableCell>{`User #${booking.user}`}</TableCell>
                )}
                <TableCell>
                  <Box display="flex" gap={1}>
                    {user?.role === 'ADMIN' && booking.status === 'pending' && (
                      <>
                        <Button
                          size="small"
                          variant="contained"
                          color="success"
                          onClick={() => handleApprove(booking.id)}
                        >
                          Подтвердить
                        </Button>
                        <Button
                          size="small"
                          variant="contained"
                          color="error"
                          onClick={() => handleReject(booking.id)}
                        >
                          Отклонить
                        </Button>
                      </>
                    )}
                    {(user?.role === 'ADMIN' || booking.user === user?.id) && (
                      <>
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(booking)}
                          disabled={booking.status === 'approved'}
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(booking.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );

  if (bookingsLoading || facilitiesLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (bookingsError) {
    return (
      <Alert severity="error">
        Ошибка загрузки бронирований
      </Alert>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ru}>
      <Box>
        {/* Заголовок */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            Бронирования
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Создать бронирование
          </Button>
        </Box>

        {/* Вкладки */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label="Все" />
            <Tab label="Ожидают" />
            <Tab label="Подтверждены" />
            <Tab label="Отклонены" />
          </Tabs>
        </Box>

        {/* Содержимое вкладок */}
        <TabPanel value={tabValue} index={0}>
          {renderBookingsTable(getFilteredBookings())}
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          {renderBookingsTable(getFilteredBookings('pending'))}
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          {renderBookingsTable(getFilteredBookings('approved'))}
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          {renderBookingsTable(getFilteredBookings('rejected'))}
        </TabPanel>

        {/* Диалог создания/редактирования */}
        <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            {isEditing ? 'Редактировать бронирование' : 'Создать бронирование'}
          </DialogTitle>
          <Formik
            initialValues={{
              facility: selectedBooking?.facility || '',
              start_time: selectedBooking ? new Date(selectedBooking.start_time) : new Date(),
              end_time: selectedBooking ? new Date(selectedBooking.end_time) : new Date(),
              purpose: selectedBooking?.purpose || '',
            }}
            validationSchema={bookingValidationSchema}
            onSubmit={handleSubmit}
          >
            {({ values, errors, touched, setFieldValue }) => (
              <Form>
                <DialogContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <FormControl fullWidth error={touched.facility && !!errors.facility}>
                        <InputLabel>Объект</InputLabel>
                        <Select
                          value={values.facility}
                          label="Объект"
                          onChange={(e) => setFieldValue('facility', e.target.value)}
                        >
                          {facilities?.map((facility) => (
                            <MenuItem key={facility.id} value={facility.id}>
                              {facility.name} - {facility.location}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <DateTimePicker
                        label="Время начала"
                        value={values.start_time}
                        onChange={(value) => setFieldValue('start_time', value)}
                        renderInput={(params) => (
                          <TextField
                            {...params}
                            fullWidth
                            error={touched.start_time && !!errors.start_time}
                            helperText={touched.start_time && errors.start_time ? String(errors.start_time) : ''}
                          />
                        )}
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <DateTimePicker
                        label="Время окончания"
                        value={values.end_time}
                        onChange={(value) => setFieldValue('end_time', value)}
                        renderInput={(params) => (
                          <TextField
                            {...params}
                            fullWidth
                            error={touched.end_time && !!errors.end_time}
                            helperText={touched.end_time && errors.end_time ? String(errors.end_time) : ''}
                          />
                        )}
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Field
                        as={TextField}
                        name="purpose"
                        label="Цель бронирования"
                        fullWidth
                        multiline
                        rows={3}
                        error={touched.purpose && !!errors.purpose}
                        helperText={touched.purpose && errors.purpose}
                      />
                    </Grid>
                  </Grid>
                </DialogContent>
                <DialogActions>
                  <Button onClick={() => setDialogOpen(false)}>
                    Отмена
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={createMutation.isLoading || updateMutation.isLoading}
                  >
                    {isEditing ? 'Сохранить' : 'Создать'}
                  </Button>
                </DialogActions>
              </Form>
            )}
          </Formik>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

export default Bookings;