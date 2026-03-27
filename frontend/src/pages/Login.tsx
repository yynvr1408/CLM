import React, { useState, useEffect } from 'react';
import { Layout, Button, Form, Input, Card, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import './Login.css';

const { Content } = Layout;

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      navigate('/dashboard');
    }
  }, [navigate]);

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      await apiService.login(values.email, values.password);
      message.success('Login successful!');
      navigate('/dashboard');
    } catch (error: any) {
      message.error(error.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout className="login-layout">
      <Content className="login-content">
        <Card className="login-card">
          <div className="login-title-center">
            <h1>CLM Platform</h1>
            <p>Contract Lifecycle Management</p>
          </div>

          <Form
            form={form}
            onFinish={onFinish}
            layout="vertical"
            requiredMark="optional"
            size="large"
          >
            <Form.Item
              label="Email"
              name="email"
              rules={[
                { required: true, message: 'Please enter email' },
                { type: 'email', message: 'Invalid email' },
              ]}
            >
              <Input placeholder="your@email.com" />
            </Form.Item>

            <Form.Item
              label="Password"
              name="password"
              rules={[{ required: true, message: 'Please enter password' }]}
            >
              <Input.Password placeholder="Enter password" />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                block
                loading={loading}
                size="large"
              >
                Login
              </Button>
            </Form.Item>

            <div className="login-footer-center">
              <p>
                No account?{' '}
                <a onClick={() => navigate('/register')}>Register here</a>
              </p>
            </div>
          </Form>
        </Card>
      </Content>
    </Layout>
  );
};

export default Login;
