import React, { useState } from 'react';
import {
  Box,
  Card,
  TextField,
  Button,
  Typography,
  Link,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  Container,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import { useFormik } from 'formik';
import * as yup from 'yup';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { registerStart, registerSuccess, registerFailure } from '../../store/slices/authSlice';
import { authAPI } from '../../services/api';
import logoImage from '../../assets/images/9881812ec5a15eea28da6c949d13734d.png';
import { Plasma } from '../../components/Plasma';

const validationSchema = yup.object({
  firstName: yup
    .string()
    .required('Имя обязательно'),
  lastName: yup
    .string()
    .required('Фамилия обязательна'),
  email: yup
    .string()
    .email('Введите корректный email')
    .required('Email обязателен'),
  password: yup
    .string()
    .min(6, 'Пароль должен содержать минимум 6 символов')
    .required('Пароль обязателен'),
  confirmPassword: yup
    .string()
    .oneOf([yup.ref('password')], 'Пароли должны совпадать')
    .required('Подтверждение пароля обязательно'),
});

const Register: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { isLoading, error } = useSelector((state: RootState) => state.auth);

  const formik = useFormik({
    initialValues: {
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
    validationSchema: validationSchema,
    onSubmit: async (values) => {
      dispatch(registerStart());
      try {
        const response = await authAPI.register({
          username: values.email, // Используем email как username
          first_name: values.firstName,
          last_name: values.lastName,
          email: values.email,
          password: values.password,
          password_confirm: values.confirmPassword,
        });
        dispatch(registerSuccess({
          user: response.user,
        }));
        navigate('/dashboard');
      } catch (error: any) {
        dispatch(registerFailure(
          error.response?.data?.detail || 
          error.response?.data?.email?.[0] ||
          error.response?.data?.password?.[0] ||
          'Ошибка регистрации'
        ));
      }
    },
  });

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleClickShowConfirmPassword = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: '#ededed',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 2,
      }}
    >
      <Container maxWidth="lg">
        <Card
          sx={{
            display: 'flex',
            borderRadius: 4,
            overflow: 'hidden',
            boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
            maxWidth: 1000,
            margin: '0 auto',
          }}
        >
          {/* Left side - Branding */}
          <Box
            sx={{
              flex: 1,
              color: 'white',
              padding: 6,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              position: 'relative',
              minHeight: 500,
              overflow: 'hidden',
              backgroundColor: '#d9710f',
            }}
          >
            <Plasma
              color="#ff6b35"
              speed={0.6}
              direction="forward"
              scale={1.4}
              opacity={0.5}
              mouseInteractive={false}
            />
            <Box
              sx={{
                position: 'relative',
                zIndex: 2,
              }}
            >
              <Typography
                variant="h3"
                sx={{
                  fontWeight: 700,
                  mb: 2,
                  lineHeight: 1.2,
                  textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
                }}
              >
                Среда для управления строительными объектами
    
              </Typography>
            </Box>
          </Box>

          {/* Right side - Register Form */}
          <Box
            sx={{
              flex: 1,
              padding: 6,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              backgroundColor: '#f8f9fa',
            }}
          >
            {/* Logo/Icon */}
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: 2,
                background: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 3,
                mx: 'auto',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                overflow: 'hidden',
              }}
            >
              <img
                src={logoImage}
                alt="Block Logo"
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                }}
              />
            </Box>

            <Typography
              variant="h4"
              sx={{
                fontWeight: 600,
                mb: 1,
                textAlign: 'center',
                color: '#2c3e50',
              }}
            >
              Добро пожаловать
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: '#6c757d',
                textAlign: 'center',
                mb: 4,
              }}
            >
              Добро пожаловать в Block — Давайте начнем
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={formik.handleSubmit}>
              {/* Name Fields */}
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Box sx={{ flex: 1 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      color: '#6c757d',
                      mb: 1,
                      fontWeight: 500,
                    }}
                  >
                    Имя
                  </Typography>
                  <TextField
                    fullWidth
                    id="firstName"
                    name="firstName"
                    placeholder="Иван"
                    autoComplete="given-name"
                    value={formik.values.firstName}
                    onChange={formik.handleChange}
                    error={formik.touched.firstName && Boolean(formik.errors.firstName)}
                    helperText={formik.touched.firstName && formik.errors.firstName}
                    disabled={isLoading}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        backgroundColor: 'white',
                        '& fieldset': {
                          borderColor: '#e9ecef',
                        },
                        '&:hover fieldset': {
                          borderColor: '#FF6B35',
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: '#FF6B35',
                        },
                      },
                    }}
                  />
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      color: '#6c757d',
                      mb: 1,
                      fontWeight: 500,
                    }}
                  >
                    Фамилия
                  </Typography>
                  <TextField
                    fullWidth
                    id="lastName"
                    name="lastName"
                    placeholder="Иванов"
                    autoComplete="family-name"
                    value={formik.values.lastName}
                    onChange={formik.handleChange}
                    error={formik.touched.lastName && Boolean(formik.errors.lastName)}
                    helperText={formik.touched.lastName && formik.errors.lastName}
                    disabled={isLoading}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        backgroundColor: 'white',
                        '& fieldset': {
                          borderColor: '#e9ecef',
                        },
                        '&:hover fieldset': {
                          borderColor: '#FF6B35',
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: '#FF6B35',
                        },
                      },
                    }}
                  />
                </Box>
              </Box>

              <Typography
                variant="body2"
                sx={{
                  color: '#6c757d',
                  mb: 1,
                  fontWeight: 500,
                }}
              >
                Ваш email
              </Typography>
              <TextField
                fullWidth
                id="email"
                name="email"
                placeholder="block@example.com"
                type="email"
                autoComplete="email"
                value={formik.values.email}
                onChange={formik.handleChange}
                error={formik.touched.email && Boolean(formik.errors.email)}
                helperText={formik.touched.email && formik.errors.email}
                disabled={isLoading}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'white',
                    '& fieldset': {
                      borderColor: '#e9ecef',
                    },
                    '&:hover fieldset': {
                      borderColor: '#FF6B35',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#FF6B35',
                    },
                  },
                }}
              />

              <Typography
                variant="body2"
                sx={{
                  color: '#6c757d',
                  mb: 1,
                  fontWeight: 500,
                }}
              >
                Создать пароль
              </Typography>
              <TextField
                fullWidth
                name="password"
                placeholder="••••••••••"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="new-password"
                value={formik.values.password}
                onChange={formik.handleChange}
                error={formik.touched.password && Boolean(formik.errors.password)}
                helperText={formik.touched.password && formik.errors.password}
                disabled={isLoading}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={handleClickShowPassword}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'white',
                    '& fieldset': {
                      borderColor: '#e9ecef',
                    },
                    '&:hover fieldset': {
                      borderColor: '#FF6B35',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#FF6B35',
                    },
                  },
                }}
              />

              <Typography
                variant="body2"
                sx={{
                  color: '#6c757d',
                  mb: 1,
                  fontWeight: 500,
                }}
              >
                Подтвердите пароль
              </Typography>
              <TextField
                fullWidth
                name="confirmPassword"
                placeholder="••••••••••"
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirmPassword"
                autoComplete="new-password"
                value={formik.values.confirmPassword}
                onChange={formik.handleChange}
                error={formik.touched.confirmPassword && Boolean(formik.errors.confirmPassword)}
                helperText={formik.touched.confirmPassword && formik.errors.confirmPassword}
                disabled={isLoading}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle confirm password visibility"
                        onClick={handleClickShowConfirmPassword}
                        edge="end"
                      >
                        {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 4,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'white',
                    '& fieldset': {
                      borderColor: '#e9ecef',
                    },
                    '&:hover fieldset': {
                      borderColor: '#FF6B35',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#FF6B35',
                    },
                  },
                }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={isLoading}
                sx={{
                  py: 1.5,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #FF6B35 0%, #FFA500 100%)',
                  fontWeight: 600,
                  fontSize: '1rem',
                  textTransform: 'none',
                  mb: 3,
                  '&:hover': {
                    background: 'linear-gradient(135deg, #e55a2b 0%, #e6940a 100%)',
                  },
                  '&:disabled': {
                    background: '#cccccc',
                  },
                }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'Зарегистрироваться'
                )}
              </Button>

              <Box textAlign="center">
                <Typography variant="body2" sx={{ color: '#6c757d' }}>
                  Уже есть аккаунт?{' '}
                  <Link
                    component={RouterLink}
                    to="/login"
                    sx={{
                      color: '#FF6B35',
                      textDecoration: 'none',
                      fontWeight: 600,
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    Войти
                  </Link>
                </Typography>
              </Box>
            </Box>
          </Box>
        </Card>
      </Container>
    </Box>
  );
};

export default Register;