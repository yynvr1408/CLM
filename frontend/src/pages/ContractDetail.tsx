import React, { useState, useEffect } from 'react';
import { Layout, Card, Descriptions, Tag, Button, Table, Space, Spin, message, Timeline, Tabs } from 'antd';
import { ArrowLeftOutlined, EditOutlined, SendOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import apiService from '../services/api';
import { Approval, AuditLogResponse } from '../types';
import './ContractDetail.css';

const { Content } = Layout;

const ContractDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { user } = useSelector((state: RootState) => state.auth);
  
  const [loading, setLoading] = useState(true);
  const [contract, setContract] = useState<any>(null);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [auditTrail, setAuditTrail] = useState<AuditLogResponse[]>([]);

  const isAuthorized = user?.is_superuser || 
                       ['super_admin', 'admin', 'contract_manager'].includes(user?.role_name || '');

  useEffect(() => {
    if (id) loadContractData(parseInt(id));
  }, [id, user]);

  const loadContractData = async (contractId: number) => {
    setLoading(true);
    try {
      const fetchHistory = isAuthorized 
        ? apiService.getContractHistory(contractId).catch(() => [])
        : Promise.resolve([]);

      const [contractData, approvalsData, auditData] = await Promise.all([
        apiService.getContract(contractId),
        apiService.getContractApprovals(contractId).catch(() => ({ items: [] })),
        fetchHistory
      ]);
      setContract(contractData);
      setApprovals(approvalsData.items || approvalsData || []);
      setAuditTrail(auditData || []);
    } catch (error: any) {
      message.error('Failed to load contract');
      navigate('/contracts');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!id) return;
    try {
      await apiService.submitContract(parseInt(id));
      message.success('Contract submitted for approval');
      loadContractData(parseInt(id));
    } catch (error: any) {
      message.error(error.message || 'Failed to submit');
    }
  };

  const statusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'blue',
      submitted: 'orange',
      approved: 'green',
      rejected: 'red',
      executed: 'green',
    };
    return colors[status] || 'default';
  };

  const approvalColumns = [
    {
      title: 'Level',
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
      title: 'Comments',
      dataIndex: 'comments',
      key: 'comments',
      render: (text: string) => text || '-',
    },
    {
      title: 'Date',
      dataIndex: 'approved_at',
      key: 'approved_at',
      render: (date: string) => (date ? new Date(date).toLocaleDateString() : 'Pending'),
    },
  ];

  if (loading) {
    return (
      <Layout className="contract-detail-layout">
        <Content className="contract-detail-content">
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  if (!contract) return null;

  const detailTabs = [
    {
      key: 'details',
      label: 'Details',
      children: (
        <Descriptions bordered column={{ xs: 1, sm: 2 }}>
          <Descriptions.Item label="Contract Number">{contract.contract_number}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={statusColor(contract.status)}>{contract.status.toUpperCase()}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Type">{contract.contract_type}</Descriptions.Item>
          <Descriptions.Item label="Value">
            {contract.value ? `${contract.currency} ${(contract.value / 100).toFixed(2)}` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Start Date">
            {contract.start_date || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="End Date">
            {contract.end_date || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Created">
            {new Date(contract.created_at).toLocaleDateString()}
          </Descriptions.Item>
          <Descriptions.Item label="Last Updated">
            {new Date(contract.updated_at).toLocaleDateString()}
          </Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>
            {contract.description || 'No description provided'}
          </Descriptions.Item>
        </Descriptions>
      ),
    },
    {
      key: 'clauses',
      label: `Clauses (${contract.clauses?.length || 0})`,
      children: contract.clauses && contract.clauses.length > 0 ? (
        <Table
          dataSource={contract.clauses}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            { title: 'Title', dataIndex: 'title', key: 'title' },
            {
              title: 'Category',
              dataIndex: 'category',
              key: 'category',
              render: (cat: string) => <Tag color="blue">{cat}</Tag>,
            },
            { title: 'Version', dataIndex: 'version', key: 'version' },
          ]}
        />
      ) : (
        <p>No clauses attached to this contract.</p>
      ),
    },
    {
      key: 'approvals',
      label: `Approvals (${approvals.length})`,
      children: (
        <Table
          dataSource={approvals}
          columns={approvalColumns}
          rowKey="id"
          size="small"
          pagination={false}
        />
      ),
    },
  ];

  if (isAuthorized) {
    detailTabs.push({
      key: 'audit',
      label: 'Audit Trail',
      children: auditTrail.length > 0 ? (
        <Timeline
          mode="left"
          items={auditTrail.map((log) => {
            const getLogColor = (action: string) => {
              switch (action.toUpperCase()) {
                case 'CREATE': return 'green';
                case 'UPDATE': return 'blue';
                case 'SUBMIT': return 'orange';
                case 'APPROVE': return 'green';
                case 'REJECT': return 'red';
                case 'DELETE': return 'red';
                default: return 'gray';
              }
            };

            return {
              color: getLogColor(log.action),
              children: (
                <div className="audit-timeline-item">
                  <div className="audit-header">
                    <Tag color={getLogColor(log.action)}>{log.action.toUpperCase()}</Tag>
                    <span className="audit-user">{log.user_full_name || 'System'}</span>
                    <span className="audit-time">
                      {new Date(log.created_at).toLocaleString()}
                    </span>
                  </div>
                  {log.changes && Object.keys(log.changes).length > 0 && (
                    <div className="audit-changes">
                      <ul className="audit-changes-list">
                        {Object.entries(log.changes).map(([field, delta]: [string, any]) => (
                          <li key={field}>
                            <span className="field-name">{field}:</span>
                            <span className="old-val">{String(delta.old)}</span>
                            <span className="arrow">→</span>
                            <span className="new-val">{String(delta.new)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ),
            };
          })}
        />
      ) : (
        <p>No audit trail available.</p>
      ),
    });
  }

  return (
    <Layout className="contract-detail-layout">
      <Content className="contract-detail-content">
        <div className="page-header">
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/contracts')}>
              Back
            </Button>
            <h1>{contract.title}</h1>
            <Tag color={
              contract.status === 'active' ? 'green' : 
              contract.status === 'expired' ? 'red' : 
              'orange'
            }>
              {contract.status.toUpperCase()}
            </Tag>
          </Space>
          <Space>
            {contract.status === 'draft' && (
              <Button type="primary" icon={<SendOutlined />} onClick={handleSubmit}>
                Submit for Approval
              </Button>
            )}
            <Button icon={<EditOutlined />} onClick={() => navigate(`/contracts/${id}/edit`)}>
              Edit
            </Button>
          </Space>
        </div>

        <Card className="detail-card">
          <Tabs items={detailTabs} />
        </Card>
      </Content>
    </Layout>
  );
};

export default ContractDetail;
