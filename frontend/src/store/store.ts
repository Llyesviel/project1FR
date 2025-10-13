import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import facilitiesReducer from './slices/facilitiesSlice';
import notificationsReducer from './slices/notificationsSlice';
import defectsReducer from './slices/defectsSlice';
import tasksReducer from './slices/tasksSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    facilities: facilitiesReducer,
    notifications: notificationsReducer,
    defects: defectsReducer,
    tasks: tasksReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;