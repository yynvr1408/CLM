import React, { useState } from 'react';
import { Upload, message, List, Button, Space, Typography } from 'antd';
import { InboxOutlined, DeleteOutlined, FileOutlined, PaperClipOutlined } from '@ant-design/icons';
import apiService from '../services/api';
import { Attachment } from '../types';

const { Dragger } = Upload;
const { Text } = Typography;

interface FileUploaderProps {
  parentId: { contract_id?: number; clause_id?: number; template_id?: number };
  existingAttachments?: Attachment[];
  onUploadSuccess?: (attachment: Attachment) => void;
  onDeleteSuccess?: (id: number) => void;
}

const FileUploader: React.FC<FileUploaderProps> = ({ 
  parentId, 
  existingAttachments = [], 
  onUploadSuccess, 
  onDeleteSuccess 
}) => {
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (options: any) => {
    const { file, onSuccess, onError } = options;
    setUploading(true);
    try {
      const response = await apiService.uploadAttachment(file as File, parentId);
      message.success(`${file.name} uploaded successfully.`);
      if (onUploadSuccess) onUploadSuccess(response);
      onSuccess(response);
    } catch (err: any) {
      message.error(`${file.name} upload failed: ${err.message}`);
      onError(err);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiService.deleteAttachment(id);
      message.success('Attachment deleted.');
      if (onDeleteSuccess) onDeleteSuccess(id);
    } catch (err: any) {
      message.error(`Failed to delete: ${err.message}`);
    }
  };

  return (
    <div className="file-uploader" style={{ marginTop: 16 }}>
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <PaperClipOutlined style={{ color: '#6366f1' }} />
          <Text strong>Media & Attachments</Text>
        </div>

        <Dragger 
          customRequest={handleUpload} 
          showUploadList={false}
          disabled={uploading}
          multiple={false}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Click or drag media file to this area to upload</p>
          <p className="ant-upload-hint">Support for PNG, JPG, PDF, DOCX (Max 25MB)</p>
        </Dragger>

        {existingAttachments.length > 0 && (
          <List
            size="small"
            bordered
            dataSource={existingAttachments}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button 
                    type="text" 
                    danger 
                    icon={<DeleteOutlined />} 
                    onClick={() => handleDelete(item.id)}
                  />
                ]}
              >
                <List.Item.Meta
                  avatar={<FileOutlined style={{ color: '#6366f1' }} />}
                  title={<a href={item.file_path} target="_blank" rel="noreferrer">{item.filename}</a>}
                  description={`${( (item.file_size || 0) / 1024 / 1024).toFixed(2)} MB • ${new Date(item.created_at).toLocaleDateString()}`}
                />
              </List.Item>
            )}
          />
        )}
      </Space>
    </div>
  );
};

export default FileUploader;
