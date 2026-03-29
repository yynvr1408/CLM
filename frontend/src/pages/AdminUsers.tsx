import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, message, Select, Modal, Space, Card, Tabs, Input, Badge } from 'antd';
import { CheckOutlined, StopOutlined, UnlockOutlined, UserAddOutlined, SearchOutlined } from '@ant-design/icons';
import apiService from '../services/api';
import { User, Role } from '../types';

const { TabPane } = Tabs;

const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [search, setSearch] = useState('');

  useEffect(() => { loadData(); }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const filters: any = {};
      if (activeTab === 'pending') { filters.is_approved = false; }
      if (activeTab === 'inactive') { filters.is_active = false; }

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

  return (
    <div style={{ padding: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>User Management</h1>
        <Input
          placeholder="Search users..."
          prefix={<SearchOutlined />}
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: 260 }}
        />
      </div>

      <Card bordered={false} bodyStyle={{ padding: 0 }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} style={{ paddingLeft: 16 }}>
          <TabPane tab="All Users" key="all" />
          <TabPane tab={<Badge count={pendingCount} offset={[10, 0]}>Pending Approval</Badge>} key="pending" />
          <TabPane tab="Inactive" key="inactive" />
        </Tabs>
        <Table
          dataSource={filteredUsers}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 15 }}
          size="middle"
        />
      </Card>
    </div>
  );
};

export default AdminUsers;
