import React, { useState, useEffect } from 'react';
import { Layout, Table, Tag, message, Alert } from 'antd';
import { BellOutlined } from '@ant-design/icons';
import apiService from '../services/api';
import { Renewal } from '../types';

const { Content } = Layout;

const Renewals: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [renewals, setRenewals] = useState<Renewal[]>([]);
  const [upcomingRenewals, setUpcomingRenewals] = useState<Renewal[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });

  useEffect(() => {
    loadRenewals();
    loadUpcomingRenewals();
  }, [pagination]);

  const loadRenewals = async () => {
    setLoading(true);
    try {
      const skip = (pagination.current - 1) * pagination.pageSize;
      const data = await apiService.getOverdueRenewals(skip, pagination.pageSize);
      setRenewals(data.items || []);
      setTotal(data.total);
    } catch (error: any) {
      message.error('Failed to load renewals');
    } finally {
      setLoading(false);
    }
  };

  const loadUpcomingRenewals = async () => {
    try {
      const data = await apiService.getUpcomingRenewals(0, 10, 30);
      setUpcomingRenewals(data.items || []);
    } catch (error: any) {
      console.error('Failed to load upcoming renewals');
    }
  };

  const columns = [
    {
      title: 'Contract ID',
      dataIndex: 'contract_id',
      key: 'contract_id',
    },
    {
      title: 'Renewal Date',
      dataIndex: 'renewal_date',
      key: 'renewal_date',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Alert Date',
      dataIndex: 'alert_date',
      key: 'alert_date',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: any = {
          pending: 'red',
          notified: 'orange',
          renewed: 'green',
          expired: 'red',
        };
        return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Notified',
      dataIndex: 'notification_sent',
      key: 'notification_sent',
      render: (sent: boolean) => (sent ? '✓' : '✗'),
    },
  ];

  return (
    <Layout>
      <Content style={{ padding: '20px' }}>
        <h1>Contract Renewals</h1>

        {/* Upcoming Renewals Alert */}
        {upcomingRenewals.length > 0 && (
          <Alert
            message={`${upcomingRenewals.length} contracts coming up for renewal in the next 30 days`}
            type="warning"
            icon={<BellOutlined />}
            closable
            style={{ marginBottom: '20px' }}
          />
        )}

        <h2>Overdue & Pending Renewals</h2>
        <Table
          loading={loading}
          dataSource={renewals}
          columns={columns}
          rowKey="id"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: total,
            onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
          }}
        />

        {upcomingRenewals.length > 0 && (
          <>
            <h2 className="renewals-section-title">Upcoming Renewals (Next 30 Days)</h2>
            <Table
              dataSource={upcomingRenewals}
              columns={columns}
              rowKey="id"
              pagination={false}
            />
          </>
        )}
      </Content>
    </Layout>
  );
};

export default Renewals;
