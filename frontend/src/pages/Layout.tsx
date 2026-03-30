import React, { useState, useEffect } from 'react';
import { Layout, Menu, Dropdown, Spin, message, Badge, Popover, List, Button } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
  LogoutOutlined,
  UserOutlined,
  BellOutlined,
  AuditOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  TeamOutlined,
  SnippetsOutlined,
  PaperClipOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { setUser } from '../store/authSlice';
import apiService from '../services/api';
import { User, Notification } from '../types';
import './Layout.css';

const { Header, Sider, Content } = Layout;

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const [user, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [collapsed, setCollapsed] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [notifOpen, setNotifOpen] = useState(false);

  useEffect(() => {
    loadUser();
    loadUnreadCount();
    // Poll for notifications every 30s
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadUser = async () => {
    try {
      const currentUser = await apiService.getCurrentUser();
      setCurrentUser(currentUser);
      dispatch(setUser({
        id: currentUser.id,
        email: currentUser.email,
        username: currentUser.username,
        full_name: currentUser.full_name,
        role_id: currentUser.role_id,
        role_name: currentUser.role_name,
        permissions: currentUser.permissions || [],
        is_superuser: currentUser.is_superuser,
        is_approved: currentUser.is_approved,
        organization_id: currentUser.organization_id,
      }));
    } catch {
      // API service handles 401 redirect
    } finally {
      setLoading(false);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const data = await apiService.getUnreadCount();
      setUnreadCount(data.unread_count);
    } catch { /* ignore */ }
  };

  const loadNotifications = async () => {
    try {
      const data = await apiService.getNotifications(false, 0, 10);
      setNotifications(data.items || []);
      setUnreadCount(data.unread_count || 0);
    } catch { /* ignore */ }
  };

  const handleNotifOpen = (open: boolean) => {
    setNotifOpen(open);
    if (open) loadNotifications();
  };

  const handleMarkAllRead = async () => {
    try {
      await apiService.markNotificationsRead(undefined, true);
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch { /* ignore */ }
  };

  const handleNotifClick = (notif: Notification) => {
    if (notif.link) {
      navigate(notif.link);
      setNotifOpen(false);
    }
    if (!notif.is_read) {
      apiService.markNotificationsRead([notif.id]);
      setUnreadCount(prev => Math.max(0, prev - 1));
    }
  };

  const handleLogout = async () => {
    try {
      await apiService.logout();
      message.success('Logged out successfully');
      navigate('/login');
    } catch {
      // Force logout even on error
      apiService.clearToken();
      navigate('/login');
    }
  };

  if (loading) {
    return <Spin fullscreen />;
  }

  const hasPermission = (perm: string) => {
    if (!user) return false;
    if (user.is_superuser) return true;
    return user.permissions?.includes(perm) ?? false;
  };

  // Determine active menu key from path
  const pathKey = location.pathname.split('/')[1] || 'dashboard';
  const activeKey = ['contracts', 'clauses', 'approvals', 'renewals', 'audit', 'dashboard', 'admin', 'templates', 'attachments'].includes(pathKey) ? pathKey : 'dashboard';

  const userMenu: any = {
    items: [
      {
        label: user?.full_name || user?.email || 'User',
        key: 'profile-name',
        disabled: true,
        style: { fontWeight: 600, color: '#0f172a' },
      },
      {
        label: `${user?.role_name || 'User'} • ${user?.email}`,
        key: 'profile-email',
        disabled: true,
        style: { fontSize: 12, color: '#64748b' },
      },
      { type: 'divider' },
      {
        label: 'Logout',
        key: 'logout',
        icon: <LogoutOutlined />,
        onClick: handleLogout,
        danger: true,
      },
    ],
  };

  const menuItems: any[] = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: 'Dashboard', onClick: () => navigate('/dashboard') },
    { key: 'contracts', icon: <FileTextOutlined />, label: 'Contracts', onClick: () => navigate('/contracts') },
    { key: 'clauses', icon: <DatabaseOutlined />, label: 'Clause Library', onClick: () => navigate('/clauses') },
    { key: 'templates', icon: <SnippetsOutlined />, label: 'Templates', onClick: () => navigate('/templates') },
    { key: 'approvals', icon: <CheckCircleOutlined />, label: 'Approvals', onClick: () => navigate('/approvals') },
    { key: 'renewals', icon: <BellOutlined />, label: 'Renewals', onClick: () => navigate('/renewals') },
    { key: 'attachments', icon: <PaperClipOutlined />, label: 'Attachments', onClick: () => navigate('/attachments') },
  ];

  // Admin-only menu items
  if (hasPermission('audit:view')) {
    menuItems.push({ key: 'audit', icon: <AuditOutlined />, label: 'Audit Logs', onClick: () => navigate('/audit') });
  }
  if (hasPermission('users:manage')) {
    menuItems.push({ key: 'admin', icon: <TeamOutlined />, label: 'Admin', onClick: () => navigate('/admin/users') });
  }

  const notifContent = (
    <div style={{ width: 340 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', borderBottom: '1px solid #f0f0f0' }}>
        <span style={{ fontWeight: 600 }}>Notifications</span>
        {unreadCount > 0 && (
          <Button type="link" size="small" onClick={handleMarkAllRead}>Mark all read</Button>
        )}
      </div>
      <List
        dataSource={notifications.slice(0, 8)}
        locale={{ emptyText: 'No notifications' }}
        renderItem={(item: Notification) => (
          <List.Item
            onClick={() => handleNotifClick(item)}
            style={{
              padding: '10px 12px',
              cursor: 'pointer',
              background: item.is_read ? 'transparent' : '#f0f5ff',
            }}
          >
            <List.Item.Meta
              title={<span style={{ fontSize: 13, fontWeight: item.is_read ? 400 : 600 }}>{item.title}</span>}
              description={<span style={{ fontSize: 12, color: '#64748b' }}>{item.message}</span>}
            />
          </List.Item>
        )}
      />
    </div>
  );

  return (
    <Layout className="app-layout">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="sidebar"
        width={240}
        collapsedWidth={72}
        breakpoint="lg"
        onBreakpoint={(broken) => { if (broken) setCollapsed(true); }}
      >
        <div className="logo-section">
          <div className="logo-icon">
            <FileTextOutlined style={{ fontSize: collapsed ? 20 : 22, color: 'white' }} />
          </div>
          {!collapsed && <span className="logo-text">CLM Platform</span>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[activeKey]}
          items={menuItems}
          className="sidebar-menu"
        />
      </Sider>

      <Layout>
        <Header className="header">
          <button
            className="collapse-btn"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>

          <div className="header-right">
            <div className="header-greeting">
              {user?.full_name ? `Hi, ${user.full_name.split(' ')[0]}` : 'Welcome'}
              <span style={{ fontSize: 11, color: '#94a3b8', marginLeft: 8 }}>
                {user?.role_name}
              </span>
            </div>

            <Popover
              content={notifContent}
              trigger="click"
              open={notifOpen}
              onOpenChange={handleNotifOpen}
              placement="bottomRight"
            >
              <div className="avatar-btn" style={{ marginRight: 8, cursor: 'pointer' }}>
                <Badge count={unreadCount} size="small" offset={[-2, 2]}>
                  <BellOutlined style={{ fontSize: 18, color: '#64748b' }} />
                </Badge>
              </div>
            </Popover>

            <Dropdown menu={userMenu} placement="bottomRight" trigger={['click']}>
              <div className="avatar-btn">
                <div className="user-avatar">
                  <UserOutlined style={{ fontSize: 16, color: 'white' }} />
                </div>
              </div>
            </Dropdown>
          </div>
        </Header>

        <Content className="content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
