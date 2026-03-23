import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Dropdown, Avatar, Spin, message } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
  LogoutOutlined,
  UserOutlined,
  BellOutlined,
  AuditOutlined,
} from '@ant-design/icons';
import { useNavigate, Outlet } from 'react-router-dom';
import apiService from '../services/api';
import { User } from '../types';
import './Layout.css';

const { Header, Sider, Content } = Layout;

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
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
    } catch (error: any) {
      message.error('Failed to load user');
      navigate('/login');
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

  const userMenu: any = {
    items: [
      {
        label: `${user?.full_name} (${user?.email})`,
        key: 'profile',
        disabled: true,
      },
      {
        type: 'divider',
      },
      {
        label: 'Logout',
        key: 'logout',
        icon: <LogoutOutlined />,
        onClick: handleLogout,
      },
    ],
  };

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      onClick: () => navigate('/dashboard'),
    },
    {
      key: 'contracts',
      icon: <FileTextOutlined />,
      label: 'Contracts',
      onClick: () => navigate('/contracts'),
    },
    {
      key: 'clauses',
      icon: <DatabaseOutlined />,
      label: 'Clause Library',
      onClick: () => navigate('/clauses'),
    },
    {
      key: 'approvals',
      icon: <CheckCircleOutlined />,
      label: 'Approvals',
      onClick: () => navigate('/approvals'),
    },
    {
      key: 'renewals',
      icon: <BellOutlined />,
      label: 'Renewals',
      onClick: () => navigate('/renewals'),
    },
    {
      key: 'audit',
      icon: <AuditOutlined />,
      label: 'Audit Logs',
      onClick: () => navigate('/audit'),
    },
  ];

  return (
    <Layout className="app-layout">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="sidebar"
      >
        <div className="logo">
          <span>CLM</span>
        </div>
        <Menu theme="dark" mode="inline" items={menuItems} />
      </Sider>

      <Layout>
        <Header className="header">
          <Button
            type="text"
            icon={collapsed ? '☰' : '⊗'}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: '18px', color: 'white' }}
          />
          <div className="header-right">
            <Dropdown menu={userMenu} placement="bottomRight">
              <Avatar
                icon={<UserOutlined />}
                className="user-menu-dropdown"
                style={{ backgroundColor: '#1890ff' }}
              />
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
