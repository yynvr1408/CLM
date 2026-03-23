import React, { useState, useEffect } from 'react';
import { Layout, Row, Col, Card, Statistic, Table, Tag, Button, Spin, message } from 'antd';
import { FileTextOutlined, CheckCircleOutlined, ClockCircleOutlined, BellOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import { Contract, Renewal } from '../types';
import './Dashboard.css';

const { Content } = Layout;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [renewals, setRenewals] = useState<Renewal[]>([]);
  const [stats, setStats] = useState({
    totalContracts: 0,
    draftContracts: 0,
    approvedContracts: 0,
    upcomingRenewals: 0,
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load contracts
      const contractsData = await apiService.getContracts(0, 5);
      setContracts(contractsData.items || []);
      setStats((prev) => ({
        ...prev,
        totalContracts: contractsData.total,
        draftContracts: contractsData.items?.filter((c: Contract) => c.status === 'draft').length || 0,
        approvedContracts: contractsData.items?.filter((c: Contract) => c.status === 'approved').length || 0,
      }));

      // Load upcoming renewals
      const renewalsData = await apiService.getUpcomingRenewals(0, 5);
      setRenewals(renewalsData.items || []);
      setStats((prev) => ({
        ...prev,
        upcomingRenewals: renewalsData.total,
      }));
    } catch (error: any) {
      message.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const contractColumns = [
    {
      title: 'Contract Number',
      dataIndex: 'contract_number',
      key: 'contract_number',
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
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
      title: 'Action',
      key: 'action',
      render: (_: any, record: Contract) => (
        <Button type="link" onClick={() => navigate(`/contracts/${record.id}`)}>
          View
        </Button>
      ),
    },
  ];

  const renewalColumns = [
    {
      title: 'Contract',
      dataIndex: 'contract_id',
      key: 'contract_id',
    },
    {
      title: 'Renewal Date',
      dataIndex: 'renewal_date',
      key: 'renewal_date',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={status === 'pending' ? 'red' : 'green'}>{status}</Tag>,
    },
  ];

  return (
    <Layout className="dashboard-layout">
      <Content className="dashboard-content">
        <div className="page-header">
          <h1>Dashboard</h1>
          <Button type="primary" size="large" onClick={() => navigate('/contracts/new')}>
            + New Contract
          </Button>
        </div>

        {loading ? (
          <Spin size="large" />
        ) : (
          <>
            {/* Stats Cards */}
            <Row gutter={[16, 16]} className="stats-row">
              <Col xs={24} sm={12} md={6}>
                <Card className="stat-card">
                  <Statistic
                    title="Total Contracts"
                    value={stats.totalContracts}
                    prefix={<FileTextOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card className="stat-card">
                  <Statistic
                    title="Draft Contracts"
                    value={stats.draftContracts}
                    prefix={<ClockCircleOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card className="stat-card">
                  <Statistic
                    title="Approved"
                    value={stats.approvedContracts}
                    prefix={<CheckCircleOutlined />}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card className="stat-card">
                  <Statistic
                    title="Upcoming Renewals"
                    value={stats.upcomingRenewals}
                    prefix={<BellOutlined />}
                    valueStyle={{ color: '#f5222d' }}
                  />
                </Card>
              </Col>
            </Row>

            {/* Recent Contracts */}
            <Row gutter={[16, 16]} style={{ marginTop: '20px' }}>
              <Col xs={24} lg={14}>
                <Card title="Recent Contracts">
                  <Table
                    dataSource={contracts}
                    columns={contractColumns}
                    rowKey="id"
                    pagination={false}
                    size="small"
                  />
                </Card>
              </Col>

              {/* Upcoming Renewals */}
              <Col xs={24} lg={10}>
                <Card title="Upcoming Renewals">
                  <Table
                    dataSource={renewals}
                    columns={renewalColumns}
                    rowKey="id"
                    pagination={false}
                    size="small"
                  />
                </Card>
              </Col>
            </Row>
          </>
        )}
      </Content>
    </Layout>
  );
};

export default Dashboard;
