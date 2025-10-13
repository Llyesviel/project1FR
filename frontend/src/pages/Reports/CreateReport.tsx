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
import CreateReportForm from '../../components/forms/CreateReportForm';

const CreateReport: React.FC = () => {
  const navigate = useNavigate();
  const [showSuccess, setShowSuccess] = useState(false);

  const handleReportSubmit = (reportData: any) => {
    console.log('Создание отчета:', reportData);
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
          Создание нового отчета
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Заполните форму ниже для создания нового отчета в системе
        </Typography>
      </Box>

      <Paper elevation={3} sx={{ p: 4 }}>
        <CreateReportForm
          open={true}
          onClose={handleBack}
          onSubmit={handleReportSubmit}
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
          Отчет успешно создан! Перенаправление на панель управления...
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default CreateReport;