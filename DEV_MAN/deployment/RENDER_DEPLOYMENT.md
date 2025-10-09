# 🚀 Render Deployment Guide

Deploy PeteRental VAPI to Render in minutes!

## 📋 **Prerequisites**

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Push your code to GitHub
3. **OpenRouter API Key**: Get your key from [openrouter.ai](https://openrouter.ai)

## 🚀 **Deployment Steps**

### **Step 1: Push to GitHub**

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### **Step 2: Connect to Render**

1. **Go to [render.com](https://render.com)**
2. **Click "New +" → "Blueprint"**
3. **Connect your GitHub repository**
4. **Select the repository with PeteRental VAPI**

### **Step 3: Configure Environment**

1. **Set Environment Variables:**

   - `OPENROUTER_API_KEY`: Your OpenRouter API key
   - `PORT`: 8000 (Render sets this automatically)

2. **Build Settings:**
   - **Dockerfile**: Render will use your `./Dockerfile`
   - **Build Context**: Current directory (`.`)
   - **No manual commands needed** - Docker handles everything

### **Step 4: Deploy**

1. **Click "Create New Web Service"**
2. **Wait for build to complete** (5-10 minutes)
3. **Your app will be live at**: `https://your-app-name.onrender.com`

## 🔧 **Render-Specific Configuration**

### **🐳 Docker-Based Deployment Benefits**

Render will use your `Dockerfile` to build the container:

- ✅ **Consistent Environment**: Same as your local development
- ✅ **Playwright Ready**: All browser dependencies included
- ✅ **uv Management**: Fast dependency resolution
- ✅ **Production Optimized**: Multi-stage build for efficiency
- ✅ **Faster Deploys**: No need to reinstall dependencies

### **render.yaml (Blueprint)**

The `render.yaml` file in your repo automatically configures:

- ✅ **Docker-based deployment** using your Dockerfile
- ✅ Starter plan ($7/month)
- ✅ Auto-deploy on git push
- ✅ Health checks at `/health`
- ✅ Environment variable setup

### **Health Check Endpoint**

Render will automatically check `/health` to ensure your app is running.

## 🌐 **Production URLs**

Once deployed, your VAPI webhook will be available at:

```
https://your-app-name.onrender.com/vapi/webhook
```

## 📊 **Monitoring**

- **Logs**: View real-time logs in Render dashboard
- **Metrics**: Monitor CPU, memory, and response times
- **Deployments**: Automatic deployments on every git push

## 💰 **Pricing**

- **Starter Plan**: $7/month (perfect for development/testing)
- **Standard Plan**: $25/month (for production use)
- **Pro Plan**: $100/month (high traffic applications)

## 🔒 **Security**

- **HTTPS**: Automatically enabled
- **Environment Variables**: Securely stored
- **No Public Access**: Only accessible via your domain

## 🚨 **Troubleshooting**

### **Build Fails**

- Check logs for dependency issues
- Ensure `pyproject.toml` is valid
- Verify Python version compatibility

### **App Won't Start**

- Check environment variables
- Verify `OPENROUTER_API_KEY` is set
- Check health check endpoint

### **Playwright Issues**

- Ensure `playwright install chromium` runs in build
- Check if Chrome dependencies are installed

## 🎯 **Next Steps**

1. **Deploy to Render** using the steps above
2. **Test your VAPI webhook** with the new URL
3. **Update VAPI** with the new webhook endpoint
4. **Monitor performance** in Render dashboard

**Your PeteRental VAPI will be production-ready in minutes!** 🎉
