import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Grid,
  Chip,
  Stack,
  Autocomplete,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ru } from 'date-fns/locale';

interface CreateTaskFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (taskData: any) => void;
}

// Mock users data - в реальном приложении это будет загружаться с сервера
const mockUsers = [
  { id: 1, name: 'Иван Петров', email: 'ivan@example.com', role: 'Разработчик' },
  { id: 2, name: 'Мария Сидорова', email: 'maria@example.com', role: 'Дизайнер' },
  { id: 3, name: 'Алексей Козлов', email: 'alexey@example.com', role: 'Тестировщик' },
  { id: 4, name: 'Елена Васильева', email: 'elena@example.com', role: 'Аналитик' },
  { id: 5, name: 'Дмитрий Смирнов', email: 'dmitry@example.com', role: 'DevOps' },
];

const CreateTaskForm: React.FC<CreateTaskFormProps> = ({ open, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'todo',
    priority: 'medium',
    assignedTo: null as any,
    project: '',
    dueDate: null,
    estimatedHours: '',
    tags: [] as string[],
  });

  const [newTag, setNewTag] = useState('');

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSubmit = () => {
    onSubmit(formData);
    setFormData({
      title: '',
      description: '',
      status: 'todo',
      priority: 'medium',
      assignedTo: null,
      project: '',
      dueDate: null,
      estimatedHours: '',
      tags: [],
    });
    onClose();
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ru}>
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle sx={{ bgcolor: '#ea580c', color: 'white', fontWeight: 'bold' }}>
          Создание новой задачи
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Название задачи"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Описание задачи"
                multiline
                rows={3}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
              />
            </Grid>

            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Статус</InputLabel>
                <Select
                  value={formData.status}
                  label="Статус"
                  onChange={(e) => handleInputChange('status', e.target.value)}
                >
                  <MenuItem value="todo">К выполнению</MenuItem>
                  <MenuItem value="in_progress">В работе</MenuItem>
                  <MenuItem value="review">На проверке</MenuItem>
                  <MenuItem value="done">Выполнено</MenuItem>
                  <MenuItem value="blocked">Заблокировано</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Приоритет</InputLabel>
                <Select
                  value={formData.priority}
                  label="Приоритет"
                  onChange={(e) => handleInputChange('priority', e.target.value)}
                >
                  <MenuItem value="low">Низкий</MenuItem>
                  <MenuItem value="medium">Средний</MenuItem>
                  <MenuItem value="high">Высокий</MenuItem>
                  <MenuItem value="critical">Критический</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Autocomplete
                options={mockUsers}
                getOptionLabel={(option) => `${option.name} (${option.role})`}
                value={formData.assignedTo}
                onChange={(event, newValue) => handleInputChange('assignedTo', newValue)}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Назначить исполнителя"
                    placeholder="Выберите пользователя"
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props}>
                    <Box>
                      <Typography variant="body1">{option.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {option.role} • {option.email}
                      </Typography>
                    </Box>
                  </Box>
                )}
              />
            </Grid>

            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Проект"
                value={formData.project}
                onChange={(e) => handleInputChange('project', e.target.value)}
                placeholder="Название проекта"
              />
            </Grid>

            <Grid item xs={6}>
              <DatePicker
                label="Срок выполнения"
                value={formData.dueDate}
                onChange={(date) => handleInputChange('dueDate', date)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Оценка времени (часы)"
                type="number"
                value={formData.estimatedHours}
                onChange={(e) => handleInputChange('estimatedHours', e.target.value)}
                inputProps={{ min: 0, step: 0.5 }}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Теги задачи</Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  size="small"
                  label="Добавить тег"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                />
                <Button variant="outlined" onClick={handleAddTag}>
                  Добавить
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {formData.tags.map((tag, index) => (
                  <Chip
                    key={index}
                    label={tag}
                    onDelete={() => handleRemoveTag(tag)}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Stack>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={onClose} color="inherit">
            Отмена
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            sx={{ bgcolor: '#ea580c', '&:hover': { bgcolor: '#c2410c' } }}
            disabled={!formData.title.trim()}
          >
            Создать задачу
          </Button>
        </DialogActions>
      </Dialog>
    </LocalizationProvider>
  );
};

export default CreateTaskForm;