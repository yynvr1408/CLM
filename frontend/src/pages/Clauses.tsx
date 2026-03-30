import React, { useState, useEffect } from 'react';
import { Layout, Button, Table, Space, Tag, Input, Select, message, Modal } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import apiService from '../services/api';
import { Clause } from '../types';
import './Clauses.css';

const { Content } = Layout;

const ClausesList: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });
  const [filters, setFilters] = useState({ category: '', search: '' });
  const { user } = useSelector((state: RootState) => state.auth);
  const isSuperAdmin = user?.is_superuser || user?.role_name === 'super_admin';
  const categories = [
    'Payment Terms',
    'Liability',
    'Termination',
    'Confidentiality',
    'Indemnification',
    'Warranty',
    'Intellectual Property',
  ];

  useEffect(() => {
    loadClauses();
  }, [pagination, filters]);

  const loadClauses = async () => {
    setLoading(true);
    try {
      const skip = (pagination.current - 1) * pagination.pageSize;
      const data = await apiService.getClauses(
        skip,
        pagination.pageSize,
        filters.category || undefined,
        filters.search || undefined
      );
      setClauses(data.items || []);
      setTotal(data.total);
    } catch (error: any) {
      message.error('Failed to load clauses');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDelete = async (id: number) => {
    message.loading({ content: 'Deleting clause...', key: 'delete_clause' });
    try {
      await apiService.deleteClause(id);
      message.success({ content: 'Clause deleted successfully', key: 'delete_clause' });
      loadClauses();
    } catch (error: any) {
      message.error({ content: error.message || 'Failed to delete clause', key: 'delete_clause' });
    }
  };

  const columns = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Clause) => (
        <a onClick={() => navigate(`/clauses/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => <Tag color="blue">{category}</Tag>,
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>{isActive ? 'Active' : 'Inactive'}</Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Clause) => (
        <Space size="small">
          <Button type="link" onClick={() => navigate(`/clauses/${record.id}`)}>
            View
          </Button>
          <Button type="link" onClick={() => navigate(`/clauses/${record.id}/edit`)}>
            Edit
          </Button>
          {isSuperAdmin && (
            <Button 
              type="link" 
              danger 
              onClick={() => {
                Modal.confirm({
                  title: 'Are you sure you want to delete this clause?',
                  content: 'This action is permanent and will be logged in the audit trail.',
                  okText: 'Yes, Delete',
                  okType: 'danger',
                  cancelText: 'Cancel',
                  onOk: () => handleDelete(record.id),
                });
              }}
            >
              Delete
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Layout className="clauses-layout">
      <Content className="clauses-content">
        <div className="page-header">
          <h1>Clause Library</h1>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="large"
            onClick={() => navigate('/clauses/new')}
          >
            New Clause
          </Button>
        </div>

        {/* Filters */}
        <div className="clauses-filters">
          <Input
            placeholder="Search clauses..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="clauses-search"
            prefix={<SearchOutlined />}
          />
          <Select
            placeholder="Filter by category"
            value={filters.category || undefined}
            onChange={(value) => setFilters({ ...filters, category: value || '' })}
            className="clauses-category-select"
            allowClear
          >
            {categories.map((cat) => (
              <Select.Option key={cat} value={cat}>
                {cat}
              </Select.Option>
            ))}
          </Select>
        </div>

        {/* Clauses Table */}
        <div className="clauses-table-card">
          <Table
            loading={loading}
            dataSource={clauses}
            columns={columns}
            rowKey="id"
            scroll={{ x: 700 }}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: total,
              onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} clauses`,
            }}
          />
        </div>
      </Content>
    </Layout>
  );
};

export default ClausesList;
