import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Alert,
  Snackbar,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CreateTaskForm from '../../components/forms/CreateTaskForm';

const CreateTask: React.FC = () => {
  const navigate = useNavigate();
  const [showSuccess, setShowSuccess] = useState(false);

  const handleTaskSubmit = (taskData: any) => {
    console.log('Создание задачи:', taskData);
    // Here you would typically send the data to your backend API
    setShowSuccess(true);
    
    // Redirect to dashboard after a short delay
    setTimeout(() => {
      navigate('/dashboard');
    }, 2000);
  };

  const handleBack = () => {
    navigate('/dashboard');
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={handleBack}
          sx={{ mb: 2 }}
        >
          Вернуться к панели управления
        </Button>
        
        <Typography variant="h4" component="h1" gutterBottom>
          Создание новой задачи
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Заполните форму ниже для создания и назначения новой задачи
        </Typography>
      </Box>

      <Paper elevation={3} sx={{ p: 4 }}>
        <CreateTaskForm
          open={true}
          onClose={handleBack}
          onSubmit={handleTaskSubmit}
        />
      </Paper>

      <Snackbar
        open={showSuccess}
        autoHideDuration={6000}
        onClose={() => setShowSuccess(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setShowSuccess(false)}
          severity="success"
          sx={{ width: '100%' }}
        >
          Задача успешно создана и назначена! Перенаправление на панель управления...
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default CreateTask;