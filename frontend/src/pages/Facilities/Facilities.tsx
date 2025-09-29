import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Fab,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  LocationOn as LocationIcon,
  People as PeopleIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { facilitiesAPI } from '../../services/api';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { Facility } from '../../store/slices/facilitiesSlice';

interface FacilityCardProps {
  facility: Facility;
  onEdit: (facility: Facility) => void;
  onDelete: (id: number) => void;
  onBook: (facility: Facility) => void;
}

const FacilityCard: React.FC<FacilityCardProps> = ({ facility, onEdit, onDelete, onBook }) => {
  const { user } = useSelector((state: RootState) => state.auth);
  const isAdmin = user?.role === 'admin';

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'success';
      case 'occupied': return 'error';
      case 'maintenance': return 'warning';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'available': return 'Доступен';
      case 'occupied': return 'Занят';
      case 'maintenance': return 'Обслуживание';
      default: return status;
    }
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {facility.image && (
        <CardMedia
          component="img"
          height="200"
          image={facility.image}
          alt={facility.name}
        />
      )}
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
          <Typography variant="h6" component="h2" gutterBottom>
            {facility.name}
          </Typography>
          <Chip
            label={getStatusText(facility.status)}
            color={getStatusColor(facility.status) as any}
            size="small"
          />
        </Box>
        
        <Typography variant="body2" color="textSecondary" paragraph>
          {facility.description}
        </Typography>

        <Box display="flex" alignItems="center" mb={1}>
          <LocationIcon fontSize="small" color="action" sx={{ mr: 1 }} />
          <Typography variant="body2" color="textSecondary">
            {facility.location}
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" mb={2}>
          <PeopleIcon fontSize="small" color="action" sx={{ mr: 1 }} />
          <Typography variant="body2" color="textSecondary">
            Вместимость: {facility.capacity} человек
          </Typography>
        </Box>

        <Box display="flex" flexWrap="wrap" gap={0.5} mb={2}>
          {facility.amenities.map((amenity, index) => (
            <Chip
              key={index}
              label={amenity}
              size="small"
              variant="outlined"
            />
          ))}
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Button
            variant="contained"
            color="primary"
            onClick={() => onBook(facility)}
            disabled={facility.status !== 'available'}
            size="small"
          >
            Забронировать
          </Button>
          
          {isAdmin && (
            <Box>
              <IconButton
                size="small"
                onClick={() => onEdit(facility)}
                color="primary"
              >
                <EditIcon />
              </IconButton>
              <IconButton
                size="small"
                onClick={() => onDelete(facility.id)}
                color="error"
              >
                <DeleteIcon />
              </IconButton>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

const Facilities: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const queryClient = useQueryClient();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [capacityFilter, setCapacityFilter] = useState('');
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [bookingDialogOpen, setBookingDialogOpen] = useState(false);

  // Получение списка объектов
  const {
    data: facilities,
    isLoading,
    error,
  } = useQuery('facilities', facilitiesAPI.getAll);

  // Мутация для удаления объекта
  const deleteMutation = useMutation(facilitiesAPI.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries('facilities');
    },
  });

  // Фильтрация объектов
  const filteredFacilities = facilities?.filter((facility) => {
    const matchesSearch = facility.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         facility.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         facility.location.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = !statusFilter || facility.status === statusFilter;
    
    const matchesCapacity = !capacityFilter || 
                           (capacityFilter === 'small' && facility.capacity <= 10) ||
                           (capacityFilter === 'medium' && facility.capacity > 10 && facility.capacity <= 50) ||
                           (capacityFilter === 'large' && facility.capacity > 50);

    return matchesSearch && matchesStatus && matchesCapacity;
  }) || [];

  const handleEdit = (facility: Facility) => {
    // TODO: Открыть форму редактирования
    console.log('Edit facility:', facility);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Вы уверены, что хотите удалить этот объект?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleBook = (facility: Facility) => {
    setSelectedFacility(facility);
    setBookingDialogOpen(true);
  };

  const handleBookingSubmit = () => {
    // TODO: Реализовать логику бронирования
    setBookingDialogOpen(false);
    setSelectedFacility(null);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Ошибка загрузки объектов
      </Alert>
    );
  }

  return (
    <Box>
      {/* Заголовок */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Объекты
        </Typography>
        {user?.role === 'admin' && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {/* TODO: Открыть форму создания */}}
          >
            Добавить объект
          </Button>
        )}
      </Box>

      {/* Фильтры и поиск */}
      <Box mb={3}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Поиск объектов..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Статус</InputLabel>
              <Select
                value={statusFilter}
                label="Статус"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="">Все</MenuItem>
                <MenuItem value="available">Доступен</MenuItem>
                <MenuItem value="occupied">Занят</MenuItem>
                <MenuItem value="maintenance">Обслуживание</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Вместимость</InputLabel>
              <Select
                value={capacityFilter}
                label="Вместимость"
                onChange={(e) => setCapacityFilter(e.target.value)}
              >
                <MenuItem value="">Любая</MenuItem>
                <MenuItem value="small">До 10 человек</MenuItem>
                <MenuItem value="medium">10-50 человек</MenuItem>
                <MenuItem value="large">Более 50 человек</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<FilterIcon />}
              onClick={() => {
                setSearchTerm('');
                setStatusFilter('');
                setCapacityFilter('');
              }}
            >
              Сбросить
            </Button>
          </Grid>
        </Grid>
      </Box>

      {/* Список объектов */}
      {filteredFacilities.length === 0 ? (
        <Box textAlign="center" py={4}>
          <Typography variant="h6" color="textSecondary">
            Объекты не найдены
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Попробуйте изменить параметры поиска
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filteredFacilities.map((facility) => (
            <Grid item xs={12} sm={6} md={4} key={facility.id}>
              <FacilityCard
                facility={facility}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onBook={handleBook}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Диалог бронирования */}
      <Dialog
        open={bookingDialogOpen}
        onClose={() => setBookingDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Бронирование: {selectedFacility?.name}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" paragraph>
            Для создания бронирования перейдите на страницу "Бронирования" и выберите этот объект.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBookingDialogOpen(false)}>
            Отмена
          </Button>
          <Button onClick={handleBookingSubmit} variant="contained">
            Перейти к бронированию
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Facilities;