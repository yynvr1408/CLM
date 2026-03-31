import React, { useState, useEffect } from 'react';
import { Table, Tag, Spin, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import {
  FileText, Clock, CheckCircle, Bell, Plus, ArrowRight,
  TrendingUp, BarChart3, PieChart as PieChartIcon
} from 'lucide-react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import apiService from '../services/api';
import { Contract, Renewal } from '../types';
import './Dashboard.css';

const COLORS = ['#6366f1', '#f59e0b', '#22c55e', '#ef4444', '#06b6d4'];

const AnimatedNumber = ({ value }: { value: number }) => {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest));
  React.useEffect(() => {
    const controls = animate(count, value, { duration: 1.2, ease: 'easeOut' });
    return controls.stop;
  }, [value, count]);
  return <motion.span>{rounded}</motion.span>;
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' as const } },
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [allContracts, setAllContracts] = useState<Contract[]>([]);
  const [renewals, setRenewals] = useState<Renewal[]>([]);
  const [stats, setStats] = useState({
    totalContracts: 0,
    draftContracts: 0,
    approvedContracts: 0,
    upcomingRenewals: 0,
    pendingApprovals: 0,
    totalValue: 0,
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [contractsData, allContractsData, renewalsData, statsData] = await Promise.all([
        apiService.getContracts(0, 5),
        apiService.getContracts(0, 100),
        apiService.getUpcomingRenewals(0, 5),
        apiService.getContractStats(),
      ]);

      setContracts(contractsData.items || []);
      setAllContracts(allContractsData.items || []);
      setRenewals(renewalsData.items || []);

      setStats({
        totalContracts: statsData.total_contracts,
        draftContracts: statsData.draft_contracts,
        approvedContracts: statsData.approved_contracts + statsData.executed_contracts,
        upcomingRenewals: statsData.upcoming_renewals,
        pendingApprovals: statsData.pending_approvals,
        totalValue: statsData.total_value,
      });
    } catch (error: any) {
      message.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Chart data
  const statusCounts = allContracts.reduce((acc: Record<string, number>, c) => {
    acc[c.status] = (acc[c.status] || 0) + 1;
    return acc;
  }, {});

  const pieData = Object.entries(statusCounts).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const typeCounts = allContracts.reduce((acc: Record<string, number>, c) => {
    acc[c.contract_type] = (acc[c.contract_type] || 0) + 1;
    return acc;
  }, {});

  const barData = Object.entries(typeCounts).map(([name, count]) => ({ name, count }));

  // Status bar for the activity widget
  const total = allContracts.length || 1;
  const statusBreakdown = [
    { label: 'Draft', value: Math.round((stats.draftContracts / total) * 100), color: 'bg-indigo-400' },
    { label: 'Approved', value: Math.round((stats.approvedContracts / total) * 100), color: 'bg-emerald-400' },
    { label: 'Other', value: Math.max(0, 100 - Math.round((stats.draftContracts / total) * 100) - Math.round((stats.approvedContracts / total) * 100)), color: 'bg-amber-300' },
  ];

  const contractColumns = [
    {
      title: 'Contract Number',
      dataIndex: 'contract_number',
      key: 'contract_number',
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: any = {
          draft: 'blue',
          submitted: 'orange',
          approved: 'green',
          rejected: 'red',
          executed: 'green',
        };
        return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: Contract) => (
        <button
          className="text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors bg-transparent border-none cursor-pointer"
          onClick={() => navigate(`/contracts/${record.id}`)}
        >
          View
        </button>
      ),
    },
  ];

  const renewalColumns = [
    {
      title: 'Contract',
      dataIndex: 'contract_id',
      key: 'contract_id',
      render: (id: number) => (
        <a onClick={() => navigate(`/contracts/${id}`)}>Contract #{id}</a>
      ),
    },
    {
      title: 'Renewal Date',
      dataIndex: 'renewal_date',
      key: 'renewal_date',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={status === 'pending' ? 'red' : 'green'}>{status}</Tag>,
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <motion.div
      className="dashboard-wrapper"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* ── Header ────────────────────────────────────────── */}
      <motion.div variants={itemVariants} className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#0f172a] m-0">Dashboard</h1>
          <p className="text-sm text-[#64748b] mt-1 mb-0">Welcome back. Here's your contract overview.</p>
        </div>
        <Button
          onClick={() => navigate('/contracts/new')}
          className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-5 py-2.5 text-sm font-medium shadow-md shadow-indigo-200 transition-all"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Contract
        </Button>
      </motion.div>

      {/* ── Stat Cards ────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
        {[
          { title: 'Total Contracts', value: stats.totalContracts, icon: FileText, gradient: 'from-indigo-500 to-indigo-600', bgLight: 'bg-indigo-50', iconColor: 'text-indigo-600' },
          { title: 'Pending Approvals', value: stats.pendingApprovals, icon: Clock, gradient: 'from-amber-500 to-amber-600', bgLight: 'bg-amber-50', iconColor: 'text-amber-600' },
          { title: 'Approved', value: stats.approvedContracts, icon: CheckCircle, gradient: 'from-emerald-500 to-emerald-600', bgLight: 'bg-emerald-50', iconColor: 'text-emerald-600' },
          { title: 'Upcoming Renewals', value: stats.upcomingRenewals, icon: Bell, gradient: 'from-rose-500 to-rose-600', bgLight: 'bg-rose-50', iconColor: 'text-rose-600' },
          { title: 'Drafts', value: stats.draftContracts, icon: Clock, gradient: 'from-slate-400 to-slate-500', bgLight: 'bg-slate-50', iconColor: 'text-slate-600' },
          { title: 'Total Value ($)', value: stats.totalValue, icon: TrendingUp, gradient: 'from-cyan-500 to-cyan-600', bgLight: 'bg-cyan-50', iconColor: 'text-cyan-600' },
        ].map((stat) => (
          <motion.div
            key={stat.title}
            variants={itemVariants}
            whileHover={{ scale: 1.03, y: -4 }}
            transition={{ type: 'spring', stiffness: 300, damping: 15 }}
          >
            <Card className="overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
              <div className={`h-1 bg-gradient-to-r ${stat.gradient}`} />
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-medium text-[#64748b] truncate mr-1">{stat.title}</p>
                  <div className={`p-2 rounded-lg ${stat.bgLight} shrink-0`}>
                    <stat.icon className={`w-5 h-5 ${stat.iconColor}`} />
                  </div>
                </div>
                <div className="text-2xl font-bold text-[#0f172a]">
                  {stat.title === 'Total Value ($)' ? (
                    <span>${stats.totalValue.toLocaleString()}</span>
                  ) : (
                    <AnimatedNumber value={stat.value} />
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* ── Activity + Quick Actions Row ──────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Contract Activity Widget */}
        <motion.div variants={itemVariants} whileHover={{ scale: 1.02 }} transition={{ type: 'spring', stiffness: 300, damping: 15 }} className="lg:col-span-2">
          <Card className="h-full border-0 shadow-md">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <TrendingUp className="w-5 h-5 text-indigo-600" />
                  Contract Activity
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="mb-1">
                <span className="text-4xl font-bold text-[#0f172a]">
                  <AnimatedNumber value={stats.totalContracts} />
                </span>
                <span className="ml-2 text-[#64748b]">total contracts</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-[#f1f5f9] flex overflow-hidden mt-4 mb-3">
                {statusBreakdown.map((stat, index) => (
                  <motion.div
                    key={index}
                    className={`h-full ${stat.color}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${stat.value}%` }}
                    transition={{ duration: 1, delay: 0.5 + index * 0.1 }}
                  />
                ))}
              </div>
              <div className="flex items-center gap-4 text-xs text-[#64748b]">
                {statusBreakdown.map((stat) => (
                  <div key={stat.label} className="flex items-center gap-1.5">
                    <span className={`w-2.5 h-2.5 rounded-full ${stat.color}`} />
                    <span>{stat.label} ({stat.value}%)</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Quick Actions */}
        <motion.div variants={itemVariants} whileHover={{ scale: 1.02 }} transition={{ type: 'spring', stiffness: 300, damping: 15 }}>
          <Card className="h-full border-0 shadow-md bg-gradient-to-br from-indigo-50 to-violet-50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-indigo-900">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { label: 'Create Contract', path: '/contracts/new', icon: FileText },
                { label: 'Clause Library', path: '/clauses', icon: BarChart3 },
                { label: 'View Approvals', path: '/approvals', icon: CheckCircle },
                { label: 'Audit Logs', path: '/audit', icon: PieChartIcon },
              ].map((action) => (
                <button
                  key={action.label}
                  onClick={() => navigate(action.path)}
                  className="w-full flex items-center justify-between p-3 rounded-lg bg-white/80 hover:bg-white hover:shadow-sm transition-all border border-indigo-100 cursor-pointer text-left"
                >
                  <div className="flex items-center gap-3">
                    <action.icon className="w-4 h-4 text-indigo-600" />
                    <span className="text-sm font-medium text-[#334155]">{action.label}</span>
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#94a3b8]" />
                </button>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* ── Charts Row ────────────────────────────────────── */}
      {allContracts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <motion.div variants={itemVariants}>
            <Card className="border-0 shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <PieChartIcon className="w-5 h-5 text-indigo-600" />
                  Contracts by Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {pieData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                      }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={itemVariants}>
            <Card className="border-0 shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <BarChart3 className="w-5 h-5 text-indigo-600" />
                  Contracts by Type
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={barData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                      }}
                    />
                    <Bar dataKey="count" fill="#6366f1" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      {/* ── Tables Row ────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <Card className="border-0 shadow-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Recent Contracts</CardTitle>
                <button
                  onClick={() => navigate('/contracts')}
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-800 bg-transparent border-none cursor-pointer flex items-center gap-1 transition-colors"
                >
                  View All <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <Table
                dataSource={contracts}
                columns={contractColumns}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="border-0 shadow-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Upcoming Renewals</CardTitle>
                <button
                  onClick={() => navigate('/renewals')}
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-800 bg-transparent border-none cursor-pointer flex items-center gap-1 transition-colors"
                >
                  View All <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <Table
                dataSource={renewals}
                columns={renewalColumns}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* ── CTA Banner ────────────────────────────────────── */}
      <motion.div variants={itemVariants} whileHover={{ scale: 1.01 }} transition={{ type: 'spring', stiffness: 300, damping: 15 }}>
        <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 shadow-lg shadow-indigo-200">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-full bg-white/20">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-white font-medium text-sm m-0">Streamline your contract workflow</p>
              <p className="text-indigo-200 text-xs mt-0.5 m-0">Create, approve, and track contracts in one place</p>
            </div>
          </div>
          <Button
            onClick={() => navigate('/contracts/new')}
            className="bg-white text-indigo-700 hover:bg-indigo-50 rounded-lg px-5 py-2.5 text-sm font-semibold shadow-none border-none"
          >
            Get Started
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Dashboard;
