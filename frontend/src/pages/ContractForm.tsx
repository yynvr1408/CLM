import React, { useState, useEffect } from 'react';
import { Layout, Form, Input, Select, Button, DatePicker, InputNumber, Card, message, Spin, Space, Table, Tag } from 'antd';
import { ArrowLeftOutlined, SaveOutlined, SendOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import apiService from '../services/api';
import { Contract, Clause, Attachment } from '../types';
import FileUploader from '../components/FileUploader';
import './ContractForm.css';


const { Content } = Layout;
const { TextArea } = Input;

const ContractForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [contract, setContract] = useState<Contract | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [newAttachmentIds, setNewAttachmentIds] = useState<number[]>([]);


  // Clause selection state
  const [availableClauses, setAvailableClauses] = useState<Clause[]>([]);
  const [selectedClauseIds, setSelectedClauseIds] = useState<number[]>([]);
  const [clauseLoading, setClauseLoading] = useState(false);

  useEffect(() => {
    loadClauses();
    if (isEdit && id) {
      loadContract(parseInt(id));
    }
  }, [id]);

  const loadContract = async (contractId: number) => {
    setLoading(true);
    try {
      const data = await apiService.getContract(contractId);
      setContract(data);
      form.setFieldsValue({
        title: data.title,
        description: data.description,
        contract_type: data.contract_type,
        value: data.value,
        currency: data.currency,
        start_date: data.start_date ? dayjs(data.start_date) : null,
        end_date: data.end_date ? dayjs(data.end_date) : null,
      });
      setAttachments(data.attachments || []);
      // Load associated clauses if available
      if ((data as any).clauses) {
        setSelectedClauseIds((data as any).clauses.map((c: Clause) => c.id));
      }
    } catch (error: any) {
      message.error('Failed to load contract');
      navigate('/contracts');
    } finally {
      setLoading(false);
    }
  };

  const loadClauses = async () => {
    setClauseLoading(true);
    try {
      const data = await apiService.getClauses(0, 100);
      setAvailableClauses((data.items || []).filter((c: Clause) => c.is_active));
    } catch {
      // Clauses are optional, don't block the form
    } finally {
      setClauseLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    setSaving(true);
    try {
      const payload: any = {
        title: values.title,
        description: values.description || '',
        contract_type: values.contract_type,
        value: values.value || 0,
        currency: values.currency || 'USD',
        start_date: values.start_date ? values.start_date.format('YYYY-MM-DD') : null,
        end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : null,
      };

      if (isEdit && id) {
        await apiService.updateContract(parseInt(id), payload);
        message.success('Contract updated successfully');
      } else {
        payload.clauses = selectedClauseIds.map((clauseId, index) => ({
          clause_id: clauseId,
          order: index + 1,
        }));
        payload.attachment_ids = newAttachmentIds;
        await apiService.createContract(payload);
        message.success('Contract created successfully');
      }
      navigate('/contracts');
    } catch (error: any) {
      message.error(error.message || 'Failed to save contract');
    } finally {
      setSaving(false);
    }
  };

  const handleSubmitForApproval = async () => {
    if (!isEdit || !id) return;
    try {
      await apiService.submitContract(parseInt(id));
      message.success('Contract submitted for approval');
      navigate('/contracts');
    } catch (error: any) {
      message.error(error.message || 'Failed to submit contract');
    }
  };

  const toggleClause = (clauseId: number) => {
    setSelectedClauseIds((prev) =>
      prev.includes(clauseId)
        ? prev.filter((id) => id !== clauseId)
        : [...prev, clauseId]
    );
  };

  const clauseColumns = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (cat: string) => <Tag color="blue">{cat}</Tag>,
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: Clause) => (
        <Button
          type={selectedClauseIds.includes(record.id) ? 'default' : 'primary'}
          danger={selectedClauseIds.includes(record.id)}
          size="small"
          icon={selectedClauseIds.includes(record.id) ? <DeleteOutlined /> : <PlusOutlined />}
          onClick={() => toggleClause(record.id)}
        >
          {selectedClauseIds.includes(record.id) ? 'Remove' : 'Add'}
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <Layout className="contract-form-layout">
        <Content className="contract-form-content">
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  return (
    <Layout className="contract-form-layout">
      <Content className="contract-form-content">
        <div className="page-header">
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/contracts')}>
              Back
            </Button>
            <h1>{isEdit ? 'Edit Contract' : 'New Contract'}</h1>
          </Space>
          <Space>
            {isEdit && contract?.status === 'draft' && (
              <Button
                icon={<SendOutlined />}
                onClick={handleSubmitForApproval}
              >
                Submit for Approval
              </Button>
            )}
            <Button
              type="primary"
              icon={<SaveOutlined />}
              loading={saving}
              onClick={() => form.submit()}
            >
              {isEdit ? 'Update' : 'Create'} Contract
            </Button>
          </Space>
        </div>

        <Card title="Contract Details" className="form-card">
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{ currency: 'USD', contract_type: 'service' }}
          >
            <Form.Item
              name="title"
              label="Contract Title"
              rules={[{ required: true, message: 'Please enter a contract title' }]}
            >
              <Input placeholder="Enter contract title" />
            </Form.Item>

            <Form.Item name="description" label="Description">
              <TextArea rows={4} placeholder="Enter contract description" />
            </Form.Item>

            <div className="form-grid-2col">
              <Form.Item
                name="contract_type"
                label="Contract Type"
                rules={[{ required: true, message: 'Please select a contract type' }]}
              >
                <Select placeholder="Select type">
                  <Select.Option value="service">Service Agreement</Select.Option>
                  <Select.Option value="nda">Non-Disclosure Agreement</Select.Option>
                  <Select.Option value="employment">Employment Contract</Select.Option>
                  <Select.Option value="vendor">Vendor Agreement</Select.Option>
                  <Select.Option value="lease">Lease Agreement</Select.Option>
                  <Select.Option value="partnership">Partnership Agreement</Select.Option>
                  <Select.Option value="licensing">Licensing Agreement</Select.Option>
                  <Select.Option value="other">Other</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item name="currency" label="Currency">
                <Select>
                  <Select.Option value="USD">USD</Select.Option>
                  <Select.Option value="EUR">EUR</Select.Option>
                  <Select.Option value="GBP">GBP</Select.Option>
                  <Select.Option value="INR">INR</Select.Option>
                </Select>
              </Form.Item>
            </div>

            <Form.Item name="value" label="Contract Value (in cents)">
              <InputNumber
                style={{ width: '100%' }}
                min={0}
                placeholder="Enter contract value"
              />
            </Form.Item>

            <div className="form-grid-2col">
              <Form.Item name="start_date" label="Start Date">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item name="end_date" label="End Date">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </div>

            <div style={{ marginTop: 24 }}>
              <FileUploader
                parentId={isEdit ? { contract_id: parseInt(id!) } : {}}
                existingAttachments={attachments}
                onUploadSuccess={(att) => {
                  setAttachments(prev => [...prev, att]);
                  if (!isEdit) setNewAttachmentIds(prev => [...prev, att.id]);
                }}
                onDeleteSuccess={(attId) => {
                  setAttachments(prev => prev.filter(a => a.id !== attId));
                  setNewAttachmentIds(prev => prev.filter(id => id !== attId));
                }}
              />
            </div>
          </Form>

        </Card>

        {/* Clause Selection (only for new contracts) */}
        {!isEdit && (
          <Card
            title={`Attach Clauses (${selectedClauseIds.length} selected)`}
            className="form-card"
            style={{ marginTop: '16px' }}
          >
            <Table
              loading={clauseLoading}
              dataSource={availableClauses}
              columns={clauseColumns}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 5 }}
              rowClassName={(record) =>
                selectedClauseIds.includes(record.id) ? 'clause-selected-row' : ''
              }
            />
          </Card>
        )}
      </Content>
    </Layout>
  );
};

export default ContractForm;
