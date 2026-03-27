import React, { useState, useEffect } from 'react';
import { Layout, Button, Table, Space, Tag, message, Modal, Input } from 'antd';
import { CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import { Approval } from '../types';
import './Approvals.css';

const { Content } = Layout;
const { TextArea } = Input;

const Approvals: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });

  // Approval/Rejection modal state
  const [actionModal, setActionModal] = useState<{
    visible: boolean;
    type: 'approve' | 'reject';
    approvalId: number;
  }>({ visible: false, type: 'approve', approvalId: 0 });
  const [comments, setComments] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

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

  const openActionModal = (approvalId: number, type: 'approve' | 'reject') => {
    setActionModal({ visible: true, type, approvalId });
    setComments('');
  };

  const handleAction = async () => {
    const { type, approvalId } = actionModal;

    if (type === 'reject' && !comments.trim()) {
      message.warning('Please provide a reason for rejection');
      return;
    }

    setActionLoading(true);
    try {
      if (type === 'approve') {
        await apiService.approveContract(approvalId, comments || undefined);
        message.success('Contract approved successfully');
      } else {
        await apiService.rejectContract(approvalId, comments);
        message.success('Contract rejected');
      }
      setActionModal({ visible: false, type: 'approve', approvalId: 0 });
      setComments('');
      loadApprovals();
    } catch (error: any) {
      message.error(error.message || `Failed to ${type} contract`);
    } finally {
      setActionLoading(false);
    }
  };

  const columns = [
    {
      title: 'Contract ID',
      dataIndex: 'contract_id',
      key: 'contract_id',
      render: (id: number) => (
        <a onClick={() => navigate(`/contracts/${id}`)}>Contract #{id}</a>
      ),
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
              onClick={() => openActionModal(record.id, 'approve')}
            >
              Approve
            </Button>
            <Button
              danger
              icon={<CloseOutlined />}
              size="small"
              onClick={() => openActionModal(record.id, 'reject')}
            >
              Reject
            </Button>
            <Button
              type="link"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => navigate(`/contracts/${record.contract_id}`)}
            >
              View
            </Button>
          </Space>
        ) : null,
    },
  ];

  return (
    <Layout className="approvals-layout">
      <Content className="approvals-content">
        <div className="page-header">
          <h1>Pending Approvals</h1>
        </div>

        <div className="approvals-table-card">
          <Table
            loading={loading}
            dataSource={approvals}
            columns={columns}
            rowKey="id"
            scroll={{ x: 700 }}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: total,
              onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} approvals`,
            }}
          />
        </div>

        {/* Approve/Reject Modal */}
        <Modal
          title={actionModal.type === 'approve' ? 'Approve Contract' : 'Reject Contract'}
          open={actionModal.visible}
          onOk={handleAction}
          onCancel={() => {
            setActionModal({ visible: false, type: 'approve', approvalId: 0 });
            setComments('');
          }}
          confirmLoading={actionLoading}
          okText={actionModal.type === 'approve' ? 'Approve' : 'Reject'}
          okType={actionModal.type === 'reject' ? 'danger' : 'primary'}
        >
          <p>
            {actionModal.type === 'approve'
              ? 'Add optional comments for this approval:'
              : 'Please provide a reason for rejection (required):'}
          </p>
          <TextArea
            rows={4}
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder={
              actionModal.type === 'approve'
                ? 'Optional comments...'
                : 'Reason for rejection (required)...'
            }
          />
        </Modal>
      </Content>
    </Layout>
  );
};

export default Approvals;
