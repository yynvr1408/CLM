import React, { useState, useEffect } from 'react';
import { Layout, Card, Descriptions, Tag, Button, Space, Spin, message, Table, Modal } from 'antd';
import { ArrowLeftOutlined, EditOutlined, HistoryOutlined, RollbackOutlined, PaperClipOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import apiService from '../services/api';
import { Clause, ClauseVersionResponse } from '../types';
import './ClauseDetail.css';

const { Content } = Layout;

const ClauseDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [clause, setClause] = useState<Clause | null>(null);
  const [versions, setVersions] = useState<ClauseVersionResponse[]>([]);
  const { user } = useSelector((state: RootState) => state.auth);

  const isAuthorized = user?.is_superuser || 
                       ['super_admin', 'admin', 'contract_manager'].includes(user?.role_name || '');

  useEffect(() => {
    if (id) loadClause(parseInt(id));
  }, [id, user]);

    const loadClause = async (clauseId: number) => {
    setLoading(true);
    try {
      const fetchHistory = isAuthorized 
        ? apiService.getClauseVersions(clauseId)
        : Promise.resolve([]);

      const [clauseData, versionsData] = await Promise.all([
        apiService.getClause(clauseId),
        fetchHistory
      ]);
      setClause(clauseData);
      setVersions(versionsData);
    } catch (error: any) {
      message.error('Failed to load clause');
      navigate('/clauses');
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = (versionId: number) => {
    Modal.confirm({
      title: 'Restore Version',
      content: 'Are you sure you want to restore this version? The current version will be saved as a new historical record.',
      onOk: async () => {
        try {
          if (!id) return;
          await apiService.restoreClauseVersion(parseInt(id), versionId);
          message.success('Clause restored successfully');
          loadClause(parseInt(id));
        } catch (error: any) {
          message.error(error.message || 'Failed to restore');
        }
      }
    });
  };

  if (loading) {
    return (
      <Layout className="clause-detail-layout">
        <Content className="clause-detail-content">
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  if (!clause) return null;

  return (
    <Layout className="clause-detail-layout">
      <Content className="clause-detail-content">
        <div className="page-header">
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/clauses')}>
              Back
            </Button>
            <h1>{clause.title}</h1>
            <Tag color={clause.is_active ? 'green' : 'red'}>
              {clause.is_active ? 'Active' : 'Inactive'}
            </Tag>
          </Space>
          <Button icon={<EditOutlined />} onClick={() => navigate(`/clauses/${id}/edit`)}>
            Edit
          </Button>
        </div>

        <Card className="detail-card">
          <Descriptions bordered column={1}>
            <Descriptions.Item label="Category">
              <Tag color="blue">{clause.category}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Version">{clause.version}</Descriptions.Item>
            <Descriptions.Item label="Created">
              {new Date(clause.created_at).toLocaleDateString()}
            </Descriptions.Item>
            <Descriptions.Item label="Last Updated">
              {new Date(clause.updated_at).toLocaleDateString()}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title="Clause Content" className="detail-card clause-content-card">
          <div className="clause-content-body">
            {clause.content}
          </div>
        </Card>

        {clause.attachments && clause.attachments.length > 0 && (
          <Card title={<span><PaperClipOutlined /> Attachments</span>} className="detail-card attachments-card">
            <Table
              dataSource={clause.attachments}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                { title: 'Filename', dataIndex: 'filename', key: 'filename' },
                { title: 'Type', dataIndex: 'file_type', key: 'file_type' },
                { title: 'Size', dataIndex: 'file_size', key: 'file_size', render: (s) => `${(s / 1024).toFixed(1)} KB` },
                { 
                  title: 'Action', 
                  key: 'action', 
                  render: (_, record) => (
                    <Button type="link" href={`/api/v1/attachments/download/${record.id}`} target="_blank">
                      Download
                    </Button>
                  ) 
                },
              ]}
            />
          </Card>
        )}

        {isAuthorized && (
          <Card title={<span><HistoryOutlined /> Version History</span>} className="detail-card version-history-card">
            <Table 
              dataSource={versions}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                { title: 'Ver', dataIndex: 'version_number', key: 'version_number', width: 60 },
                { title: 'Title', dataIndex: 'title', key: 'title' },
                { title: 'Category', dataIndex: 'category', key: 'category', render: (cat) => <Tag color="blue">{cat}</Tag> },
                { title: 'Date', dataIndex: 'created_at', key: 'created_at', render: (d) => new Date(d).toLocaleString() },
                {
                  title: 'Action',
                  key: 'action',
                  render: (_, record) => (
                    <Button 
                      size="small" 
                      icon={<RollbackOutlined />} 
                      onClick={() => handleRestore(record.id)}
                    >
                      Restore
                    </Button>
                  )
                }
              ]}
            />
          </Card>
        )}
      </Content>
    </Layout>
  );
};

export default ClauseDetail;
