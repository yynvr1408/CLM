import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, message, Card, Space } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
// Removed useNavigate
import apiService from '../services/api';
import { ContractTemplate } from '../types';

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<ContractTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadTemplates(); }, []);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const data = await apiService.getTemplates(0, 50);
      setTemplates(data.items || []);
    } catch (err: any) {
      message.error(err.message || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiService.deleteTemplate(id);
      message.success('Template deleted');
      loadTemplates();
    } catch (err: any) { message.error(err.message); }
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name', render: (v: string) => <b>{v}</b> },
    { title: 'Type', dataIndex: 'contract_type', key: 'contract_type', render: (v: string) => <Tag>{v}</Tag> },
    { title: 'Version', dataIndex: 'version', key: 'version' },
    {
      title: 'Clauses',
      key: 'clauses',
      render: (_: any, r: ContractTemplate) => <Tag color="blue">{r.clauses?.length || 0} clauses</Tag>,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, r: ContractTemplate) => (
        <Space>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)}>Delete</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Contract Templates</h1>
      </div>

      <Card bordered={false}>
        <Table
          dataSource={templates}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default Templates;
