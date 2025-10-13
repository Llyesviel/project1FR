import React, { useState, useMemo } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Badge,
  Menu,
  MenuItem,
  Avatar,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Business as BusinessIcon,
  BugReport as DefectIcon,
  Assignment as TaskIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountCircleIcon,
  Logout as LogoutIcon,
  Engineering as EngineeringIcon,
  Build as BuildIcon,
  BarChart as BarChartIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Report as ReportIcon,
  Security as SecurityIcon,
  Inventory as InventoryIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store/store';
import { logout } from '../../store/slices/authSlice';
import { useAuth } from '../../hooks/useAuth';

const drawerWidth = 240;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  
  const { user } = useSelector((state: RootState) => state.auth);
  const { unreadCount } = useSelector((state: RootState) => state.notifications);
  const { isAdmin, isManager, isEngineer, isExecutive, isCustomer } = useAuth();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    dispatch(logout());
    handleMenuClose();
    navigate('/login');
  };

  const handleProfileClick = () => {
    navigate('/profile');
    handleMenuClose();
  };

  const handleAccountClick = () => {
    navigate('/account');
    handleMenuClose();
  };

  // Базовые пункты меню для всех пользователей
  const baseMenuItems = [
    { text: 'Панель управления', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'Объекты', icon: <BusinessIcon />, path: '/facilities' },
    { text: 'Дефекты', icon: <DefectIcon />, path: '/defects' },
    { text: 'Задачи', icon: <TaskIcon />, path: '/tasks' },
  ];

  // Роль-специфичные пункты меню
  const menuItems = useMemo(() => {
    const roleSpecificItems = [];
    
    if (isManager() || isAdmin()) {
      roleSpecificItems.push(
        {
          text: 'Управление пользователями',
          icon: <PeopleIcon />,
          path: '/users'
        },
        {
          text: 'Отчеты',
          icon: <ReportIcon />,
          path: '/reports'
        }
      );
    }
    
    if (isEngineer() || isAdmin()) {
      roleSpecificItems.push({
        text: 'Техническое обслуживание',
        icon: <BuildIcon />,
        path: '/maintenance'
      });
    }
    
    if (isExecutive() || isAdmin()) {
      roleSpecificItems.push({
        text: 'Аналитика',
        icon: <BarChartIcon />,
        path: '/analytics'
      });
    }
    
    if (isAdmin()) {
      roleSpecificItems.push(
        {
          text: 'Настройки системы',
          icon: <SettingsIcon />,
          path: '/settings'
        },
        {
          text: 'Безопасность',
          icon: <SecurityIcon />,
          path: '/security'
        }
      );
    }

    return [...baseMenuItems, ...roleSpecificItems];
  }, [isAdmin, isManager, isEngineer, isExecutive]);

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Facilities System
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
      <AppBar
        position="fixed"
        sx={{
          width: '100%',
          bgcolor: '#ea580c',
          '&:hover': {
            bgcolor: '#dc2626',
          },
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Facilities System
          </Typography>
          
          <IconButton color="inherit" onClick={() => navigate('/notifications')}>
            <Badge badgeContent={unreadCount} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
          
          <IconButton
            size="large"
            edge="end"
            aria-label="account of current user"
            aria-controls="primary-search-account-menu"
            aria-haspopup="true"
            onClick={handleProfileMenuOpen}
            color="inherit"
          >
            <Avatar sx={{ width: 32, height: 32 }}>
              {user?.first_name?.[0] || user?.username?.[0] || 'U'}
            </Avatar>
          </IconButton>
        </Toolbar>
      </AppBar>
      
      <Menu
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        keepMounted
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleProfileClick}>
          <ListItemIcon>
            <AccountCircleIcon fontSize="small" />
          </ListItemIcon>
          Профиль
        </MenuItem>
        <MenuItem onClick={handleAccountClick}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          Личный кабинет
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          Выйти
        </MenuItem>
      </Menu>
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: '100%',
          mt: '64px',
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default Layout;