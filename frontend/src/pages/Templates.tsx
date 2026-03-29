import React, { useState, useEffect } from 'react';
import { Layout, Table, Tag, Button, message, Space, Input } from 'antd';
import { DeleteOutlined, PlusOutlined, SearchOutlined, SnippetsOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import { ContractTemplate } from '../types';
import './Contracts.css'; // Reuse common layout styles

const { Content } = Layout;

const Templates: React.FC = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<ContractTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

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

  const filteredTemplates = templates.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.contract_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const columns = [
    { 
      title: 'Name', 
      dataIndex: 'name', 
      key: 'name', 
      render: (v: string, r: ContractTemplate) => (
        <Space>
          <SnippetsOutlined style={{ color: '#6366f1' }} />
          <a onClick={() => navigate(`/templates/${r.id}/edit`)}><b>{v}</b></a>
        </Space>
      )
    },
    { title: 'Type', dataIndex: 'contract_type', key: 'contract_type', render: (v: string) => <Tag>{v}</Tag> },
    { title: 'Version', dataIndex: 'version', key: 'version', render: (v: number) => `v${v}` },
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
          <Button size="small" type="link" onClick={() => navigate(`/templates/${r.id}/edit`)}>Edit</Button>
          <Button size="small" type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)}>Delete</Button>
        </Space>
      ),
    },
  ];

  return (
    <Layout className="contracts-layout">
      <Content className="contracts-content">
        <div className="page-header">
          <h1>Contract Templates</h1>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            size="large"
            onClick={() => navigate('/templates/new')}
          >
            New Template
          </Button>
        </div>

        <div className="contracts-filters">
          <Input
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            prefix={<SearchOutlined />}
            style={{ maxWidth: 300 }}
          />
        </div>

        <div className="contracts-table-card">
          <Table
            dataSource={filteredTemplates}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 800 }}
          />
        </div>
      </Content>
    </Layout>
  );
};

export default Templates;
