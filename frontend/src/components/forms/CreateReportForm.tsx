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
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ru } from 'date-fns/locale';

interface CreateReportFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (reportData: any) => void;
}

const CreateReportForm: React.FC<CreateReportFormProps> = ({ open, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'project_status',
    status: 'draft',
    priority: 'medium',
    reportPeriod: 'weekly',
    startDate: null,
    endDate: null,
    includeCharts: true,
    includeMetrics: true,
    includeComments: false,
    recipients: [] as string[],
    tags: [] as string[],
  });

  const [newRecipient, setNewRecipient] = useState('');
  const [newTag, setNewTag] = useState('');

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAddRecipient = () => {
    if (newRecipient.trim() && !formData.recipients.includes(newRecipient.trim())) {
      setFormData(prev => ({
        ...prev,
        recipients: [...prev.recipients, newRecipient.trim()]
      }));
      setNewRecipient('');
    }
  };

  const handleRemoveRecipient = (recipientToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      recipients: prev.recipients.filter(recipient => recipient !== recipientToRemove)
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
      type: 'project_status',
      status: 'draft',
      priority: 'medium',
      reportPeriod: 'weekly',
      startDate: null,
      endDate: null,
      includeCharts: true,
      includeMetrics: true,
      includeComments: false,
      recipients: [],
      tags: [],
    });
    onClose();
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ru}>
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle sx={{ bgcolor: '#ea580c', color: 'white', fontWeight: 'bold' }}>
          Создание нового отчета
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Название отчета"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Описание отчета"
                multiline
                rows={3}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
              />
            </Grid>

            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Тип отчета</InputLabel>
                <Select
                  value={formData.type}
                  label="Тип отчета"
                  onChange={(e) => handleInputChange('type', e.target.value)}
                >
                  <MenuItem value="project_status">Статус проекта</MenuItem>
                  <MenuItem value="task_progress">Прогресс задач</MenuItem>
                  <MenuItem value="defect_analysis">Анализ дефектов</MenuItem>
                  <MenuItem value="performance">Производительность</MenuItem>
                  <MenuItem value="financial">Финансовый</MenuItem>
                  <MenuItem value="custom">Пользовательский</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Статус</InputLabel>
                <Select
                  value={formData.status}
                  label="Статус"
                  onChange={(e) => handleInputChange('status', e.target.value)}
                >
                  <MenuItem value="draft">Черновик</MenuItem>
                  <MenuItem value="in_review">На проверке</MenuItem>
                  <MenuItem value="approved">Утвержден</MenuItem>
                  <MenuItem value="published">Опубликован</MenuItem>
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

            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Период отчета</InputLabel>
                <Select
                  value={formData.reportPeriod}
                  label="Период отчета"
                  onChange={(e) => handleInputChange('reportPeriod', e.target.value)}
                >
                  <MenuItem value="daily">Ежедневно</MenuItem>
                  <MenuItem value="weekly">Еженедельно</MenuItem>
                  <MenuItem value="monthly">Ежемесячно</MenuItem>
                  <MenuItem value="quarterly">Ежеквартально</MenuItem>
                  <MenuItem value="custom">Пользовательский</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6}>
              <DatePicker
                label="Дата начала периода"
                value={formData.startDate}
                onChange={(date) => handleInputChange('startDate', date)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>

            <Grid item xs={6}>
              <DatePicker
                label="Дата окончания периода"
                value={formData.endDate}
                onChange={(date) => handleInputChange('endDate', date)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>Настройки содержимого отчета</Typography>
              <Stack spacing={1}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.includeCharts}
                      onChange={(e) => handleInputChange('includeCharts', e.target.checked)}
                    />
                  }
                  label="Включить графики и диаграммы"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.includeMetrics}
                      onChange={(e) => handleInputChange('includeMetrics', e.target.checked)}
                    />
                  }
                  label="Включить ключевые метрики"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.includeComments}
                      onChange={(e) => handleInputChange('includeComments', e.target.checked)}
                    />
                  }
                  label="Включить комментарии и рекомендации"
                />
              </Stack>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Получатели отчета</Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  size="small"
                  label="Email получателя"
                  value={newRecipient}
                  onChange={(e) => setNewRecipient(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddRecipient()}
                />
                <Button variant="outlined" onClick={handleAddRecipient}>
                  Добавить
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {formData.recipients.map((recipient, index) => (
                  <Chip
                    key={index}
                    label={recipient}
                    onDelete={() => handleRemoveRecipient(recipient)}
                    color="secondary"
                    variant="outlined"
                  />
                ))}
              </Stack>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Теги отчета</Typography>
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
            Создать отчет
          </Button>
        </DialogActions>
      </Dialog>
    </LocalizationProvider>
  );
};

export default CreateReportForm;