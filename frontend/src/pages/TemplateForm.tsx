import React, { useState, useEffect } from 'react';
import { Layout, Form, Input, Select, Button, Card, message, Spin, Space, List, Checkbox, Tag } from 'antd';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import apiService from '../services/api';
import { Clause, Attachment } from '../types';
import FileUploader from '../components/FileUploader';
import './Contracts.css';

const { Content } = Layout;
const { TextArea } = Input;

const contractTypes = [
  'Service Agreement',
  'Non-Disclosure Agreement (NDA)',
  'Master Service Agreement (MSA)',
  'Statement of Work (SOW)',
  'Employment Contract',
  'Software License',
  'Procurement Agreement',
  'IT Acts & Laws Compliance',
];

const TemplateForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [selectedClauseIds, setSelectedClauseIds] = useState<number[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);


  useEffect(() => {
    loadInitialData();
  }, [id]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const clausesData = await apiService.getClauses(0, 100);
      setClauses(clausesData.items || []);

      if (isEdit && id) {
        const template = await apiService.getTemplate(parseInt(id));
        form.setFieldsValue({
          name: template.name,
          description: template.description,
          contract_type: template.contract_type,
          approval_workflow: template.approval_workflow,
        });
        setSelectedClauseIds(template.clauses?.map(c => c.id) || []);
        setAttachments(template.attachments || []);
      }
    } catch (error: any) {

      message.error('Failed to load form data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    setSaving(true);
    try {
      const templateData = {
        ...values,
        clause_ids: selectedClauseIds.map((id, index) => ({
          clause_id: id,
          order: index,
          is_required: true,
        })),
      };

      if (isEdit && id) {
        await apiService.updateTemplate(parseInt(id), templateData);
        message.success('Template updated successfully');
      } else {
        await apiService.createTemplate(templateData);
        message.success('Template created successfully');
      }
      navigate('/templates');
    } catch (error: any) {
      message.error(error.message || 'Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  const handleClauseToggle = (clauseId: number) => {
    setSelectedClauseIds(prev => 
      prev.includes(clauseId) 
        ? prev.filter(id => id !== clauseId)
        : [...prev, clauseId]
    );
  };

  if (loading) {
    return (
      <Layout className="contracts-layout">
        <Content className="contracts-content" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  return (
    <Layout className="contracts-layout">
      <Content className="contracts-content">
        <div className="page-header">
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/templates')}>
              Back
            </Button>
            <h1>{isEdit ? 'Edit Template' : 'New Contract Template'}</h1>
          </Space>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={saving}
            size="large"
            onClick={() => form.submit()}
          >
            {isEdit ? 'Update' : 'Create'} Template
          </Button>
        </div>

        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <Card title="General Information" bordered={false}>
              <Form.Item
                name="name"
                label="Template Name"
                rules={[{ required: true, message: 'Please enter a template name' }]}
              >
                <Input placeholder="e.g., Standard NDA v2" />
              </Form.Item>

              <Form.Item
                name="contract_type"
                label="Contract Type"
                rules={[{ required: true, message: 'Please select a type' }]}
              >
                <Select placeholder="Select contract type">
                  {contractTypes.map(t => (
                    <Select.Option key={t} value={t}>{t}</Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="description"
                label="Description"
              >
                <TextArea rows={4} placeholder="What is this template for?" />
              </Form.Item>

              {isEdit && (
                <FileUploader
                  parentId={{ template_id: parseInt(id!) }}
                  existingAttachments={attachments}
                  onUploadSuccess={(att) => setAttachments(prev => [...prev, att])}
                  onDeleteSuccess={(attId) => setAttachments(prev => prev.filter(a => a.id !== attId))}
                />
              )}
            </Card>


            <Card title="Select Default Clauses" bordered={false}>
              <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                <List
                  dataSource={clauses}
                  renderItem={(clause: Clause) => (
                    <List.Item
                      actions={[
                        <Checkbox 
                          checked={selectedClauseIds.includes(clause.id)} 
                          onChange={() => handleClauseToggle(clause.id)}
                        />
                      ]}
                    >
                      <List.Item.Meta
                        title={<b>{clause.title}</b>}
                        description={<Tag>{clause.category}</Tag>}
                      />
                    </List.Item>
                  )}
                />
              </div>
              {selectedClauseIds.length === 0 && (
                <div style={{ textAlign: 'center', padding: '20px', color: '#94a3b8' }}>
                  No clauses selected. Select clauses from the library to include in this template.
                </div>
              )}
            </Card>
          </div>
        </Form>
      </Content>
    </Layout>
  );
};

export default TemplateForm;
