import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { tasksAPI, Task } from '../../services/api';

// Типы для состояния задач
export interface TasksState {
  tasks: Task[];
  currentTask: Task | null;
  myTasks: Task[];
  overdueTasks: Task[];
  projectTasks: Task[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  filters: {
    status?: string;
    priority?: string;
    project?: number;
    facility?: number;
    assigned_to?: number;
    search?: string;
    ordering?: string;
  };
}

// Начальное состояние
const initialState: TasksState = {
  tasks: [],
  currentTask: null,
  myTasks: [],
  overdueTasks: [],
  projectTasks: [],
  loading: false,
  error: null,
  totalCount: 0,
  filters: {},
};

// Async thunks для API вызовов
export const fetchTasks = createAsyncThunk(
  'tasks/fetchTasks',
  async (params?: TasksState['filters']) => {
    const response = await tasksAPI.getAll(params);
    return response;
  }
);

export const fetchTaskById = createAsyncThunk(
  'tasks/fetchTaskById',
  async (id: number) => {
    const response = await tasksAPI.getById(id);
    return response;
  }
);

export const createTask = createAsyncThunk(
  'tasks/createTask',
  async (data: Omit<Task, 'id' | 'created_at' | 'updated_at' | 'is_overdue' | 'progress_percentage' | 'created_by' | 'project_name' | 'facility_name' | 'assigned_to_name' | 'created_by_name'>) => {
    const response = await tasksAPI.create(data);
    return response;
  }
);

export const updateTask = createAsyncThunk(
  'tasks/updateTask',
  async ({ id, data }: { id: number; data: Partial<Task> }) => {
    const response = await tasksAPI.update(id, data);
    return response;
  }
);

export const deleteTask = createAsyncThunk(
  'tasks/deleteTask',
  async (id: number) => {
    await tasksAPI.delete(id);
    return id;
  }
);

export const updateTaskStatus = createAsyncThunk(
  'tasks/updateTaskStatus',
  async ({ id, status }: { id: number; status: Task['status'] }) => {
    const response = await tasksAPI.updateStatus(id, status);
    return response;
  }
);

export const assignTask = createAsyncThunk(
  'tasks/assignTask',
  async ({ id, assigned_to }: { id: number; assigned_to: number }) => {
    const response = await tasksAPI.assign(id, assigned_to);
    return response;
  }
);

export const fetchMyTasks = createAsyncThunk(
  'tasks/fetchMyTasks',
  async () => {
    const response = await tasksAPI.getMyTasks();
    return response;
  }
);

export const fetchOverdueTasks = createAsyncThunk(
  'tasks/fetchOverdueTasks',
  async () => {
    const response = await tasksAPI.getOverdue();
    return response;
  }
);

export const fetchTasksByProject = createAsyncThunk(
  'tasks/fetchTasksByProject',
  async (projectId: number) => {
    const response = await tasksAPI.getByProject(projectId);
    return response;
  }
);

// Slice
const tasksSlice = createSlice({
  name: 'tasks',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<TasksState['filters']>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    clearCurrentTask: (state) => {
      state.currentTask = null;
    },
    clearError: (state) => {
      state.error = null;
    },
    clearProjectTasks: (state) => {
      state.projectTasks = [];
    },
  },
  extraReducers: (builder) => {
    // Fetch tasks
    builder
      .addCase(fetchTasks.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTasks.fulfilled, (state, action) => {
        state.loading = false;
        state.tasks = action.payload.results;
        state.totalCount = action.payload.count;
      })
      .addCase(fetchTasks.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при загрузке задач';
      });

    // Fetch task by ID
    builder
      .addCase(fetchTaskById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTaskById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentTask = action.payload;
      })
      .addCase(fetchTaskById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при загрузке задачи';
      });

    // Create task
    builder
      .addCase(createTask.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createTask.fulfilled, (state, action) => {
        state.loading = false;
        state.tasks.unshift(action.payload);
        state.totalCount += 1;
      })
      .addCase(createTask.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при создании задачи';
      });

    // Update task
    builder
      .addCase(updateTask.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateTask.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.tasks.findIndex(task => task.id === action.payload.id);
        if (index !== -1) {
          state.tasks[index] = action.payload;
        }
        if (state.currentTask?.id === action.payload.id) {
          state.currentTask = action.payload;
        }
        // Обновляем также в projectTasks если задача там есть
        const projectIndex = state.projectTasks.findIndex(task => task.id === action.payload.id);
        if (projectIndex !== -1) {
          state.projectTasks[projectIndex] = action.payload;
        }
      })
      .addCase(updateTask.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при обновлении задачи';
      });

    // Delete task
    builder
      .addCase(deleteTask.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteTask.fulfilled, (state, action) => {
        state.loading = false;
        state.tasks = state.tasks.filter(task => task.id !== action.payload);
        state.projectTasks = state.projectTasks.filter(task => task.id !== action.payload);
        state.totalCount -= 1;
        if (state.currentTask?.id === action.payload) {
          state.currentTask = null;
        }
      })
      .addCase(deleteTask.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при удалении задачи';
      });

    // Update task status
    builder
      .addCase(updateTaskStatus.fulfilled, (state, action) => {
        const index = state.tasks.findIndex(task => task.id === action.payload.id);
        if (index !== -1) {
          state.tasks[index] = action.payload;
        }
        if (state.currentTask?.id === action.payload.id) {
          state.currentTask = action.payload;
        }
        const projectIndex = state.projectTasks.findIndex(task => task.id === action.payload.id);
        if (projectIndex !== -1) {
          state.projectTasks[projectIndex] = action.payload;
        }
      });

    // Assign task
    builder
      .addCase(assignTask.fulfilled, (state, action) => {
        const index = state.tasks.findIndex(task => task.id === action.payload.id);
        if (index !== -1) {
          state.tasks[index] = action.payload;
        }
        if (state.currentTask?.id === action.payload.id) {
          state.currentTask = action.payload;
        }
        const projectIndex = state.projectTasks.findIndex(task => task.id === action.payload.id);
        if (projectIndex !== -1) {
          state.projectTasks[projectIndex] = action.payload;
        }
      });

    // Fetch my tasks
    builder
      .addCase(fetchMyTasks.fulfilled, (state, action) => {
        state.myTasks = action.payload;
      });

    // Fetch overdue tasks
    builder
      .addCase(fetchOverdueTasks.fulfilled, (state, action) => {
        state.overdueTasks = action.payload;
      });

    // Fetch tasks by project
    builder
      .addCase(fetchTasksByProject.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTasksByProject.fulfilled, (state, action) => {
        state.loading = false;
        state.projectTasks = action.payload;
      })
      .addCase(fetchTasksByProject.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка при загрузке задач проекта';
      });
  },
});

export const { 
  setFilters, 
  clearFilters, 
  clearCurrentTask, 
  clearError, 
  clearProjectTasks 
} = tasksSlice.actions;

export default tasksSlice.reducer;