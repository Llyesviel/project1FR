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

interface CreateDefectFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (defectData: any) => void;
}

// Mock users data
const mockUsers = [
  { id: 1, name: 'Иван Петров', email: 'ivan@example.com', role: 'Разработчик' },
  { id: 2, name: 'Мария Сидорова', email: 'maria@example.com', role: 'Тестировщик' },
  { id: 3, name: 'Алексей Козлов', email: 'alexey@example.com', role: 'Тестировщик' },
  { id: 4, name: 'Елена Васильева', email: 'elena@example.com', role: 'Аналитик' },
  { id: 5, name: 'Дмитрий Смирнов', email: 'dmitry@example.com', role: 'DevOps' },
];

const CreateDefectForm: React.FC<CreateDefectFormProps> = ({ open, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    severity: 'medium',
    priority: 'medium',
    status: 'open',
    assignedTo: null as any,
    reportedBy: '',
    project: '',
    component: '',
    version: '',
    environment: 'production',
    stepsToReproduce: '',
    expectedResult: '',
    actualResult: '',
    dueDate: null,
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
      severity: 'medium',
      priority: 'medium',
      status: 'open',
      assignedTo: null,
      reportedBy: '',
      project: '',
      component: '',
      version: '',
      environment: 'production',
      stepsToReproduce: '',
      expectedResult: '',
      actualResult: '',
      dueDate: null,
      tags: [],
    });
    onClose();
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ru}>
      <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ bgcolor: '#ea580c', color: 'white', fontWeight: 'bold' }}>
          Создание нового дефекта
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Краткое описание дефекта"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Подробное описание"
                multiline
                rows={3}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
              />
            </Grid>

            <Grid item xs={4}>
              <FormControl fullWidth>
                <InputLabel>Серьезность</InputLabel>
                <Select
                  value={formData.severity}
                  label="Серьезность"
                  onChange={(e) => handleInputChange('severity', e.target.value)}
                >
                  <MenuItem value="trivial">Тривиальная</MenuItem>
                  <MenuItem value="minor">Незначительная</MenuItem>
                  <MenuItem value="medium">Средняя</MenuItem>
                  <MenuItem value="major">Значительная</MenuItem>
                  <MenuItem value="critical">Критическая</MenuItem>
                  <MenuItem value="blocker">Блокирующая</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={4}>
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
                  <MenuItem value="urgent">Срочный</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={4}>
              <FormControl fullWidth>
                <InputLabel>Статус</InputLabel>
                <Select
                  value={formData.status}
                  label="Статус"
                  onChange={(e) => handleInputChange('status', e.target.value)}
                >
                  <MenuItem value="open">Открыт</MenuItem>
                  <MenuItem value="in_progress">В работе</MenuItem>
                  <MenuItem value="resolved">Решен</MenuItem>
                  <MenuItem value="closed">Закрыт</MenuItem>
                  <MenuItem value="rejected">Отклонен</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6}>
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
                label="Кем обнаружен"
                value={formData.reportedBy}
                onChange={(e) => handleInputChange('reportedBy', e.target.value)}
              />
            </Grid>

            <Grid item xs={4}>
              <TextField
                fullWidth
                label="Проект"
                value={formData.project}
                onChange={(e) => handleInputChange('project', e.target.value)}
              />
            </Grid>

            <Grid item xs={4}>
              <TextField
                fullWidth
                label="Компонент"
                value={formData.component}
                onChange={(e) => handleInputChange('component', e.target.value)}
              />
            </Grid>

            <Grid item xs={4}>
              <TextField
                fullWidth
                label="Версия"
                value={formData.version}
                onChange={(e) => handleInputChange('version', e.target.value)}
              />
            </Grid>

            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Окружение</InputLabel>
                <Select
                  value={formData.environment}
                  label="Окружение"
                  onChange={(e) => handleInputChange('environment', e.target.value)}
                >
                  <MenuItem value="development">Разработка</MenuItem>
                  <MenuItem value="testing">Тестирование</MenuItem>
                  <MenuItem value="staging">Предпродакшн</MenuItem>
                  <MenuItem value="production">Продакшн</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6}>
              <DatePicker
                label="Срок устранения"
                value={formData.dueDate}
                onChange={(date) => handleInputChange('dueDate', date)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Шаги для воспроизведения"
                multiline
                rows={3}
                value={formData.stepsToReproduce}
                onChange={(e) => handleInputChange('stepsToReproduce', e.target.value)}
                placeholder="1. Шаг первый&#10;2. Шаг второй&#10;3. Шаг третий"
              />
            </Grid>

            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Ожидаемый результат"
                multiline
                rows={2}
                value={formData.expectedResult}
                onChange={(e) => handleInputChange('expectedResult', e.target.value)}
              />
            </Grid>

            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Фактический результат"
                multiline
                rows={2}
                value={formData.actualResult}
                onChange={(e) => handleInputChange('actualResult', e.target.value)}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Теги дефекта</Typography>
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
                    color="error"
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
            Создать дефект
          </Button>
        </DialogActions>
      </Dialog>
    </LocalizationProvider>
  );
};

export default CreateDefectForm;