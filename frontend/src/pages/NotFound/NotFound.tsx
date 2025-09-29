import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/dashboard');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          textAlign: 'center',
          gap: 3,
        }}
      >
        <ErrorOutlineIcon 
          sx={{ 
            fontSize: 120, 
            color: 'error.main',
            mb: 2 
          }} 
        />
        
        <Typography variant="h1" component="h1" sx={{ fontSize: '6rem', fontWeight: 'bold', color: 'error.main' }}>
          404
        </Typography>
        
        <Typography variant="h4" component="h2" gutterBottom>
          Страница не найдена
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500 }}>
          К сожалению, запрашиваемая вами страница не существует. 
          Возможно, она была перемещена или удалена.
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleGoHome}
            size="large"
          >
            На главную
          </Button>
          
          <Button 
            variant="outlined" 
            color="primary" 
            onClick={handleGoBack}
            size="large"
          >
            Назад
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default NotFound;