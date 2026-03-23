import React, { useState, useEffect } from 'react';
import { Layout, Button, Table, Space, Tag, Modal, Input, Select, message, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import { Contract } from '../types';
import './Contracts.css';

const { Content } = Layout;

const ContractsList: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });
  const [filters, setFilters] = useState({ status: '', search: '' });
  const [deleteModal, setDeleteModal] = useState({ visible: false, id: 0 });

  useEffect(() => {
    loadContracts();
  }, [pagination, filters]);

  const loadContracts = async () => {
    setLoading(true);
    try {
      const skip = (pagination.current - 1) * pagination.pageSize;
      const data = await apiService.getContracts(
        skip,
        pagination.pageSize,
        filters.status || undefined,
        filters.search || undefined
      );
      setContracts(data.items || []);
      setTotal(data.total);
    } catch (error: any) {
      message.error('Failed to load contracts');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiService.deleteContract(id);
      message.success('Contract deleted');
      loadContracts();
      setDeleteModal({ visible: false, id: 0 });
    } catch (error: any) {
      message.error('Failed to delete contract');
    }
  };

  const columns = [
    {
      title: 'Contract Number',
      dataIndex: 'contract_number',
      key: 'contract_number',
      sorter: (a: Contract, b: Contract) => a.contract_number.localeCompare(b.contract_number),
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Contract) => (
        <a onClick={() => navigate(`/contracts/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'contract_type',
      key: 'contract_type',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: any = {
          draft: 'blue',
          submitted: 'orange',
          approved: 'green',
          rejected: 'red',
          executed: 'green',
        };
        return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (value: number, record: Contract) => (value ? `${record.currency} ${(value / 100).toFixed(2)}` : '-'),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Contract) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/contracts/${record.id}/edit`)}
          />
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => setDeleteModal({ visible: true, id: record.id })}
          />
        </Space>
      ),
    },
  ];

  return (
    <Layout className="contracts-layout">
      <Content className="contracts-content">
        <div className="page-header">
          <h1>Contracts</h1>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="large"
            onClick={() => navigate('/contracts/new')}
          >
            New Contract
          </Button>
        </div>

        {/* Filters */}
        <Row gutter={16} className="filters-row" style={{ marginBottom: '20px' }}>
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="Search contracts..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Select
              placeholder="Filter by status"
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
              style={{ width: '100%' }}
              allowClear
            >
              <Select.Option value="draft">Draft</Select.Option>
              <Select.Option value="submitted">Submitted</Select.Option>
              <Select.Option value="approved">Approved</Select.Option>
              <Select.Option value="rejected">Rejected</Select.Option>
              <Select.Option value="executed">Executed</Select.Option>
            </Select>
          </Col>
        </Row>

        {/* Contracts Table */}
        <Table
          loading={loading}
          dataSource={contracts}
          columns={columns}
          rowKey="id"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: total,
            onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
          }}
        />

        {/* Delete Modal */}
        <Modal
          title="Delete Contract"
          open={deleteModal.visible}
          onOk={() => handleDelete(deleteModal.id)}
          onCancel={() => setDeleteModal({ visible: false, id: 0 })}
          okText="Delete"
          okType="danger"
        >
          <p>Are you sure you want to delete this contract?</p>
        </Modal>
      </Content>
    </Layout>
  );
};

export default ContractsList;
