# Contract Lifecycle Management Platform

Enterprise-grade Contract Lifecycle Management system built with FastAPI, PostgreSQL, and React.

## 🚀 Quick Start

### Prerequisites
- **PostgreSQL 16+** - [Download](https://www.postgresql.org/download/windows/)
- **Python 3.13+** - [Download](https://www.python.org/)
- **Node.js 20+** - [Download](https://nodejs.org/)

### One-Command Setup (Windows)
```bash
start-dev.bat
```

### Manual Setup

**1. Database Setup** (One-time)
```bash
# PostgreSQL CLI
psql -U postgres

CREATE USER clm_user WITH PASSWORD 'clm_password';
CREATE DATABASE clm_db OWNER clm_user;
GRANT ALL PRIVILEGES ON DATABASE clm_db TO clm_user;
\c clm_db
GRANT ALL PRIVILEGES ON SCHEMA public TO clm_user;
\q
```

**2. Backend Setup**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # venv/bin/activate on Linux/Mac
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

**3. Frontend Setup** (in new terminal)
```bash
cd frontend
npm install
npm run dev
```

## 📚 Database Setup

For detailed database setup SQL scripts, see **DATABASE_COMPLETE_SETUP.md**

## 🎯 Key Features

✅ **Contract Management** - Create, update, version, and track contracts
✅ **Clause Library** - Reusable clause templates with full-text search
✅ **Workflow Engine** - Multi-level approvals and approval routing
✅ **SLA Monitoring** - Track deadlines and renewal dates
✅ **Notifications** - Email alerts and webhook support
✅ **Audit Logging** - Complete compliance and activity tracking
✅ **User Authentication** - JWT-based with role-based access control

## 📊 Access Points

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/api/docs

## 🔐 Default Credentials

- **Email:** admin@clm.local
- **Password:** admin@123

⚠️ Change immediately in production!

## 🏗️ Architecture

- **Backend:** FastAPI with SQLAlchemy ORM
- **Database:** PostgreSQL with 9 tables
- **Frontend:** React with TypeScript and Redux
- **DevOps:** Docker, Docker Compose, Nginx

## 📦 Services Included

1. **Authentication Service** - JWT login, registration, RBAC
2. **Contract Service** - Full CRUD with versioning
3. **Clause Service** - Library management and search
4. **Workflow Service** - Multi-level approvals
5. **SLA Service** - Deadline and renewal tracking
6. **Notification Service** - Email and webhooks
7. **Audit Service** - Compliance logging

## 🔧 Technology Stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** React, TypeScript, Redux, Ant Design
- **DevOps:** Docker, Docker Compose, Nginx

## 📖 Documentation

Comprehensive documentation is provided:
- Complete API reference with examples
- Step-by-step deployment guide
- Database schema documentation
- Security best practices
- Production deployment checklist

## ✉️ Support

For questions or issues, refer to:
- API Docs: http://localhost:8000/api/docs
- Deployment Guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- API Reference: [API_REFERENCE.md](API_REFERENCE.md)

---

**Version:** 1.0.0  
**Status:** ✅ Production Ready
