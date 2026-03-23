import React, { useState, useEffect } from 'react';
import { Layout, Button, Table, Space, Tag, message } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import apiService from '../services/api';
import { Approval } from '../types';

const { Content } = Layout;

const Approvals: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });

  useEffect(() => {
    loadApprovals();
  }, [pagination]);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const skip = (pagination.current - 1) * pagination.pageSize;
      const data = await apiService.getPendingApprovals(skip, pagination.pageSize);
      setApprovals(data.items || []);
      setTotal(data.total);
    } catch (error: any) {
      message.error('Failed to load approvals');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approvalId: number) => {
    try {
      await apiService.approveContract(approvalId);
      message.success('Contract approved');
      loadApprovals();
    } catch (error: any) {
      message.error('Failed to approve contract');
    }
  };

  const handleReject = async (approvalId: number) => {
    try {
      await apiService.rejectContract(approvalId, '');
      message.success('Contract rejected');
      loadApprovals();
    } catch (error: any) {
      message.error('Failed to reject contract');
    }
  };

  const columns = [
    {
      title: 'Contract ID',
      dataIndex: 'contract_id',
      key: 'contract_id',
    },
    {
      title: 'Approval Level',
      dataIndex: 'approval_level',
      key: 'approval_level',
      render: (level: number) => `Level ${level}`,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'pending' ? 'orange' : status === 'approved' ? 'green' : 'red'}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Approval) =>
        record.status === 'pending' ? (
          <Space size="small">
            <Button
              type="primary"
              icon={<CheckOutlined />}
              size="small"
              onClick={() => handleApprove(record.id)}
            >
              Approve
            </Button>
            <Button
              danger
              icon={<CloseOutlined />}
              size="small"
              onClick={() => handleReject(record.id)}
            >
              Reject
            </Button>
          </Space>
        ) : null,
    },
  ];

  return (
    <Layout>
      <Content style={{ padding: '20px' }}>
        <h1>Pending Approvals</h1>
        <Table
          loading={loading}
          dataSource={approvals}
          columns={columns}
          rowKey="id"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: total,
            onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
          }}
        />
      </Content>
    </Layout>
  );
};

export default Approvals;
