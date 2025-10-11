# 1. Make sure you're in your project directory
cd /path/to/your/stock-analyzer

# 2. Initialize git (if not already done)
git init

# 3. Add all files
git add .

# 4. Make your initial commit
git commit -m "Initial commit: AI Stock Analyzer with Multi-Source Sentiment & Charts

Features:
- Real-time stock price charts with Chart.js
- Multi-source sentiment analysis (Finnhub, NewsAPI, Reddit)
- Technical indicators (RSI, MACD, SMA)
- AI-powered analysis using Google Gemini
- Interactive web interface
- Support for US, HK, and A-Share markets
- 100% free APIs, no credit card required"

# 5. Go to GitHub.com and create a new repository
# - Repository name: ai-stock-analyzer (or your preferred name)
# - Description: AI-powered stock analyzer with real-time charts and multi-source sentiment analysis
# - Public or Private (your choice)
# - DON'T initialize with README (we already have one)

# 6. Link your local repo to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ai-stock-analyzer.git

# 7. Push to GitHub
git branch -M main
git push -u origin main
