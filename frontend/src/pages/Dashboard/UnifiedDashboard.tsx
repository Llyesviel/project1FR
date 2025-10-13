import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import {
  Dashboard as DashboardIcon,
  Construction as ConstructionIcon,
  Assignment as AssignmentIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Business as BusinessIcon,
  Group as GroupIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  Build as BuildIcon,
  Home as HomeIcon,
  AttachMoney as MoneyIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  Description as DescriptionIcon,
  ViewList as ViewListIcon
} from '@mui/icons-material';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Avatar,
  Tabs,
  Tab,
  AppBar,
  Toolbar,
  IconButton,
  Badge,
  Divider,
  Stack
} from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';

// Create orange theme
const orangeTheme = createTheme({
  palette: {
    primary: {
      main: '#ea580c',
      light: '#fb923c',
      dark: '#c2410c',
    },
    secondary: {
      main: '#f97316',
    },
    background: {
      default: '#fef7f0',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif',
  },
});

// Unified interfaces for all dashboard data
interface StatCard {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
}

interface Task {
  id: number;
  title: string;
  description: string;
  assignee?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  priority: 'high' | 'medium' | 'low';
  deadline: string;
}

interface Project {
  id: number;
  name: string;
  description?: string;
  progress: number;
  status: 'planning' | 'active' | 'on_track' | 'at_risk' | 'delayed' | 'completed' | 'in_progress' | 'on_hold';
  start_date: string;
  end_date: string;
}

interface Report {
  id: number;
  title: string;
  type: string;
  period: string;
  status: string;
  created_at: string;
  summary: string;
}

interface DashboardConfig {
  title: string;
  tabs: Array<{
    id: string;
    name: string;
    icon: React.ReactNode;
  }>;
  stats: StatCard[];
}

const UnifiedDashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');

  // Mock data for demonstration
  const mockTasks: Task[] = [
    {
      id: 1,
      title: 'Проверка системы вентиляции',
      description: 'Плановая проверка работы системы вентиляции в здании А',
      assignee: 'Иван Петров',
      status: 'in_progress',
      priority: 'high',
      deadline: '2024-01-25'
    },
    {
      id: 2,
      title: 'Замена фильтров кондиционирования',
      description: 'Замена воздушных фильтров в системе кондиционирования',
      assignee: 'Мария Сидорова',
      status: 'pending',
      priority: 'medium',
      deadline: '2024-01-30'
    },
    {
      id: 3,
      title: 'Обслуживание лифтового оборудования',
      description: 'Ежемесячное техническое обслуживание лифтов',
      assignee: 'Алексей Козлов',
      status: 'completed',
      priority: 'high',
      deadline: '2024-01-20'
    }
  ];

  const mockProjects: Project[] = [
    {
      id: 1,
      name: 'Модернизация системы отопления',
      description: 'Замена старых радиаторов на энергоэффективные',
      progress: 75,
      status: 'on_track',
      start_date: '2024-01-01',
      end_date: '2024-03-31'
    },
    {
      id: 2,
      name: 'Установка системы видеонаблюдения',
      description: 'Монтаж камер видеонаблюдения по периметру здания',
      progress: 45,
      status: 'active',
      start_date: '2024-01-15',
      end_date: '2024-02-28'
    },
    {
      id: 3,
      name: 'Ремонт кровли',
      description: 'Капитальный ремонт кровли главного здания',
      progress: 100,
      status: 'completed',
      start_date: '2023-11-01',
      end_date: '2023-12-31'
    }
  ];

  const mockReports: Report[] = [
    {
      id: 1,
      title: 'Финансовый отчет за Q4 2023',
      type: 'financial',
      period: 'Q4 2023',
      status: 'published',
      created_at: '2024-01-05',
      summary: 'Общие расходы на содержание объектов составили 15.2 млн руб.'
    },
    {
      id: 2,
      title: 'Отчет о качестве обслуживания',
      type: 'quality',
      period: 'Декабрь 2023',
      status: 'published',
      created_at: '2024-01-03',
      summary: 'Уровень удовлетворенности клиентов составил 94.5%'
    }
  ];

  // Role-based configuration
  const getRoleConfig = (): DashboardConfig => {
    if (user?.is_customer) {
      return {
        title: 'Панель заказчика',
        tabs: [
          { id: 'overview', name: 'Обзор', icon: <DashboardIcon /> },
          { id: 'projects', name: 'Проекты', icon: <ConstructionIcon /> },
          { id: 'reports', name: 'Отчеты', icon: <AssignmentIcon /> }
        ],
        stats: [
          { title: 'Активные проекты', value: 3, icon: <ConstructionIcon />, color: '#ea580c' },
          { title: 'Завершенные проекты', value: 12, icon: <CheckCircleIcon />, color: '#10b981' },
          { title: 'Общий бюджет', value: '2.5М ₽', icon: <MoneyIcon />, color: '#3b82f6' },
          { title: 'Экономия', value: '15%', icon: <TrendingUpIcon />, color: '#10b981', trend: 'up' as const, trendValue: '+3%' }
        ]
      };
    }
    
    if (user?.is_engineer) {
      return {
        title: 'Панель инженера',
        tabs: [
          { id: 'overview', name: 'Обзор', icon: <DashboardIcon /> },
          { id: 'defects', name: 'Дефекты', icon: <BuildIcon /> },
          { id: 'maintenance', name: 'ТО', icon: <SettingsIcon /> }
        ],
        stats: [
          { title: 'Активные дефекты', value: 23, icon: <BuildIcon />, color: '#ea580c' },
          { title: 'Критические', value: 5, icon: <WarningIcon />, color: '#ef4444' },
          { title: 'Плановое ТО', value: 12, icon: <SettingsIcon />, color: '#3b82f6' },
          { title: 'Выполнено', value: 156, icon: <CheckCircleIcon />, color: '#10b981' }
        ]
      };
    }
    
    if (user?.is_executive) {
      return {
        title: 'Панель менеджера',
        tabs: [
          { id: 'overview', name: 'Обзор', icon: <DashboardIcon /> },
          { id: 'tasks', name: 'Управление задачами', icon: <AssignmentIcon /> },
          { id: 'reports', name: 'Отчеты', icon: <DescriptionIcon /> },
          { id: 'defects', name: 'Дефекты', icon: <BuildIcon /> },
          { id: 'projects', name: 'Проекты', icon: <ConstructionIcon /> },
          { id: 'showall', name: 'Показать все', icon: <ViewListIcon /> }
        ],
        stats: [
          { title: 'Активные задачи', value: 23, icon: <AssignmentIcon />, color: '#ea580c' },
          { title: 'Завершенные задачи', value: '94.5%', icon: <CheckCircleIcon />, color: '#10b981', trend: 'up' as const, trendValue: '+2.1%' },
          { title: 'Открытые дефекты', value: 12, icon: <BuildIcon />, color: '#ef4444' },
          { title: 'Активные проекты', value: 8, icon: <ConstructionIcon />, color: '#3b82f6' }
        ]
      };
    }

    // Default admin config
    return {
      title: 'Панель администратора',
      tabs: [
        { id: 'overview', name: 'Обзор', icon: <DashboardIcon /> },
        { id: 'projects', name: 'Проекты', icon: <ConstructionIcon /> },
        { id: 'defects', name: 'Дефекты', icon: <BuildIcon /> },
        { id: 'reports', name: 'Отчеты', icon: <AssignmentIcon /> }
      ],
      stats: [
        { title: 'Всего объектов', value: 45, icon: <BusinessIcon />, color: '#ea580c' },
        { title: 'Всего дефектов', value: 128, icon: <WarningIcon />, color: '#ef4444' },
        { title: 'Активные задачи', value: 67, icon: <AssignmentIcon />, color: '#3b82f6' },
        { title: 'Пользователи', value: 234, icon: <GroupIcon />, color: '#10b981' }
      ]
    };
  };

  const config = getRoleConfig();

  // Helper functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'paid':
        return 'success';
      case 'in_progress':
      case 'active':
      case 'on_track':
        return 'primary';
      case 'pending':
      case 'scheduled':
        return 'warning';
      case 'overdue':
      case 'at_risk':
      case 'delayed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUpIcon sx={{ color: '#10b981', fontSize: 16 }} />;
      case 'down':
        return <TrendingDownIcon sx={{ color: '#ef4444', fontSize: 16 }} />;
      case 'stable':
        return <TrendingFlatIcon sx={{ color: '#6b7280', fontSize: 16 }} />;
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setActiveTab(newValue);
  };

  return (
    <ThemeProvider theme={orangeTheme}>
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
        {/* Modern Navigation Tabs */}
        <Paper sx={{ boxShadow: '0 4px 12px rgba(0,0,0,0.1)', borderBottom: '1px solid #fed7aa' }}>
          <Container maxWidth="xl">
            <Tabs
              value={activeTab}
              onChange={handleTabChange}
              sx={{
                '& .MuiTab-root': {
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  minHeight: 64,
                  px: 3,
                  color: '#6b7280',
                  '&:hover': {
                    color: '#ea580c',
                    bgcolor: '#fff7ed',
                  },
                  '&.Mui-selected': {
                    color: 'white',
                    bgcolor: '#ea580c',
                    borderRadius: '12px 12px 0 0',
                    transform: 'scale(1.05)',
                    boxShadow: '0 4px 12px rgba(234, 88, 12, 0.3)',
                  },
                },
                '& .MuiTabs-indicator': {
                  display: 'none',
                },
              }}
            >
              {config.tabs.map((tab) => (
                <Tab
                  key={tab.id}
                  value={tab.id}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {tab.icon}
                      <span>{tab.name}</span>
                    </Box>
                  }
                />
              ))}
            </Tabs>
          </Container>
        </Paper>

        {/* Content */}
        <Container maxWidth="xl" sx={{ py: 4 }}>
          {activeTab === 'overview' && (
            <Stack spacing={4}>
              {/* Enhanced Stats Cards */}
              <Grid container spacing={3}>
                {config.stats.map((stat, index) => (
                  <Grid item xs={12} sm={6} lg={3} key={index}>
                    <Card
                      sx={{
                        borderRadius: 4,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
                          transform: 'translateY(-2px)',
                        },
                        border: '1px solid #f3f4f6',
                      }}
                    >
                      <CardContent sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box sx={{ flex: 1 }}>
                            <Typography
                              variant="body2"
                              sx={{
                                color: '#6b7280',
                                fontWeight: 600,
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                mb: 1,
                              }}
                            >
                              {stat.title}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography
                                variant="h4"
                                sx={{
                                  fontWeight: 'bold',
                                  color: '#111827',
                                }}
                              >
                                {stat.value}
                              </Typography>
                              {(stat as any).trend && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  {getTrendIcon((stat as any).trend)}
                                  {(stat as any).trendValue && (
                                    <Typography
                                      variant="body2"
                                      sx={{
                                        fontWeight: 500,
                                        color: (stat as any).trend === 'up' ? '#10b981' : 
                                               (stat as any).trend === 'down' ? '#ef4444' : '#6b7280',
                                      }}
                                    >
                                      {(stat as any).trendValue}
                                    </Typography>
                                  )}
                                </Box>
                              )}
                            </Box>
                          </Box>
                          <Avatar
                            sx={{
                              width: 56,
                              height: 56,
                              bgcolor: stat.color,
                              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                            }}
                          >
                            {stat.icon}
                          </Avatar>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>

              {/* Recent Activity Section */}
              <Grid container spacing={4}>
                {/* Recent Tasks/Projects */}
                <Grid item xs={12} lg={6}>
                  <Card
                    sx={{
                      borderRadius: 4,
                      boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                      border: '1px solid #f3f4f6',
                    }}
                  >
                    <CardContent sx={{ p: 3 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#111827' }}>
                          {user?.is_customer ? 'Активные проекты' : 'Последние задачи'}
                        </Typography>
                        <Button
                          variant="text"
                          sx={{
                            color: '#ea580c',
                            fontWeight: 600,
                            fontSize: '0.875rem',
                            '&:hover': { bgcolor: '#fff7ed' },
                          }}
                        >
                          Показать все
                        </Button>
                      </Box>
                      <Stack spacing={2}>
                        {(user?.is_customer ? mockProjects : mockTasks).slice(0, 3).map((item: any) => (
                          <Paper
                            key={item.id}
                            sx={{
                              p: 2,
                              bgcolor: '#f9fafb',
                              borderRadius: 3,
                              transition: 'all 0.2s ease',
                              '&:hover': {
                                bgcolor: '#fff7ed',
                                transform: 'translateX(4px)',
                              },
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <Box sx={{ flex: 1 }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#111827' }}>
                                  {item.title || item.name}
                                </Typography>
                                <Typography variant="body2" sx={{ color: '#6b7280', mt: 0.5 }}>
                                  {item.description || `Прогресс: ${item.progress}%`}
                                </Typography>
                                {item.assignee && (
                                  <Typography variant="caption" sx={{ color: '#9ca3af', mt: 0.5 }}>
                                    Исполнитель: {item.assignee}
                                  </Typography>
                                )}
                              </Box>
                              <Box sx={{ ml: 2, textAlign: 'right' }}>
                                <Chip
                                  label={
                                    item.status === 'pending' ? 'Ожидает' :
                                    item.status === 'in_progress' ? 'В процессе' :
                                    item.status === 'completed' ? 'Завершен' :
                                    item.status === 'active' ? 'Активен' :
                                    item.status === 'on_track' ? 'По плану' : item.status
                                  }
                                  color={getStatusColor(item.status)}
                                  size="small"
                                  sx={{ fontWeight: 600 }}
                                />
                              </Box>
                            </Box>
                          </Paper>
                        ))}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Recent Reports */}
                <Grid item xs={12} lg={6}>
                  <Card
                    sx={{
                      borderRadius: 4,
                      boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                      border: '1px solid #f3f4f6',
                    }}
                  >
                    <CardContent sx={{ p: 3 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#111827' }}>
                          Последние отчеты
                        </Typography>
                        <Button
                          variant="text"
                          sx={{
                            color: '#ea580c',
                            fontWeight: 600,
                            fontSize: '0.875rem',
                            '&:hover': { bgcolor: '#fff7ed' },
                          }}
                        >
                          Показать все
                        </Button>
                      </Box>
                      <Stack spacing={2}>
                        {mockReports.slice(0, 3).map((report) => (
                          <Paper
                            key={report.id}
                            sx={{
                              p: 2,
                              bgcolor: '#f9fafb',
                              borderRadius: 3,
                              transition: 'all 0.2s ease',
                              '&:hover': {
                                bgcolor: '#fff7ed',
                                transform: 'translateX(4px)',
                              },
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <Box sx={{ flex: 1 }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#111827' }}>
                                  {report.title}
                                </Typography>
                                <Typography variant="body2" sx={{ color: '#6b7280', mt: 0.5 }}>
                                  {report.summary}
                                </Typography>
                                <Typography variant="caption" sx={{ color: '#9ca3af', mt: 0.5 }}>
                                  {report.period} • {report.created_at}
                                </Typography>
                              </Box>
                              <Box sx={{ ml: 2 }}>
                                <Chip
                                  label="Опубликован"
                                  color="success"
                                  size="small"
                                  sx={{ fontWeight: 600 }}
                                />
                              </Box>
                            </Box>
                          </Paper>
                        ))}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Stack>
          )}

          {/* Projects Tab */}
          {activeTab === 'projects' && (
            <Stack spacing={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#111827' }}>
                  Управление проектами
                </Typography>
                <Button
                  variant="contained"
                  sx={{
                    bgcolor: '#ea580c',
                    borderRadius: 3,
                    px: 3,
                    py: 1.5,
                    fontWeight: 600,
                    boxShadow: '0 4px 12px rgba(234, 88, 12, 0.3)',
                    '&:hover': {
                      bgcolor: '#c2410c',
                      boxShadow: '0 6px 20px rgba(234, 88, 12, 0.4)',
                    },
                  }}
                >
                  + Новый проект
                </Button>
              </Box>
              
              <Grid container spacing={3}>
                {mockProjects.map((project) => (
                  <Grid item xs={12} md={6} lg={4} key={project.id}>
                    <Card
                      sx={{
                        borderRadius: 4,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
                          transform: 'translateY(-4px)',
                        },
                        border: '1px solid #f3f4f6',
                      }}
                    >
                      <CardContent sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                          <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#111827' }}>
                            {project.name}
                          </Typography>
                          <Chip
                            label={
                              project.status === 'planning' ? 'Планирование' :
                              project.status === 'active' ? 'Активен' :
                              project.status === 'on_track' ? 'По плану' :
                              project.status === 'at_risk' ? 'Риск' :
                              project.status === 'delayed' ? 'Задержка' :
                              project.status === 'completed' ? 'Завершен' : project.status
                            }
                            color={getStatusColor(project.status)}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        
                        <Typography variant="body2" sx={{ color: '#6b7280', mb: 2 }}>
                          {project.description}
                        </Typography>
                        
                        <Box sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="body2" sx={{ color: '#6b7280' }}>
                              Прогресс
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 600, color: '#111827' }}>
                              {project.progress}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={project.progress}
                            sx={{
                              height: 8,
                              borderRadius: 4,
                              bgcolor: '#f3f4f6',
                              '& .MuiLinearProgress-bar': {
                                bgcolor: project.progress === 100 ? '#10b981' : '#ea580c',
                                borderRadius: 4,
                              },
                            }}
                          />
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="caption" sx={{ color: '#9ca3af' }}>
                            {project.start_date} - {project.end_date}
                          </Typography>
                          <Button
                            size="small"
                            sx={{
                              color: '#ea580c',
                              fontWeight: 600,
                              '&:hover': { bgcolor: '#fff7ed' },
                            }}
                          >
                            Подробнее
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Stack>
          )}

          {/* Other tabs content would go here... */}

          {/* Task Management Tab */}
          {activeTab === 'tasks' && (
            <Stack spacing={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#111827' }}>
                  Управление задачами
                </Typography>
                <Button
                  variant="contained"
                  sx={{
                    bgcolor: '#ea580c',
                    borderRadius: 3,
                    px: 3,
                    py: 1.5,
                    fontWeight: 600,
                    boxShadow: '0 4px 12px rgba(234, 88, 12, 0.3)',
                    '&:hover': {
                      bgcolor: '#c2410c',
                      boxShadow: '0 6px 20px rgba(234, 88, 12, 0.4)',
                    },
                  }}
                >
                  + Новая задача
                </Button>
              </Box>
              
              <Grid container spacing={3}>
                {mockTasks.map((task) => (
                  <Grid item xs={12} md={6} lg={4} key={task.id}>
                    <Card
                      sx={{
                        borderRadius: 4,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
                          transform: 'translateY(-4px)',
                        },
                        border: '1px solid #f3f4f6',
                      }}
                    >
                      <CardContent sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                          <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#111827' }}>
                            {task.title}
                          </Typography>
                          <Chip
                            label={
                              task.priority === 'high' ? 'Высокий' :
                              task.priority === 'medium' ? 'Средний' :
                              task.priority === 'low' ? 'Низкий' : task.priority
                            }
                            color={task.priority === 'high' ? 'error' : task.priority === 'medium' ? 'warning' : 'default'}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        
                        <Typography variant="body2" sx={{ color: '#6b7280', mb: 2 }}>
                          {task.description}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="body2" sx={{ color: '#6b7280' }}>
                            Исполнитель: {task.assignee || 'Не назначен'}
                          </Typography>
                          <Chip
                            label={
                              task.status === 'pending' ? 'Ожидает' :
                              task.status === 'in_progress' ? 'В процессе' :
                              task.status === 'completed' ? 'Завершен' :
                              task.status === 'overdue' ? 'Просрочен' : task.status
                            }
                            color={getStatusColor(task.status)}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="caption" sx={{ color: '#9ca3af' }}>
                            Срок: {task.deadline}
                          </Typography>
                          <Button
                            size="small"
                            sx={{
                              color: '#ea580c',
                              fontWeight: 600,
                              '&:hover': { bgcolor: '#fff7ed' },
                            }}
                          >
                            Назначить
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Stack>
          )}

          {/* Reports Tab */}
          {activeTab === 'reports' && (
            <Stack spacing={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#111827' }}>
                  Управление отчетами
                </Typography>
                <Button
                  variant="contained"
                  sx={{
                    bgcolor: '#ea580c',
                    borderRadius: 3,
                    px: 3,
                    py: 1.5,
                    fontWeight: 600,
                    boxShadow: '0 4px 12px rgba(234, 88, 12, 0.3)',
                    '&:hover': {
                      bgcolor: '#c2410c',
                      boxShadow: '0 6px 20px rgba(234, 88, 12, 0.4)',
                    },
                  }}
                >
                  + Новый отчет
                </Button>
              </Box>
              
              <Grid container spacing={3}>
                {mockReports.map((report) => (
                  <Grid item xs={12} md={6} lg={4} key={report.id}>
                    <Card
                      sx={{
                        borderRadius: 4,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
                          transform: 'translateY(-4px)',
                        },
                        border: '1px solid #f3f4f6',
                      }}
                    >
                      <CardContent sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                          <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#111827' }}>
                            {report.title}
                          </Typography>
                          <Chip
                            label={
                              report.type === 'financial' ? 'Финансовый' :
                              report.type === 'quality' ? 'Качество' :
                              report.type === 'technical' ? 'Технический' : report.type
                            }
                            color="primary"
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        
                        <Typography variant="body2" sx={{ color: '#6b7280', mb: 2 }}>
                          {report.summary}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="body2" sx={{ color: '#6b7280' }}>
                            Период: {report.period}
                          </Typography>
                          <Chip
                            label={
                              report.status === 'draft' ? 'Черновик' :
                              report.status === 'published' ? 'Опубликован' :
                              report.status === 'archived' ? 'Архив' : report.status
                            }
                            color={getStatusColor(report.status)}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="caption" sx={{ color: '#9ca3af' }}>
                            Создан: {report.created_at}
                          </Typography>
                          <Button
                            size="small"
                            sx={{
                              color: '#ea580c',
                              fontWeight: 600,
                              '&:hover': { bgcolor: '#fff7ed' },
                            }}
                          >
                            Просмотр
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Stack>
          )}

          {/* Defects Tab */}
          {activeTab === 'defects' && (
            <Stack spacing={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#111827' }}>
                  Управление дефектами
                </Typography>
                <Button
                  variant="contained"
                  sx={{
                    bgcolor: '#ea580c',
                    borderRadius: 3,
                    px: 3,
                    py: 1.5,
                    fontWeight: 600,
                    boxShadow: '0 4px 12px rgba(234, 88, 12, 0.3)',
                    '&:hover': {
                      bgcolor: '#c2410c',
                      boxShadow: '0 6px 20px rgba(234, 88, 12, 0.4)',
                    },
                  }}
                >
                  + Новый дефект
                </Button>
              </Box>
              
              <Grid container spacing={3}>
                {[
                  { id: 1, title: 'Протечка в системе отопления', severity: 'critical', location: 'Здание А, 3 этаж', status: 'open', created: '2024-01-20' },
                  { id: 2, title: 'Неисправность лифта №2', severity: 'high', location: 'Здание Б, лифт 2', status: 'in_progress', created: '2024-01-18' },
                  { id: 3, title: 'Трещина в стене', severity: 'medium', location: 'Здание А, 1 этаж', status: 'resolved', created: '2024-01-15' }
                ].map((defect) => (
                  <Grid item xs={12} md={6} lg={4} key={defect.id}>
                    <Card
                      sx={{
                        borderRadius: 4,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
                          transform: 'translateY(-4px)',
                        },
                        border: '1px solid #f3f4f6',
                      }}
                    >
                      <CardContent sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                          <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#111827' }}>
                            {defect.title}
                          </Typography>
                          <Chip
                            label={
                              defect.severity === 'critical' ? 'Критический' :
                              defect.severity === 'high' ? 'Высокий' :
                              defect.severity === 'medium' ? 'Средний' :
                              defect.severity === 'low' ? 'Низкий' : defect.severity
                            }
                            color={
                              defect.severity === 'critical' ? 'error' :
                              defect.severity === 'high' ? 'error' :
                              defect.severity === 'medium' ? 'warning' : 'default'
                            }
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        
                        <Typography variant="body2" sx={{ color: '#6b7280', mb: 2 }}>
                          Местоположение: {defect.location}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Chip
                            label={
                              defect.status === 'open' ? 'Открыт' :
                              defect.status === 'in_progress' ? 'В работе' :
                              defect.status === 'resolved' ? 'Решен' : defect.status
                            }
                            color={getStatusColor(defect.status)}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="caption" sx={{ color: '#9ca3af' }}>
                            Создан: {defect.created}
                          </Typography>
                          <Button
                            size="small"
                            sx={{
                              color: '#ea580c',
                              fontWeight: 600,
                              '&:hover': { bgcolor: '#fff7ed' },
                            }}
                          >
                            Подробнее
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Stack>
          )}

          {/* Show All Tab */}
          {activeTab === 'showall' && (
            <Stack spacing={4}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#111827' }}>
                Полный список задач и отчетов
              </Typography>
              
              {/* All Tasks Section */}
              <Card sx={{ borderRadius: 4, boxShadow: '0 4px 20px rgba(0,0,0,0.08)', border: '1px solid #f3f4f6' }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#111827', mb: 3 }}>
                    Все задачи
                  </Typography>
                  <Grid container spacing={2}>
                    {mockTasks.map((task) => (
                      <Grid item xs={12} key={task.id}>
                        <Paper
                          sx={{
                            p: 2,
                            borderRadius: 3,
                            border: '1px solid #f3f4f6',
                            '&:hover': { bgcolor: '#fafafa' },
                          }}
                        >
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="h6" sx={{ fontWeight: 600, color: '#111827' }}>
                                {task.title}
                              </Typography>
                              <Typography variant="body2" sx={{ color: '#6b7280', mt: 0.5 }}>
                                {task.description}
                              </Typography>
                              <Typography variant="caption" sx={{ color: '#9ca3af', mt: 0.5 }}>
                                Исполнитель: {task.assignee || 'Не назначен'} • Срок: {task.deadline}
                              </Typography>
                            </Box>
                            <Box sx={{ ml: 2, textAlign: 'right' }}>
                              <Chip
                                label={
                                  task.status === 'pending' ? 'Ожидает' :
                                  task.status === 'in_progress' ? 'В процессе' :
                                  task.status === 'completed' ? 'Завершен' :
                                  task.status === 'overdue' ? 'Просрочен' : task.status
                                }
                                color={getStatusColor(task.status)}
                                size="small"
                                sx={{ fontWeight: 600 }}
                              />
                            </Box>
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>

              {/* All Reports Section */}
              <Card sx={{ borderRadius: 4, boxShadow: '0 4px 20px rgba(0,0,0,0.08)', border: '1px solid #f3f4f6' }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#111827', mb: 3 }}>
                    Все отчеты
                  </Typography>
                  <Grid container spacing={2}>
                    {mockReports.map((report) => (
                      <Grid item xs={12} key={report.id}>
                        <Paper
                          sx={{
                            p: 2,
                            borderRadius: 3,
                            border: '1px solid #f3f4f6',
                            '&:hover': { bgcolor: '#fafafa' },
                          }}
                        >
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="h6" sx={{ fontWeight: 600, color: '#111827' }}>
                                {report.title}
                              </Typography>
                              <Typography variant="body2" sx={{ color: '#6b7280', mt: 0.5 }}>
                                {report.summary}
                              </Typography>
                              <Typography variant="caption" sx={{ color: '#9ca3af', mt: 0.5 }}>
                                {report.period} • Создан: {report.created_at}
                              </Typography>
                            </Box>
                            <Box sx={{ ml: 2 }}>
                              <Chip
                                label={
                                  report.status === 'draft' ? 'Черновик' :
                                  report.status === 'published' ? 'Опубликован' :
                                  report.status === 'archived' ? 'Архив' : report.status
                                }
                                color={getStatusColor(report.status)}
                                size="small"
                                sx={{ fontWeight: 600 }}
                              />
                            </Box>
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Stack>
          )}
        </Container>
      </Box>
    </ThemeProvider>
  );
};

export default UnifiedDashboard;