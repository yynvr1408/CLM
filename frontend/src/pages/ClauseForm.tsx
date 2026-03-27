import React, { useState, useEffect } from 'react';
import { Layout, Form, Input, Select, Button, Card, message, Spin, Space } from 'antd';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import apiService from '../services/api';
import './ClauseForm.css';

const { Content } = Layout;
const { TextArea } = Input;

const categories = [
  'Payment Terms',
  'Liability',
  'Termination',
  'Confidentiality',
  'Indemnification',
  'Warranty',
  'Intellectual Property',
];

const ClauseForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isEdit && id) {
      loadClause(parseInt(id));
    }
  }, [id]);

  const loadClause = async (clauseId: number) => {
    setLoading(true);
    try {
      const data = await apiService.getClause(clauseId);
      form.setFieldsValue({
        title: data.title,
        content: data.content,
        category: data.category,
      });
    } catch (error: any) {
      message.error('Failed to load clause');
      navigate('/clauses');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    setSaving(true);
    try {
      if (isEdit && id) {
        await apiService.updateClause(parseInt(id), values);
        message.success('Clause updated successfully');
      } else {
        await apiService.createClause(values);
        message.success('Clause created successfully');
      }
      navigate('/clauses');
    } catch (error: any) {
      message.error(error.message || 'Failed to save clause');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout className="clause-form-layout">
        <Content className="clause-form-content">
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  return (
    <Layout className="clause-form-layout">
      <Content className="clause-form-content">
        <div className="page-header">
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/clauses')}>
              Back
            </Button>
            <h1>{isEdit ? 'Edit Clause' : 'New Clause'}</h1>
          </Space>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={saving}
            onClick={() => form.submit()}
          >
            {isEdit ? 'Update' : 'Create'} Clause
          </Button>
        </div>

        <Card title="Clause Details" className="form-card">
          <Form form={form} layout="vertical" onFinish={handleSubmit}>
            <Form.Item
              name="title"
              label="Clause Title"
              rules={[{ required: true, message: 'Please enter a clause title' }]}
            >
              <Input placeholder="Enter clause title" />
            </Form.Item>

            <Form.Item
              name="category"
              label="Category"
              rules={[{ required: true, message: 'Please select a category' }]}
            >
              <Select placeholder="Select category">
                {categories.map((cat) => (
                  <Select.Option key={cat} value={cat}>
                    {cat}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="content"
              label="Clause Content"
              rules={[{ required: true, message: 'Please enter clause content' }]}
            >
              <TextArea
                rows={10}
                placeholder="Enter the full clause text..."
              />
            </Form.Item>
          </Form>
        </Card>
      </Content>
    </Layout>
  );
};

export default ClauseForm;
