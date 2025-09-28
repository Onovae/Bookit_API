# 🚀 BookIt API - Render Deployment Guide

## **Prerequisites**
1. GitHub account with your BookIt API repository
2. Render account 
3. Your code pushed to GitHub

## **Step-by-Step Deployment on Render**

### **1. Create PostgreSQL Database on Render**

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure database:
   - **Name**: `bookit-db`
   - **Database**: `bookit_db`
   - **User**: `bookit_user`
   - **Region**: Choose closest to your users
   - **Plan**: Free (for testing) or Paid (for production)
4. Click **"Create Database"**
5. **Save the connection details** - using the `External Database URL`

### **2. Deploy FastAPI Application**

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure the web service:
   - **Name**: `bookit-api`
   - **Region**: Same as your database
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

### **3. Environment Variables**

Add these environment variables in Render's web service settings:

```bash
# Database (use the External Database URL from step 1)
DATABASE_URL=postgresql://bookit_user:password@hostname:port/bookit_db

# JWT Configuration
SECRET_KEY=your-super-secret-32-character-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME=BookIt API
API_V1_STR=/api/v1

# CORS (replace with your frontend domain)
BACKEND_CORS_ORIGINS=["https://your-frontend-domain.com"]

# Admin User (for initial setup)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your-secure-admin-password
ADMIN_NAME=System Administrator

# Security (disable docs in production)
DOCS_URL=null
REDOC_URL=null

# Logging
LOG_LEVEL=INFO
```

### **4. Deploy and Run Migrations**

1. Click **"Create Web Service"**
2. Render will automatically build and deploy your app
3. Once deployed, run database migrations via Render Shell:
   ```bash
   python -m alembic upgrade head
   ```

### **5. Create Admin User**

Run your admin creation script:
```bash
python create_admin.py
```

### **6. Test Your Deployment**

Your API will be available at: `https://bookit-api.onrender.com`

Test endpoints:
- **Health Check**: `GET https://bookit-api.onrender.com/api/v1/health`
- **Register User**: `POST https://bookit-api.onrender.com/api/v1/auth/register`
- **Login**: `POST https://bookit-api.onrender.com/api/v1/auth/login`

## **Important Production Notes**

### **🔒 Security Checklist**
- ✅ Set strong `SECRET_KEY` (32+ characters)
- ✅ Use secure admin password
- ✅ Set `DEBUG=false`
- ✅ Configure proper CORS origins
- ✅ Disable API docs in production (`DOCS_URL=null`)

### **📊 Monitoring**
- Monitor logs in Render Dashboard
- Set up health checks
- Monitor database performance

### **💰 Cost Considerations**
- **Free Tier**: Good for testing/demos
  - Web Service sleeps after 15 minutes of inactivity
  - PostgreSQL: 1GB storage, 1 month retention
- **Paid Tier**: Recommended for production
  - Always-on services
  - Better database specs
  - Custom domains

## **Render vs Other Platforms**

**Render Advantages:**
- ✅ Zero configuration PostgreSQL
- ✅ Automatic HTTPS
- ✅ Git-based deployments
- ✅ Built-in monitoring
- ✅ Free tier available

**Perfect for your BookIt API!** 🎉

## **Troubleshooting**

### **Common Issues:**
1. **Build fails**: Check `requirements.txt` format
2. **Database connection**: Verify `DATABASE_URL` format
3. **Migration errors**: Run migrations manually via Render Shell
4. **CORS issues**: Check `BACKEND_CORS_ORIGINS` setting

### **Getting Help:**
- Render has excellent documentation
- Check deployment logs in dashboard
- Use Render Shell for debugging