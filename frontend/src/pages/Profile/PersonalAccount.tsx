import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';

interface UserProfile {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  position?: string;
  department?: string;
  avatar?: string;
  bio?: string;
  location?: string;
  timezone?: string;
  language?: string;
  notifications: {
    email: boolean;
    sms: boolean;
    push: boolean;
    reports: boolean;
  };
  preferences: {
    theme: 'light' | 'dark' | 'auto';
    dashboard_layout: 'compact' | 'detailed';
    date_format: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD';
    currency: 'RUB' | 'USD' | 'EUR';
  };
}

const PersonalAccount: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'notifications' | 'preferences'>('profile');
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const [profile, setProfile] = useState<UserProfile>({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone: '+7 (999) 123-45-67',
    position: 'Менеджер проектов',
    department: 'Техническое обслуживание',
    bio: 'Опытный специалист в области управления объектами недвижимости с более чем 5-летним стажем.',
    location: 'Москва, Россия',
    timezone: 'Europe/Moscow',
    language: 'ru',
    notifications: {
      email: true,
      sms: false,
      push: true,
      reports: true
    },
    preferences: {
      theme: 'light',
      dashboard_layout: 'detailed',
      date_format: 'DD/MM/YYYY',
      currency: 'RUB'
    }
  });

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  const handleProfileUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    // Here you would typically send the updated profile to your API
    console.log('Updated profile:', profile);
    setIsEditing(false);
  };

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      alert('Пароли не совпадают');
      return;
    }
    // Here you would typically send the password change request to your API
    console.log('Password change request');
    setShowPasswordModal(false);
    setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
  };

  const getRoleDisplayName = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'Администратор';
      case 'MANAGER':
        return 'Менеджер';
      case 'ENGINEER':
        return 'Инженер';
      case 'EXECUTIVE':
        return 'Руководитель';
      case 'CUSTOMER':
        return 'Заказчик';
      default:
        return role;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Личный кабинет</h1>
              <p className="text-gray-600">Управление профилем и настройками</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-orange-100 p-3 rounded-full">
                <svg className="w-8 h-8 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg p-6 sticky top-8">
              {/* User Avatar and Basic Info */}
              <div className="text-center mb-6">
                <div className="relative inline-block">
                  <div className="w-24 h-24 bg-gradient-to-r from-orange-400 to-orange-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4">
                    {profile.first_name.charAt(0)}{profile.last_name.charAt(0)}
                  </div>
                  <button className="absolute bottom-0 right-0 bg-orange-500 text-white rounded-full p-2 hover:bg-orange-600 transition-colors">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/>
                    </svg>
                  </button>
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {profile.first_name} {profile.last_name}
                </h3>
                <p className="text-sm text-gray-600">{profile.position}</p>
                <span className="inline-flex px-3 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800 mt-2">
                  {getRoleDisplayName(user?.role || '')}
                </span>
              </div>

              {/* Navigation */}
              <nav className="space-y-2">
                {[
                  { id: 'profile', name: 'Профиль', icon: '👤' },
                  { id: 'security', name: 'Безопасность', icon: '🔒' },
                  { id: 'notifications', name: 'Уведомления', icon: '🔔' },
                  { id: 'preferences', name: 'Настройки', icon: '⚙️' }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all ${
                      activeTab === tab.id
                        ? 'bg-orange-100 text-orange-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <span className="text-lg">{tab.icon}</span>
                    <span>{tab.name}</span>
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-2xl shadow-lg p-8">
              {activeTab === 'profile' && (
                <div>
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Информация профиля</h2>
                    <button
                      onClick={() => setIsEditing(!isEditing)}
                      className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                        isEditing
                          ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          : 'bg-orange-600 text-white hover:bg-orange-700'
                      }`}
                    >
                      {isEditing ? 'Отменить' : 'Редактировать'}
                    </button>
                  </div>

                  <form onSubmit={handleProfileUpdate}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Basic Information */}
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Основная информация</h3>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Имя</label>
                          <input
                            type="text"
                            value={profile.first_name}
                            onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                            disabled={!isEditing}
                            className={`w-full px-4 py-3 rounded-lg border ${
                              isEditing 
                                ? 'border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent' 
                                : 'border-gray-200 bg-gray-50'
                            } transition-colors`}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Фамилия</label>
                          <input
                            type="text"
                            value={profile.last_name}
                            onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                            disabled={!isEditing}
                            className={`w-full px-4 py-3 rounded-lg border ${
                              isEditing 
                                ? 'border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent' 
                                : 'border-gray-200 bg-gray-50'
                            } transition-colors`}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                          <input
                            type="email"
                            value={profile.email}
                            onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                            disabled={!isEditing}
                            className={`w-full px-4 py-3 rounded-lg border ${
                              isEditing 
                                ? 'border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent' 
                                : 'border-gray-200 bg-gray-50'
                            } transition-colors`}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Телефон</label>
                          <input
                            type="tel"
                            value={profile.phone}
                            onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                            disabled={!isEditing}
                            className={`w-full px-4 py-3 rounded-lg border ${
                              isEditing 
                                ? 'border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent' 
                                : 'border-gray-200 bg-gray-50'
                            } transition-colors`}
                          />
                        </div>
                      </div>

                      {/* Work Information */}
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Рабочая информация</h3>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Должность</label>
                          <input
                            type="text"
                            value={profile.position}
                            onChange={(e) => setProfile({ ...profile, position: e.target.value })}
                            disabled={!isEditing}
                            className={`w-full px-4 py-3 rounded-lg border ${
                              isEditing 
                                ? 'border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent' 
                                : 'border-gray-200 bg-gray-50'
                            } transition-colors`}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Отдел</label>
                          <input
                            type="text"
                            value={profile.department}
                            onChange={(e) => setProfile({ ...profile, department: e.target.value })}
                            disabled={!isEditing}
                            className={`w-full px-4 py-3 rounded-lg border ${
                              isEditing 
                                ? 'border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent' 
                                : 'border-gray-200 bg-gray-50'
                            } transition-colors`}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Местоположение</label>
                          <input
                            type="text"
                            value={profile.location}
                            onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                            disabled={!isEditing}
                            className={`w-full px-4 py-3 rounded-lg border ${
                              isEditing 
                                ? 'border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent' 
                                : 'border-gray-200 bg-gray-50'
                            } transition-colors`}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Часовой пояс</label>
                          <select
                            value={profile.timezone}
                            onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
                            disabled={!isEditing}
                            className={`w-full px-4 py-3 rounded-lg border ${
                              isEditing 
                                ? 'border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent' 
                                : 'border-gray-200 bg-gray-50'
                            } transition-colors`}
                          >
                            <option value="Europe/Moscow">Москва (UTC+3)</option>
                            <option value="Europe/London">Лондон (UTC+0)</option>
                            <option value="America/New_York">Нью-Йорк (UTC-5)</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Bio */}
                    <div className="mt-6">
                      <label className="block text-sm font-medium text-gray-700 mb-2">О себе</label>
                      <textarea
                        value={profile.bio}
                        onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                        disabled={!isEditing}
                        rows={4}
                        className={`w-full px-4 py-3 rounded-lg border ${
                          isEditing 
                            ? 'border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent' 
                            : 'border-gray-200 bg-gray-50'
                        } transition-colors`}
                      />
                    </div>

                    {isEditing && (
                      <div className="mt-8 flex space-x-4">
                        <button
                          type="submit"
                          className="bg-orange-600 text-white px-6 py-3 rounded-lg hover:bg-orange-700 font-medium transition-colors"
                        >
                          Сохранить изменения
                        </button>
                        <button
                          type="button"
                          onClick={() => setIsEditing(false)}
                          className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 font-medium transition-colors"
                        >
                          Отмена
                        </button>
                      </div>
                    )}
                  </form>
                </div>
              )}

              {activeTab === 'security' && (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Безопасность</h2>
                  
                  <div className="space-y-6">
                    {/* Password Section */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">Пароль</h3>
                          <p className="text-sm text-gray-600 mt-1">Последнее изменение: 15 дней назад</p>
                        </div>
                        <button
                          onClick={() => setShowPasswordModal(true)}
                          className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors"
                        >
                          Изменить пароль
                        </button>
                      </div>
                    </div>

                    {/* Two-Factor Authentication */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">Двухфакторная аутентификация</h3>
                          <p className="text-sm text-gray-600 mt-1">Дополнительная защита вашего аккаунта</p>
                        </div>
                        <div className="flex items-center space-x-3">
                          <span className="text-sm text-red-600">Отключена</span>
                          <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                            Включить
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Active Sessions */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Активные сессии</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-white rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                  <span className="text-orange-600">💻</span>
                </div>
                            <div>
                              <p className="font-medium text-gray-900">Windows • Chrome</p>
                              <p className="text-sm text-gray-600">Москва, Россия • Сейчас</p>
                            </div>
                          </div>
                          <span className="text-sm text-green-600 font-medium">Текущая</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-white rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                              <span className="text-green-600">📱</span>
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">iPhone • Safari</p>
                              <p className="text-sm text-gray-600">Москва, Россия • 2 часа назад</p>
                            </div>
                          </div>
                          <button className="text-red-600 hover:text-red-800 text-sm font-medium">
                            Завершить
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'notifications' && (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Настройки уведомлений</h2>
                  
                  <div className="space-y-6">
                    {/* Email Notifications */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Email уведомления</h3>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-medium text-gray-900">Новые заявки</p>
                            <p className="text-sm text-gray-600">Получать уведомления о новых заявках</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={profile.notifications.email}
                              onChange={(e) => setProfile({
                                ...profile,
                                notifications: { ...profile.notifications, email: e.target.checked }
                              })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600"></div>
                          </label>
                        </div>
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-medium text-gray-900">Отчеты</p>
                            <p className="text-sm text-gray-600">Еженедельные и месячные отчеты</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={profile.notifications.reports}
                              onChange={(e) => setProfile({
                                ...profile,
                                notifications: { ...profile.notifications, reports: e.target.checked }
                              })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600"></div>
                          </label>
                        </div>
                      </div>
                    </div>

                    {/* Push Notifications */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Push уведомления</h3>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-medium text-gray-900">Браузерные уведомления</p>
                            <p className="text-sm text-gray-600">Показывать уведомления в браузере</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={profile.notifications.push}
                              onChange={(e) => setProfile({
                                ...profile,
                                notifications: { ...profile.notifications, push: e.target.checked }
                              })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600"></div>
                          </label>
                        </div>
                      </div>
                    </div>

                    {/* SMS Notifications */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">SMS уведомления</h3>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-medium text-gray-900">Критические уведомления</p>
                            <p className="text-sm text-gray-600">Только для срочных заявок и аварий</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={profile.notifications.sms}
                              onChange={(e) => setProfile({
                                ...profile,
                                notifications: { ...profile.notifications, sms: e.target.checked }
                              })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600"></div>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'preferences' && (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Настройки интерфейса</h2>
                  
                  <div className="space-y-6">
                    {/* Theme */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Тема оформления</h3>
                      <div className="grid grid-cols-3 gap-4">
                        {[
                          { value: 'light', name: 'Светлая', icon: '☀️' },
                          { value: 'dark', name: 'Темная', icon: '🌙' },
                          { value: 'auto', name: 'Авто', icon: '🔄' }
                        ].map((theme) => (
                          <button
                            key={theme.value}
                            onClick={() => setProfile({
                              ...profile,
                              preferences: { ...profile.preferences, theme: theme.value as any }
                            })}
                            className={`p-4 rounded-lg border-2 transition-all ${
                              profile.preferences.theme === theme.value
                                ? 'border-orange-500 bg-orange-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className="text-2xl mb-2">{theme.icon}</div>
                            <div className="font-medium text-gray-900">{theme.name}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Dashboard Layout */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Макет дашборда</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {[
                          { value: 'compact', name: 'Компактный', description: 'Больше информации на экране' },
                          { value: 'detailed', name: 'Детальный', description: 'Подробная информация с большими карточками' }
                        ].map((layout) => (
                          <button
                            key={layout.value}
                            onClick={() => setProfile({
                              ...profile,
                              preferences: { ...profile.preferences, dashboard_layout: layout.value as any }
                            })}
                            className={`p-4 rounded-lg border-2 text-left transition-all ${
                              profile.preferences.dashboard_layout === layout.value
                                ? 'border-orange-500 bg-orange-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className="font-medium text-gray-900 mb-1">{layout.name}</div>
                            <div className="text-sm text-gray-600">{layout.description}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Date Format */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Формат даты</h3>
                      <select
                        value={profile.preferences.date_format}
                        onChange={(e) => setProfile({
                          ...profile,
                          preferences: { ...profile.preferences, date_format: e.target.value as any }
                        })}
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      >
                        <option value="DD/MM/YYYY">ДД/ММ/ГГГГ (31/12/2024)</option>
                        <option value="MM/DD/YYYY">ММ/ДД/ГГГГ (12/31/2024)</option>
                        <option value="YYYY-MM-DD">ГГГГ-ММ-ДД (2024-12-31)</option>
                      </select>
                    </div>

                    {/* Currency */}
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Валюта</h3>
                      <select
                        value={profile.preferences.currency}
                        onChange={(e) => setProfile({
                          ...profile,
                          preferences: { ...profile.preferences, currency: e.target.value as any }
                        })}
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      >
                        <option value="RUB">Российский рубль (₽)</option>
                        <option value="USD">Доллар США ($)</option>
                        <option value="EUR">Евро (€)</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-2xl bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Изменить пароль</h3>
              <form onSubmit={handlePasswordChange}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Текущий пароль
                    </label>
                    <input
                      type="password"
                      value={passwordData.current_password}
                      onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Новый пароль
                    </label>
                    <input
                      type="password"
                      value={passwordData.new_password}
                      onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Подтвердить пароль
                    </label>
                    <input
                      type="password"
                      value={passwordData.confirm_password}
                      onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      required
                    />
                  </div>
                </div>
                <div className="flex space-x-3 mt-6">
                  <button
                    type="submit"
                    className="flex-1 bg-orange-600 text-white px-4 py-3 rounded-lg hover:bg-orange-700 font-medium transition-colors"
                  >
                    Изменить пароль
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowPasswordModal(false)}
                    className="flex-1 border border-gray-300 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-50 font-medium transition-colors"
                  >
                    Отмена
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PersonalAccount;