import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Avatar,
  IconButton,
  InputAdornment,
  Grid,
} from '@mui/material';
import {
  Search as SearchIcon,
  LocalShipping as ShippingIcon,
  Inventory as InventoryIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';

// Типы для данных доставки
interface DeliveryItem {
  id: string;
  date: string;
  shipper: string;
  carrier: string;
  parcelNumber: string;
  status: 'IN_DELIVERY' | 'DELIVERED' | 'PENDING';
}

// Мок данные для истории доставок
const mockDeliveries: DeliveryItem[] = [
  {
    id: '1',
    date: '24.04.2020',
    shipper: 'Zalando',
    carrier: 'DHL',
    parcelNumber: 'PN12398765',
    status: 'IN_DELIVERY',
  },
  {
    id: '2',
    date: '17.04.2020',
    shipper: 'Parfumdreams',
    carrier: 'DPD',
    parcelNumber: 'PN12123412',
    status: 'DELIVERED',
  },
  {
    id: '3',
    date: '13.04.2020',
    shipper: 'Abercrombie & Fitch',
    carrier: 'DHL',
    parcelNumber: 'PN31245799',
    status: 'DELIVERED',
  },
  {
    id: '4',
    date: '06.04.2020',
    shipper: 'Wayfair',
    carrier: 'UPS',
    parcelNumber: 'Z1 123 312384 8644',
    status: 'DELIVERED',
  },
  {
    id: '5',
    date: '30.03.2020',
    shipper: 'Amazon',
    carrier: 'Amazon',
    parcelNumber: 'PN123087817312S',
    status: 'DELIVERED',
  },
];

const ParcelTracking: React.FC = () => {
  const [trackingNumber, setTrackingNumber] = useState('');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'IN_DELIVERY':
        return '#FF6B35';
      case 'DELIVERED':
        return '#4CAF50';
      case 'PENDING':
        return '#2196F3';
      default:
        return '#757575';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'IN_DELIVERY':
        return 'В доставке';
      case 'DELIVERED':
        return 'Доставлено';
      case 'PENDING':
        return 'Ожидает';
      default:
        return status;
    }
  };

  const handleTrackPackage = () => {
    console.log('Отслеживание посылки:', trackingNumber);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #FFF8F0 0%, #FFFFFF 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        {/* Заголовок и приветствие */}
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              mb: 3,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar
                sx={{
                  width: 48,
                  height: 48,
                  background: 'linear-gradient(135deg, #FF6B35 0%, #FFA500 100%)',
                }}
              >
                <InventoryIcon />
              </Avatar>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 600,
                  color: '#333',
                }}
              >
                Добро пожаловать, Diana!
              </Typography>
            </Box>
          </Box>

          {/* Совет */}
          <Box
            sx={{
              p: 2,
              backgroundColor: '#FFF8F0',
              borderRadius: 2,
              border: '1px solid #FFE0B2',
            }}
          >
            <Typography
              sx={{
                color: '#FF6B35',
                fontSize: '1.1rem',
                fontWeight: 500,
              }}
            >
              💡 Совет: Настройте предпочтительные дни доставки
            </Typography>
          </Box>
        </Box>

        {/* Основной контент */}
        <Grid container spacing={4}>
          {/* Левая панель - статистика доставки */}
          <Grid item xs={12} md={4}>
            <Card
              sx={{
                borderRadius: 3,
                boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
                border: '1px solid #F5F5F5',
                mb: 3,
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      width: 60,
                      height: 60,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #FF6B35 0%, #FFA500 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mr: 2,
                    }}
                  >
                    <ShippingIcon sx={{ color: 'white', fontSize: 28 }} />
                  </Box>
                  <Box>
                    <Typography
                      variant="h3"
                      sx={{
                        fontWeight: 700,
                        color: '#333',
                        lineHeight: 1,
                      }}
                    >
                      1
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        color: '#666',
                        fontSize: '0.9rem',
                      }}
                    >
                      в доставке сегодня
                    </Typography>
                  </Box>
                </Box>

                <Typography
                  variant="body2"
                  sx={{
                    color: '#666',
                    mb: 2,
                  }}
                >
                  Доставка вашей посылки ожидается в{' '}
                  <strong>10:30 AM до 1:30 PM</strong>. Не собираетесь быть дома?
                </Typography>

                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    size="small"
                    sx={{
                      backgroundColor: '#FF6B35',
                      color: 'white',
                      textTransform: 'none',
                      borderRadius: 2,
                      fontSize: '0.8rem',
                      '&:hover': {
                        backgroundColor: '#E55A2B',
                      },
                    }}
                  >
                    Перенести
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    sx={{
                      borderColor: '#FF6B35',
                      color: '#FF6B35',
                      textTransform: 'none',
                      borderRadius: 2,
                      fontSize: '0.8rem',
                      '&:hover': {
                        borderColor: '#E55A2B',
                        backgroundColor: '#FFF5F0',
                      },
                    }}
                  >
                    Настройки
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Правая панель - отслеживание посылок */}
          <Grid item xs={12} md={8}>
            <Card
              sx={{
                borderRadius: 3,
                boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
                border: '1px solid #F5F5F5',
                background: 'linear-gradient(135deg, #FF6B35 0%, #FFA500 100%)',
                color: 'white',
                mb: 3,
              }}
            >
              <CardContent sx={{ p: 4 }}>
                <Typography
                  variant="h5"
                  sx={{
                    fontWeight: 600,
                    mb: 3,
                  }}
                >
                  Введите номер посылки для отслеживания доставки
                </Typography>

                <Box
                  sx={{
                    display: 'flex',
                    gap: 2,
                    alignItems: 'center',
                  }}
                >
                  <TextField
                    fullWidth
                    placeholder="Введите номер отслеживания..."
                    value={trackingNumber}
                    onChange={(e) => setTrackingNumber(e.target.value)}
                    sx={{
                      backgroundColor: 'white',
                      borderRadius: 2,
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        '& fieldset': {
                          border: 'none',
                        },
                      },
                    }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon sx={{ color: '#666' }} />
                        </InputAdornment>
                      ),
                    }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleTrackPackage}
                    sx={{
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      color: 'white',
                      px: 4,
                      py: 1.5,
                      borderRadius: 2,
                      textTransform: 'none',
                      fontWeight: 600,
                      border: '1px solid rgba(255,255,255,0.3)',
                      '&:hover': {
                        backgroundColor: 'rgba(255,255,255,0.3)',
                      },
                    }}
                  >
                    Отследить
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* История доставок */}
        <Card
          sx={{
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
            border: '1px solid #F5F5F5',
            mt: 4,
          }}
        >
          <Box sx={{ p: 3, borderBottom: '1px solid #F5F5F5' }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                color: '#333',
              }}
            >
              Ваши последние доставки
            </Typography>
          </Box>

          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell
                    sx={{
                      fontWeight: 600,
                      color: '#666',
                      backgroundColor: '#FAFAFA',
                    }}
                  >
                    Дата доставки
                  </TableCell>
                  <TableCell
                    sx={{
                      fontWeight: 600,
                      color: '#666',
                      backgroundColor: '#FAFAFA',
                    }}
                  >
                    Отправитель
                  </TableCell>
                  <TableCell
                    sx={{
                      fontWeight: 600,
                      color: '#666',
                      backgroundColor: '#FAFAFA',
                    }}
                  >
                    Перевозчик
                  </TableCell>
                  <TableCell
                    sx={{
                      fontWeight: 600,
                      color: '#666',
                      backgroundColor: '#FAFAFA',
                    }}
                  >
                    Номер посылки
                  </TableCell>
                  <TableCell
                    sx={{
                      fontWeight: 600,
                      color: '#666',
                      backgroundColor: '#FAFAFA',
                    }}
                  >
                    Статус
                  </TableCell>
                  <TableCell
                    sx={{
                      fontWeight: 600,
                      color: '#666',
                      backgroundColor: '#FAFAFA',
                    }}
                  >
                    Действия
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {mockDeliveries.map((delivery) => (
                  <TableRow
                    key={delivery.id}
                    sx={{
                      '&:hover': {
                        backgroundColor: '#FAFAFA',
                      },
                    }}
                  >
                    <TableCell sx={{ color: '#333' }}>{delivery.date}</TableCell>
                    <TableCell sx={{ color: '#333' }}>{delivery.shipper}</TableCell>
                    <TableCell sx={{ color: '#333' }}>{delivery.carrier}</TableCell>
                    <TableCell sx={{ color: '#333' }}>{delivery.parcelNumber}</TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusText(delivery.status)}
                        sx={{
                          backgroundColor: `${getStatusColor(delivery.status)}20`,
                          color: getStatusColor(delivery.status),
                          fontWeight: 500,
                          fontSize: '0.8rem',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        sx={{
                          color: '#FF6B35',
                          textTransform: 'none',
                          fontWeight: 500,
                          '&:hover': {
                            backgroundColor: '#FFF5F0',
                          },
                        }}
                      >
                        Подробнее →
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ p: 3, textAlign: 'center', borderTop: '1px solid #F5F5F5' }}>
            <Button
              sx={{
                color: '#FF6B35',
                fontWeight: 600,
                textTransform: 'none',
                '&:hover': {
                  backgroundColor: '#FFF5F0',
                },
              }}
            >
              Показать все →
            </Button>
          </Box>
        </Card>
      </Container>
    </Box>
  );
};

export default ParcelTracking;