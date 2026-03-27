import React, { useState } from 'react';
import { Layout, Form, Input, Button, message, Card, Row, Col } from 'antd';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import './Register.css';

const { Content } = Layout;

const Register: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      await apiService.register(
        values.email,
        values.username,
        values.password,
        values.full_name
      );
      message.success('Registration successful! Please login.');
      navigate('/login');
    } catch (error: any) {
      message.error(error.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout className="register-layout">
      <Content className="register-content">
        <Row justify="center" style={{ width: '100%' }}>
          <Col xs={24} sm={20} md={14} lg={10} xl={8}>
            <Card className="register-card">
              <h1 className="register-title">Register</h1>
              <Form
                form={form}
                onFinish={onFinish}
                layout="vertical"
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
                  label="Username"
                  name="username"
                  rules={[{ required: true, message: 'Please enter username' }]}
                >
                  <Input placeholder="Username" />
                </Form.Item>

                <Form.Item
                  label="Full Name"
                  name="full_name"
                >
                  <Input placeholder="Full Name" />
                </Form.Item>

                <Form.Item
                  label="Password"
                  name="password"
                  rules={[
                    { required: true, message: 'Please enter password' },
                    { min: 8, message: 'Password must be at least 8 characters' },
                  ]}
                >
                  <Input.Password placeholder="Enter password" />
                </Form.Item>

                <Form.Item
                  label="Confirm Password"
                  name="confirm"
                  dependencies={['password']}
                  rules={[
                    { required: true, message: 'Please confirm password' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('password') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(new Error('Passwords do not match'));
                      },
                    }),
                  ]}
                >
                  <Input.Password placeholder="Confirm password" />
                </Form.Item>

                <Form.Item>
                  <Button type="primary" htmlType="submit" block loading={loading}>
                    Register
                  </Button>
                </Form.Item>

                <div className="register-footer-center">
                  <p>
                    Already have an account? <a onClick={() => navigate('/login')}>Login here</a>
                  </p>
                </div>
              </Form>
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default Register;
