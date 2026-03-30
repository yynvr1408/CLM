import React, { useState, useEffect } from 'react';
import { Layout, Table, Button, Space, message, Card, Input, Tag } from 'antd';
import { DownloadOutlined, DeleteOutlined, SearchOutlined, PaperClipOutlined, FileTextOutlined, SnippetsOutlined, DatabaseOutlined } from '@ant-design/icons';
import apiService from '../services/api';
import { AttachmentResponse } from '../types';
import './Clauses.css'; // Reusing some base styles

const { Content } = Layout;

const Attachments: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [attachments, setAttachments] = useState<AttachmentResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadAttachments();
  }, [pagination]);

  const loadAttachments = async () => {
    setLoading(true);
    try {
      const skip = (pagination.current - 1) * pagination.pageSize;
      const data = await apiService.getAttachments(skip, pagination.pageSize);
      setAttachments(data.items || []);
      setTotal(data.total);
    } catch (error: any) {
      message.error('Failed to load attachments');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiService.deleteAttachment(id);
      message.success('Attachment deleted');
      loadAttachments();
    } catch (error: any) {
      message.error('Failed to delete attachment');
    }
  };

  const getSourceIcon = (record: AttachmentResponse) => {
    if (record.contract_id) return <FileTextOutlined style={{ color: '#10b981' }} />;
    if (record.clause_id) return <DatabaseOutlined style={{ color: '#6366f1' }} />;
    if (record.template_id) return <SnippetsOutlined style={{ color: '#f59e0b' }} />;
    return <PaperClipOutlined />;
  };

  const getSourceType = (record: AttachmentResponse) => {
    if (record.contract_id) return 'Contract';
    if (record.clause_id) return 'Clause';
    if (record.template_id) return 'Template';
    return 'General';
  };

  const filteredAttachments = attachments.filter(a => 
    a.filename.toLowerCase().includes(search.toLowerCase())
  );

  const columns = [
    {
      title: 'File Name',
      key: 'filename',
      render: (_: any, record: AttachmentResponse) => (
        <Space>
          {getSourceIcon(record)}
          <span style={{ fontWeight: 500 }}>{record.filename}</span>
        </Space>
      ),
    },
    {
      title: 'Source',
      key: 'source',
      render: (_: any, record: AttachmentResponse) => (
        <Tag color="default">{getSourceType(record)}</Tag>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type: string) => <small>{type}</small>
    },
    {
      title: 'Size',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => `${(size / 1024).toFixed(1)} KB`
    },
    {
      title: 'Uploaded',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: AttachmentResponse) => (
        <Space>
          <Button 
            icon={<DownloadOutlined />} 
            type="primary" 
            size="small" 
            ghost
            // Assuming download endpoint format
            href={`/api/v1/attachments/download/${record.id}`}
            target="_blank"
          >
            Download
          </Button>
          <Button 
            icon={<DeleteOutlined />} 
            danger 
            size="small" 
            onClick={() => handleDelete(record.id)}
          />
        </Space>
      ),
    },
  ];

  return (
    <Layout style={{ background: 'transparent' }}>
      <Content style={{ padding: '0 24px 24px' }}>
        <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '24px 0' }}>
          <h1 style={{ margin: 0 }}>Attachments Repository</h1>
          <Input 
            placeholder="Search files..." 
            prefix={<SearchOutlined />} 
            style={{ width: 300 }}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <Card bordered={false} bodyStyle={{ padding: 0 }}>
          <Table
            dataSource={filteredAttachments}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: total,
              onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
            }}
          />
        </Card>
      </Content>
    </Layout>
  );
};

export default Attachments;
