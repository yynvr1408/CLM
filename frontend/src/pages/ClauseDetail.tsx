import React, { useState, useEffect } from 'react';
import { Layout, Card, Descriptions, Tag, Button, Space, Spin, message } from 'antd';
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import apiService from '../services/api';
import { Clause } from '../types';
import './ClauseDetail.css';

const { Content } = Layout;

const ClauseDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [clause, setClause] = useState<Clause | null>(null);

  useEffect(() => {
    if (id) loadClause(parseInt(id));
  }, [id]);

  const loadClause = async (clauseId: number) => {
    setLoading(true);
    try {
      const data = await apiService.getClause(clauseId);
      setClause(data);
    } catch (error: any) {
      message.error('Failed to load clause');
      navigate('/clauses');
    } finally {
      setLoading(false);
    }
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
      </Content>
    </Layout>
  );
};

export default ClauseDetail;
