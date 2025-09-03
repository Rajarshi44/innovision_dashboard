# 🚀 Deployment Guide for Event Analytics Dashboard

## Option 1: Streamlit Cloud (Recommended - FREE)

### Step 1: Prepare Your Repository
1. Create a GitHub account at https://github.com
2. Create a new repository called "event-analytics-dashboard"
3. Upload these files to your repository:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `.streamlit/config.toml`
   - `Supabase Snippet Event Analytic.xlsx`

### Step 2: Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository: `your-username/event-analytics-dashboard`
5. Set main file path: `app.py`
6. Click "Deploy!"

### Step 3: Your App is Live! 🎉
- Your app will be available at: `https://your-username-event-analytics-dashboard-app-xxxxx.streamlit.app`
- It auto-updates when you push changes to GitHub

---

## Option 2: Heroku (Scalable)

### Prerequisites
- Heroku account (free tier available)
- Git installed on your computer

### Step 1: Create Heroku Files

Create `Procfile` (no extension):
```
web: sh setup.sh && streamlit run app.py
```

Create `setup.sh`:
```bash
mkdir -p ~/.streamlit/
echo "\
[general]\n\
email = \"your-email@domain.com\"\n\
" > ~/.streamlit/credentials.toml
echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml
```

### Step 2: Deploy to Heroku
```bash
# Install Heroku CLI first
git init
git add .
git commit -m "Initial commit"
heroku create your-app-name
git push heroku main
```

---

## Option 3: Render (Free & Easy)

### Step 1: Connect Repository
1. Go to https://render.com
2. Sign up and connect your GitHub account
3. Click "New Web Service"
4. Select your repository

### Step 2: Configure Deployment
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

---

## Option 4: Railway (Modern Platform)

### Step 1: Deploy on Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "Deploy from GitHub repo"
4. Select your repository

### Step 2: Configure
Railway auto-detects Streamlit apps and configures everything automatically!

---

## Option 5: Docker Deployment

### Create Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Deploy with Docker:
```bash
docker build -t event-analytics .
docker run -p 8501:8501 event-analytics
```

---

## 🎯 Quick Start (Streamlit Cloud - 5 minutes)

1. **Create GitHub repo** and upload your files
2. **Go to share.streamlit.io** 
3. **Connect your repo**
4. **Click Deploy**
5. **Done!** Your app is live

## 📋 Pre-Deployment Checklist

- ✅ `requirements.txt` with all dependencies
- ✅ `app.py` works locally without errors
- ✅ Excel file is included in repository
- ✅ No hardcoded file paths
- ✅ README.md for documentation
- ✅ .streamlit/config.toml for configuration

## 🔧 Troubleshooting

### Common Issues:
1. **Module not found:** Add missing packages to `requirements.txt`
2. **File not found:** Ensure Excel file is in repository
3. **Memory issues:** Use smaller datasets or upgrade to paid tier

### Performance Tips:
- Use `@st.cache_data` for expensive operations
- Optimize data loading with `@st.cache_resource`
- Minimize large file uploads

## 🌐 Custom Domain (Optional)

For Streamlit Cloud:
1. Get a custom domain
2. Add CNAME record pointing to your Streamlit app
3. Contact Streamlit support for SSL setup

---

## 💡 Best Practices

1. **Version Control:** Always use Git for tracking changes
2. **Environment Variables:** Use secrets for sensitive data
3. **Error Handling:** Add try-catch blocks for robust apps
4. **User Experience:** Add loading spinners and progress bars
5. **Documentation:** Keep README.md updated

## 🚀 Go Live Now!

The fastest way is **Streamlit Cloud** - it's free, easy, and perfect for data science apps!

1. Upload to GitHub ➜ 2. Connect to Streamlit Cloud ➜ 3. Deploy ➜ 4. Share your URL! 🎉
