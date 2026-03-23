# COMPLETE PROJECT SETUP - DO THIS IN ORDER

## ✅ STEP-BY-STEP INSTRUCTIONS TO GET EVERYTHING WORKING

### STEP 1: VERIFY POSTGRESQL IS RUNNING
1. Open PostgreSQL pgAdmin (comes with PostgreSQL installation)
2. Log in with your PostgreSQL credentials
3. Check that these exist:
   - User: `clm_user` with password `clm_password`
   - Database: `clm_db` owned by `clm_user`

**If not created yet, run in pgAdmin Query Tool:**
```sql
-- Create user
CREATE USER clm_user WITH PASSWORD 'clm_password';

-- Create database
CREATE DATABASE clm_db OWNER clm_user;

-- Grant privileges
\c clm_db
GRANT ALL PRIVILEGES ON SCHEMA public TO clm_user;
```

---

### STEP 2: VERIFY PYTHON DEPENDENCIES
Open PowerShell and run:
```powershell
cd 'c:\Users\Nandhi vardhan reddy\Desktop\CLM\backend'
venv\Scripts\activate
pip list | findstr fastapi
```

You should see output showing installed packages. If you get errors, install again:
```powershell
pip install -r requirements.txt --force-reinstall
```

---

### STEP 3: START BACKEND SERVER
Open PowerShell **Terminal 1**:
```powershell
cd 'c:\Users\Nandhi vardhan reddy\Desktop\CLM\backend'
venv\Scripts\activate
python -m uvicorn main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

✅ **Test:** Open http://localhost:8000/health in browser → should show `{"status":"ok","service":"CLM Platform"}`

---

###STEP 4: START FRONTEND SERVER
Open PowerShell **Terminal 2** (keep backend running):
```powershell
cd 'c:\Users\Nandhi vardhan reddy\Desktop\CLM\frontend'
npm run dev
```

**Expected Output:**
```
  VITE v7.3.1  ready in 500 ms
  ➜  Local:   http://localhost:5173/
```

✅ **Test:** Open http://localhost:5173 in browser → Login page should load

---

### STEP 5: CREATE TEST USER & LOGIN
In pgAdmin **Query Tool** connected to `clm_db`, run:
```sql
-- Create default role
INSERT INTO roles (name, description, permissions) VALUES
('user', 'Standard user', '{"read_contracts": true}');

-- Check the role ID (should be 1)
SELECT id FROM roles WHERE name = 'user';
```

**Then register in the frontend:**
1. Go to http://localhost:5173
2. Click "Register here"
3. Fill in:
   - Email: `test@example.com`
   - Password: `Test@123456`
   - Username: `testuser`
   - Full Name: `Test User`
4. Click Register
5. Login with same credentials

---

## 🔍 VERIFY EVERYTHING WORKS

### Backend Health Checks:
- Health: http://localhost:8000/health
- API Docs: http://localhost:8000/api/docs
- Swagger UI should list these endpoints:
  - POST /api/v1/auth/register
  - POST /api/v1/auth/login
  - GET /api/v1/auth/me

### Frontend Health Checks:
- Login loads: http://localhost:5173
- Can register new account
- Can login successfully
- Dashboard loads after login

---

## 🚨 TROUBLESHOOTING

### Backend won't start
**Error: `ModuleNotFoundError`**
```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt --force-reinstall
```

**Error: `psycopg2` or database connection error**
1. Check PostgreSQL is running
2. Check user `clm_user` exists with password `clm_password`
3. Check database `clm_db` exists

### Frontend won't load
**Error: `Module not found` or `npm ERR`**
```powershell
cd frontend
npm install --force
npm run dev
```

**Error: Can't connect to backend**
1. Check backend is running on port 8000
2. Check http://localhost:8000/health returns `{"status":"ok"}`
3. Open browser DevTools → Network tab → check API calls

### Login fails
**Error: `Invalid email or password`**
1. Make sure you registered first (click "Register here")
2. Check email matches exactly (test@example.com)
3. Check PostgreSQL roles table has default "user" role

---

## 📝 SUMMARY OF RUNNING SERVERS

When everything is working, you should have:

| Service | URL | Port | Status |
|---------|-----|------|--------|
| Frontend | http://localhost:5173 | 5173 | ✅ Running (Terminal 2) |
| Backend | http://localhost:8000 | 8000 | ✅ Running (Terminal 1) |
| PostgreSQL | localhost | 5432 | ✅ Running (PostgreSQL Service) |
| Database | clm_db | N/A | ✅ Connected |

---

## ✨ DONE!

You now have a fully working CLM Platform with:
- ✅ React frontend (Vite) on port 5173
- ✅ FastAPI backend on port 8000
- ✅ PostgreSQL database
- ✅ User authentication (JWT)
- ✅ Redux state management
- ✅ API integration

**Next Steps:**
- Create contracts
- Add clauses
- Set approvals
- Track renewals
- View audits
