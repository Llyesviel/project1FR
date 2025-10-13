import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { defectsAPI, Defect } from '../../services/api';

// Типы для состояния дефектов
export interface DefectsState {
  defects: Defect[];
  currentDefect: Defect | null;
  myDefects: Defect[];
  overdueDefects: Defect[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  filters: {
    status?: string;
    severity?: string;
    priority?: string;
    facility?: number;
    assigned_to?: number;
    search?: string;
    ordering?: string;
  };
}

// Начальное состояние
const initialState: DefectsState = {
  defects: [],
  currentDefect: null,
  myDefects: [],
  overdueDefects: [],
  loading: false,
  error: null,
  totalCount: 0,
  filters: {},
};

// Async thunks для API вызовов
export const fetchDefects = createAsyncThunk(
  'defects/fetchDefects',
  async (params?: DefectsState['filters']) => {
    const response = await defectsAPI.getAll(params);
    return response;
  }
);

export const fetchDefectById = createAsyncThunk(
  'defects/fetchDefectById',
  async (id: number) => {
    const response = await defectsAPI.getById(id);
    return response;
  }
);

export const createDefect = createAsyncThunk(
  'defects/createDefect',
  async (data: Omit<Defect, 'id' | 'created_at' | 'updated_at' | 'is_overdue' | 'reported_by' | 'facility_name' | 'reported_by_name' | 'assigned_to_name'>) => {
    const response = await defectsAPI.create(data);
    return response;
  }
);

export const updateDefect = createAsyncThunk(
  'defects/updateDefect',
  async ({ id, data }: { id: number; data: Partial<Defect> }) => {
    const response = await defectsAPI.update(id, data);
    return response;
  }
);

export const deleteDefect = createAsyncThunk(
  'defects/deleteDefect',
  async (id: number) => {
    await defectsAPI.delete(id);
    return id;
  }
);

export const updateDefectStatus = createAsyncThunk(
  'defects/updateDefectStatus',
  async ({ id, status }: { id: number; status: Defect['status'] }) => {
    const response = await defectsAPI.updateStatus(id, status);
    return response;
  }
);

export const assignDefect = createAsyncThunk(
  'defects/assignDefect',
  async ({ id, assigned_to }: { id: number; assigned_to: number }) => {
    const response = await defectsAPI.assign(id, assigned_to);
    return response;
  }
);

export const fetchMyDefects = createAsyncThunk(
  'defects/fetchMyDefects',
  async () => {
    const response = await defectsAPI.getMyDefects();
    return response;
  }
);

export const fetchOverdueDefects = createAsyncThunk(
  'defects/fetchOverdueDefects',
  async () => {
    const response = await defectsAPI.getOverdue();
    return response;
  }
);

// Slice
const defectsSlice = createSlice({
  name: 'defects',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<DefectsState['filters']>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    clearCurrentDefect: (state) => {
      state.currentDefect = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch defects
    builder
      .addCase(fetchDefects.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDefects.fulfilled, (state, action) => {
        state.loading = false;
        state.defects = action.payload.results;
        state.totalCount = action.payload.count;
      })
      .addCase(fetchDefects.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при загрузке дефектов';
      });

    // Fetch defect by ID
    builder
      .addCase(fetchDefectById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDefectById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentDefect = action.payload;
      })
      .addCase(fetchDefectById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при загрузке дефекта';
      });

    // Create defect
    builder
      .addCase(createDefect.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createDefect.fulfilled, (state, action) => {
        state.loading = false;
        state.defects.unshift(action.payload);
        state.totalCount += 1;
      })
      .addCase(createDefect.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при создании дефекта';
      });

    // Update defect
    builder
      .addCase(updateDefect.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateDefect.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.defects.findIndex(defect => defect.id === action.payload.id);
        if (index !== -1) {
          state.defects[index] = action.payload;
        }
        if (state.currentDefect?.id === action.payload.id) {
          state.currentDefect = action.payload;
        }
      })
      .addCase(updateDefect.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при обновлении дефекта';
      });

    // Delete defect
    builder
      .addCase(deleteDefect.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteDefect.fulfilled, (state, action) => {
        state.loading = false;
        state.defects = state.defects.filter(defect => defect.id !== action.payload);
        state.totalCount -= 1;
        if (state.currentDefect?.id === action.payload) {
          state.currentDefect = null;
        }
      })
      .addCase(deleteDefect.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при удалении дефекта';
      });

    // Update defect status
    builder
      .addCase(updateDefectStatus.fulfilled, (state, action) => {
        const index = state.defects.findIndex(defect => defect.id === action.payload.id);
        if (index !== -1) {
          state.defects[index] = action.payload;
        }
        if (state.currentDefect?.id === action.payload.id) {
          state.currentDefect = action.payload;
        }
      });

    // Assign defect
    builder
      .addCase(assignDefect.fulfilled, (state, action) => {
        const index = state.defects.findIndex(defect => defect.id === action.payload.id);
        if (index !== -1) {
          state.defects[index] = action.payload;
        }
        if (state.currentDefect?.id === action.payload.id) {
          state.currentDefect = action.payload;
        }
      });

    // Fetch my defects
    builder
      .addCase(fetchMyDefects.fulfilled, (state, action) => {
        state.myDefects = action.payload;
      });

    // Fetch overdue defects
    builder
      .addCase(fetchOverdueDefects.fulfilled, (state, action) => {
        state.overdueDefects = action.payload;
      });
  },
});

export const { setFilters, clearFilters, clearCurrentDefect, clearError } = defectsSlice.actions;
export default defectsSlice.reducer;