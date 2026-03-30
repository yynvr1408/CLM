import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, message, Select, Modal, Space, Card, Tabs, Input, Badge, Spin, Descriptions } from 'antd';
import { CheckOutlined, StopOutlined, UnlockOutlined, UserAddOutlined, SearchOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import apiService from '../services/api';
import { User, Role } from '../types';

const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('users');
  const [userSubTab, setUserSubTab] = useState('all');
  const [search, setSearch] = useState('');
  const [integrityData, setIntegrityData] = useState<any>(null);
  const { user: currentUser } = useSelector((state: RootState) => state.auth);

  const isSuperAdmin = currentUser?.is_superuser || currentUser?.role_name === 'super_admin';

  useEffect(() => { 
    if (activeTab === 'users') {
      loadData(); 
    } else if (activeTab === 'integrity') {
      loadIntegrity();
    }
  }, [activeTab, userSubTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const filters: any = {};
      if (userSubTab === 'pending') { filters.is_approved = false; }
      if (userSubTab === 'inactive') { filters.is_active = false; }

      const [usersData, rolesData] = await Promise.all([
        apiService.getUsers(0, 100, filters),
        apiService.getRoles(),
      ]);
      setUsers(usersData.items || []);
      setRoles(rolesData.items || []);
    } catch (err: any) {
      message.error(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadIntegrity = async () => {
    setLoading(true);
    try {
      const data = await apiService.checkAuditIntegrity();
      setIntegrityData(data);
    } catch (err: any) {
      message.error('Failed to load integrity status');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId: number) => {
    try {
      await apiService.approveUser(userId);
      message.success('User approved');
      loadData();
    } catch (err: any) { message.error(err.message); }
  };

  const handleDeactivate = async (userId: number) => {
    Modal.confirm({
      title: 'Deactivate User',
      content: 'Are you sure you want to deactivate this user?',
      onOk: async () => {
        try {
          await apiService.deactivateUser(userId);
          message.success('User deactivated');
          loadData();
        } catch (err: any) { message.error(err.message); }
      },
    });
  };

  const handleActivate = async (userId: number) => {
    try {
      await apiService.activateUser(userId);
      message.success('User activated');
      loadData();
    } catch (err: any) { message.error(err.message); }
  };

  const handleUnlock = async (userId: number) => {
    try {
      await apiService.unlockUser(userId);
      message.success('User unlocked');
      loadData();
    } catch (err: any) { message.error(err.message); }
  };

  const handleRoleChange = async (userId: number, roleId: number) => {
    try {
      await apiService.updateUserRole(userId, roleId);
      message.success('Role updated');
      loadData();
    } catch (err: any) { message.error(err.message); }
  };

  const filteredUsers = users.filter(u =>
    !search || u.email.includes(search) || u.username.includes(search) || (u.full_name || '').includes(search)
  );

  const pendingCount = users.filter(u => !u.is_approved).length;

  const columns = [
    {
      title: 'User',
      key: 'user',
      render: (_: any, record: User) => (
        <div>
          <div style={{ fontWeight: 600 }}>{record.full_name || record.username}</div>
          <div style={{ fontSize: 12, color: '#64748b' }}>{record.email}</div>
        </div>
      ),
    },
    {
      title: 'Role',
      key: 'role',
      render: (_: any, record: User) => (
        <Select
          value={record.role_id}
          size="small"
          style={{ width: 160 }}
          onChange={(val) => handleRoleChange(record.id, val)}
          disabled={!isSuperAdmin}
        >
          {roles.map(r => (
            <Select.Option key={r.id} value={r.id}>
              {r.name}
            </Select.Option>
          ))}
        </Select>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: (_: any, record: User) => (
        <Space>
          {!record.is_approved && <Tag color="orange">PENDING</Tag>}
          {record.is_approved && record.is_active && <Tag color="green">ACTIVE</Tag>}
          {record.is_approved && !record.is_active && <Tag color="red">INACTIVE</Tag>}
          {record.is_superuser && <Tag color="purple">SUPERUSER</Tag>}
        </Space>
      ),
    },
    {
      title: 'Joined',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space size="small">
          {!record.is_approved && (
            <Button type="primary" size="small" icon={<CheckOutlined />} onClick={() => handleApprove(record.id)}>
              Approve
            </Button>
          )}
          {record.is_active && record.is_approved && (
            <Button size="small" danger icon={<StopOutlined />} onClick={() => handleDeactivate(record.id)}>
              Deactivate
            </Button>
          )}
          {!record.is_active && record.is_approved && (
            <Button size="small" type="primary" ghost icon={<UserAddOutlined />} onClick={() => handleActivate(record.id)}>
              Activate
            </Button>
          )}
          <Button size="small" icon={<UnlockOutlined />} onClick={() => handleUnlock(record.id)}>
            Unlock
          </Button>
        </Space>
      ),
    },
  ];

  const UserManagementView = (
    <div style={{ padding: '20px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>User Accounts</h2>
        <Input
          placeholder="Search users..."
          prefix={<SearchOutlined />}
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: 300 }}
        />
      </div>

      <Card bordered={false} bodyStyle={{ padding: 0 }}>
        <Tabs activeKey={userSubTab} onChange={setUserSubTab} style={{ paddingLeft: 16 }}>
          <Tabs.TabPane tab="All Users" key="all" />
          <Tabs.TabPane tab={<Badge count={pendingCount} offset={[12, 0]}>Pending Approval</Badge>} key="pending" />
          <Tabs.TabPane tab="Inactive" key="inactive" />
        </Tabs>
        <Table
          dataSource={filteredUsers}
          columns={columns}
          rowKey="id"
          loading={loading && activeTab === 'users'}
          pagination={{ pageSize: 12 }}
          size="middle"
        />
      </Card>
    </div>
  );

  const IntegrityView = (
    <div style={{ padding: '20px 0' }}>
      <Card 
        title={<span><SafetyCertificateOutlined style={{ color: '#52c41a', marginRight: 8 }} /> Platform Integrity Status</span>} 
        extra={<Button onClick={loadIntegrity} loading={loading}>Re-verify Chain</Button>}
      >
        {loading && activeTab === 'integrity' ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin tip="Performing cryptographic audit..." size="large" />
          </div>
        ) : integrityData ? (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Card type="inner" style={{ 
              backgroundColor: integrityData.is_valid ? '#f6ffed' : '#fff2f0',
              border: `1px solid ${integrityData.is_valid ? '#b7eb8f' : '#ffccc7'}`
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <Badge status={integrityData.is_valid ? 'success' : 'error'} />
                <span style={{ fontSize: 20, fontWeight: 700, color: integrityData.is_valid ? '#389e0d' : '#cf1322' }}>
                  {integrityData.is_valid ? 'SECURE: All Audit Logs Verified' : 'CRITICAL: Data Integrity Compromised'}
                </span>
              </div>
              <p style={{ marginTop: 16, fontSize: 15, color: '#434343' }}>
                {integrityData.is_valid 
                  ? 'Our automated verification system has scanned the entire audit trail and confirmed that all cryptographic hashes are intact. The data chain has not been tampered with since its creation.'
                  : `SYSTEM ALERT: The cryptographic chain was broken at Log ID ${integrityData.broken_id}. This suggests manual database modification or data corruption.`}
              </p>
            </Card>
            
            <Descriptions bordered column={2} title="Verification Metadata">
              <Descriptions.Item label="Total Records Verified">{integrityData.total_logs}</Descriptions.Item>
              <Descriptions.Item label="Last Scan Date">{new Date().toLocaleString()}</Descriptions.Item>
              <Descriptions.Item label="Verification Method">SHA-256 Chained Integrity</Descriptions.Item>
              <Descriptions.Item label="Compliance Status">Standard CLM-Audit-v1</Descriptions.Item>
            </Descriptions>
          </Space>
        ) : (
          <div style={{ textAlign: 'center', padding: 40 }}>Click Re-verify to check integrity.</div>
        )}
      </Card>
    </div>
  );

  return (
    <div style={{ padding: 24, minHeight: '100vh', background: '#f8fafc' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: '#1e293b', marginBottom: 4 }}>Admin Dashboard</h1>
        <p style={{ color: '#64748b' }}>Manage platform users and monitor system security integrity.</p>
      </div>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab} 
        type="line"
        size="large"
        items={[
          {
            key: 'users',
            label: 'User Management',
            children: UserManagementView
          },
          {
            key: 'integrity',
            label: 'Audit Integrity & Health',
            children: IntegrityView
          }
        ]}
      />
    </div>
  );
};

export default AdminUsers;
