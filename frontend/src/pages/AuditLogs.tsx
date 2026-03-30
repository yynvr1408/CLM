import React, { useState, useEffect } from 'react';
import { Layout, Table, Tag, Select, Card, message, Row, Col, Button, Tooltip, Space } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import apiService from '../services/api';
import { AuditLog } from '../types';
import './AuditLogs.css';

const { Content } = Layout;

const AuditLogs: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });
  const [filters, setFilters] = useState<{ action: string; resource_type: string }>({
    action: '',
    resource_type: '',
  });

  useEffect(() => {
    loadLogs();
  }, [pagination, filters]);

  const loadLogs = async () => {
  setLoading(true);

  try {
    const skip = (pagination.current - 1) * pagination.pageSize;
    const params = new URLSearchParams();

    params.append("skip", skip.toString());
    params.append("limit", pagination.pageSize.toString());

    if (filters.action) params.append("action", filters.action);
    if (filters.resource_type) params.append("resource_type", filters.resource_type);

    const data = await apiService.getAuditLogs(params);

    const items = data.items ?? [];
    const totalCount = data.total ?? items.length;

    setLogs(items);
    setTotal(totalCount);

  } catch (error: any) {
    console.error(error);
    message.error("Failed to load audit logs");
  } finally {
    setLoading(false);
  }
};

  const handleExport = () => {
    const url = apiService.getAuditExportUrl();
    // Use a hidden anchor to trigger download
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    message.success('Export started');
  };

  const actionColors: Record<string, string> = {
    create: 'green',
    update: 'blue',
    delete: 'red',
    submit: 'orange',
    approve: 'green',
    reject: 'red',
    login: 'cyan',
    register: 'purple',
  };

  const getActionColor = (action: string) => {
    for (const [key, color] of Object.entries(actionColors)) {
      if (action.toLowerCase().includes(key)) return color;
    }
    return 'default';
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
      sorter: (a: AuditLog, b: AuditLog) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      defaultSortOrder: 'descend' as const,
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      width: 150,
      render: (action: string) => <Tag color={getActionColor(action)}>{action}</Tag>,
    },
    {
      title: 'Resource',
      dataIndex: 'resource_type',
      key: 'resource_type',
      width: 120,
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: 'Resource ID',
      dataIndex: 'resource_id',
      key: 'resource_id',
      width: 100,
      render: (id: number) => id || '-',
    },
    {
      title: 'User ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 80,
    },
    {
      title: 'Contract ID',
      dataIndex: 'contract_id',
      key: 'contract_id',
      width: 100,
      render: (id: number) => id || '-',
    },
    {
      title: 'Changes',
      dataIndex: 'changes',
      key: 'changes',
      ellipsis: true,
      render: (changes: Record<string, any>) =>
        changes ? (
          <pre className="changes-pre">
            {JSON.stringify(changes, null, 1)}
          </pre>
        ) : (
          '-'
        ),
    },
  ];

  return (
    <Layout className="audit-layout">
      <Content className="audit-content">
        <div className="page-header">
          <h1>Audit Logs</h1>
          <Space>
            <Tooltip title="Export all logs as CSV">
              <Button icon={<DownloadOutlined />} onClick={handleExport}>
                Export CSV
              </Button>
            </Tooltip>
            <Button icon={<ReloadOutlined />} onClick={loadLogs}>
              Refresh
            </Button>
          </Space>
        </div>

        <Card className="audit-card">
          <Row gutter={16} className="audit-filters-row">
            <Col xs={24} sm={8}>
              <Select
                placeholder="Filter by action"
                value={filters.action || undefined}
                onChange={(value) => setFilters({ ...filters, action: value || '' })}
                style={{ width: '100%' }}
                allowClear
              >
                <Select.Option value="create">Create</Select.Option>
                <Select.Option value="update">Update</Select.Option>
                <Select.Option value="delete">Delete</Select.Option>
                <Select.Option value="submit">Submit</Select.Option>
                <Select.Option value="approve">Approve</Select.Option>
                <Select.Option value="reject">Reject</Select.Option>
              </Select>
            </Col>
            <Col xs={24} sm={8}>
              <Select
                placeholder="Filter by resource"
                value={filters.resource_type || undefined}
                onChange={(value) => setFilters({ ...filters, resource_type: value || '' })}
                style={{ width: '100%' }}
                allowClear
              >
                <Select.Option value="contract">Contract</Select.Option>
                <Select.Option value="clause">Clause</Select.Option>
                <Select.Option value="approval">Approval</Select.Option>
                <Select.Option value="renewal">Renewal</Select.Option>
                <Select.Option value="user">User</Select.Option>
              </Select>
            </Col>
          </Row>

          <Table
            loading={loading}
            dataSource={logs}
            columns={columns}
            rowKey="id"
            size="small"
            scroll={{ x: 900 }}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: total,
              onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} records`,
            }}
          />
        </Card>
      </Content>
    </Layout>
  );
};

export default AuditLogs;
