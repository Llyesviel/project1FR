import { createAsyncThunk } from '@reduxjs/toolkit';
import { authAPI } from '../../services/api';
import { verifyTokenStart, verifyTokenSuccess, verifyTokenFailure } from '../slices/authSlice';

// Async thunk for token verification on app startup
export const verifyToken = createAsyncThunk(
  'auth/verifyToken',
  async (_, { dispatch, rejectWithValue }) => {
    const token = localStorage.getItem('token');
    
    if (!token) {
      dispatch(verifyTokenFailure());
      return rejectWithValue('No token found');
    }

    try {
      dispatch(verifyTokenStart());
      const user = await authAPI.getCurrentUser();
      dispatch(verifyTokenSuccess(user));
      return user;
    } catch (error: any) {
      dispatch(verifyTokenFailure());
      return rejectWithValue(error.response?.data?.detail || 'Token verification failed');
    }
  }
);