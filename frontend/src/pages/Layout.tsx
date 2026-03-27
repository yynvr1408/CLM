import React, { useState, useEffect } from 'react';
import { Layout, Menu, Dropdown, Spin, message } from 'antd';
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
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import apiService from '../services/api';
import { User } from '../types';
import './Layout.css';

const { Header, Sider, Content } = Layout;

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const currentUser = await apiService.getCurrentUser();
      setUser(currentUser);
    } catch {
      // API service handles 401 redirect — no need to navigate here
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiService.logout();
      message.success('Logged out successfully');
      navigate('/login');
    } catch (error: any) {
      message.error('Logout failed');
    }
  };

  if (loading) {
    return <Spin fullscreen />;
  }

  // Determine active menu key from path
  const pathKey = location.pathname.split('/')[1] || 'dashboard';
  const activeKey = ['contracts', 'clauses', 'approvals', 'renewals', 'audit', 'dashboard'].includes(pathKey) ? pathKey : 'dashboard';

  const userMenu: any = {
    items: [
      {
        label: user?.full_name || user?.email || 'User',
        key: 'profile-name',
        disabled: true,
        style: { fontWeight: 600, color: '#0f172a' },
      },
      {
        label: user?.email,
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

  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: 'Dashboard', onClick: () => navigate('/dashboard') },
    { key: 'contracts', icon: <FileTextOutlined />, label: 'Contracts', onClick: () => navigate('/contracts') },
    { key: 'clauses', icon: <DatabaseOutlined />, label: 'Clause Library', onClick: () => navigate('/clauses') },
    { key: 'approvals', icon: <CheckCircleOutlined />, label: 'Approvals', onClick: () => navigate('/approvals') },
    { key: 'renewals', icon: <BellOutlined />, label: 'Renewals', onClick: () => navigate('/renewals') },
    { key: 'audit', icon: <AuditOutlined />, label: 'Audit Logs', onClick: () => navigate('/audit') },
  ];

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
            </div>
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
