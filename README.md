# 🤖 AI Stock Analyzer with Multi-Source Sentiment & Real-Time Charts

A comprehensive stock analysis tool that combines technical indicators, real-time price charts, and multi-source sentiment analysis from Finnhub, NewsAPI, and Reddit. Powered by Google Gemini AI for intelligent market insights.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## ✨ Features

### 📈 Real-Time Stock Analysis
- **Live Price Data**: Intraday (5-minute) stock data from Alpha Vantage
- **Interactive Charts**: Beautiful, responsive price charts with Chart.js
- **Multiple Timeframes**: View 1 hour, 3 hours, today, or all available data
- **Volume Analysis**: Visualize trading volume alongside price movements

### 📊 Technical Indicators
- **RSI** (Relative Strength Index)
- **MACD** (Moving Average Convergence Divergence)
- **SMA** (Simple Moving Averages: 5, 10, 20, 60 periods)
- **Support & Resistance Levels**
- **Volume Ratio Analysis**

### 📰 Multi-Source Sentiment Analysis
- **Finnhub** (40% weight): Premium financial news and company updates
- **NewsAPI** (35% weight): Broad news coverage from multiple sources
- **Reddit** (25% weight): Retail investor sentiment from r/wallstreetbets, r/stocks, etc.
- **Weighted Algorithm**: Intelligently combines all sources for overall sentiment

### 🤖 AI-Powered Insights
- **Google Gemini AI**: Comprehensive market analysis
- **Signal Alignment Detection**: Identifies when technical and sentiment signals agree/diverge
- **Trading Strategies**: Entry points, stop-loss levels, and profit targets
- **Risk Assessment**: Data-driven risk evaluation

### 🎯 Additional Features
- ✅ **100% FREE APIs**: All services use free tiers
- 🔄 **Real-Time Updates**: Live data from multiple sources
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- 🎨 **Modern UI**: Clean, professional interface
- 🔐 **Secure**: API key authentication and environment variables

## 🎬 Demo

### Main Interface
![Main Interface](screenshots/main-interface.png)

### Price Chart with Technical Indicators
![Price Chart](screenshots/price-chart.png)

### Multi-Source Sentiment Analysis
![Sentiment Analysis](screenshots/sentiment-analysis.png)

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- A modern web browser

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/ai-stock-analyzer.git
cd ai-stock-analyzer
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Get FREE API Keys** (takes ~10 minutes)

   - **Alpha Vantage** (Stock Data): [Get Key](https://www.alphavantage.co/support/#api-key)
   - **Google Gemini** (AI Analysis): [Get Key](https://ai.google.dev/)
   - **Finnhub** (Premium News): [Get Key](https://finnhub.io/register)
   - **NewsAPI** (News Sentiment): [Get Key](https://newsapi.org/register)
   - **Reddit API** (Social Sentiment): [Create App](https://www.reddit.com/prefs/apps)
     - Click "create another app"
     - Select type: "script"
     - Copy the `client_id` and `client_secret`

4. **Configure Environment Variables**

Create a `.env` file in the project root:

```bash
ALPHA_VANTAGE_KEY=your_alpha_vantage_key
GEMINI_API_KEY=your_gemini_api_key
FINNHUB_API_KEY=your_finnhub_key
NEWS_API_KEY=your_newsapi_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=stock_analyzer_bot/1.0
API_KEY=my-secret-stock-api-key-2024
```

Or use the provided template:
```bash
cp .env.example .env
# Then edit .env with your actual API keys
```

5. **Run the application**

```bash
python stock_server.py
```

6. **Open your browser**

Navigate to: `http://localhost:8080`

## 📖 Usage

### Web Interface

1. Enter a stock ticker (e.g., AAPL, TSLA, NVDA)
2. Select market type (US, HK, A-Share)
3. Check "Include Sentiment Analysis" for comprehensive analysis
4. Click "Analyze Stock"
5. Explore the interactive chart and multi-source insights

### Chart Controls

- **All Data**: View complete available data
- **Last 1 Hour**: Recent 5-minute intervals
- **Last 3 Hours**: Short-term trends
- **Today**: Current trading day activity

### API Endpoints

#### Analyze with Sentiment
```bash
curl -X POST http://localhost:8080/analyze_with_sentiment \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-secret-stock-api-key-2024" \
  -d '{"stock_code": "AAPL", "market_type": "US", "include_sentiment": true}'
```

#### Get Chart Data
```bash
curl -X POST http://localhost:8080/chart_data \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-secret-stock-api-key-2024" \
  -d '{"stock_code": "AAPL", "market_type": "US"}'
```

#### Technical Analysis Only
```bash
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-secret-stock-api-key-2024" \
  -d '{"stock_code": "AAPL", "market_type": "US"}'
```

#### Health Check
```bash
curl http://localhost:8080/health
```

## 🏗️ Project Structure

```
ai-stock-analyzer/
│
├── stock_server.py          # Flask backend server
├── index.html              # Web interface
├── script.js               # Frontend JavaScript (Chart.js integration)
├── style.css               # Styling
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore file
├── README.md              # This file
├── LICENSE                # MIT License
└── screenshots/           # Demo screenshots
    ├── main-interface.png
    ├── price-chart.png
    └── sentiment-analysis.png
```

## 🔧 Technical Details

### Architecture
- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript, Chart.js
- **APIs**: Alpha Vantage, Gemini AI, Finnhub, NewsAPI, Reddit
- **Data Processing**: Pandas, NumPy
- **Sentiment Analysis**: TextBlob

### Technical Indicators Calculation
- **SMA**: Rolling window averages (5, 10, 20, 60 periods)
- **RSI**: 14-period momentum oscillator
- **MACD**: 12, 26, 9 configuration (fast, slow, signal)
- **Volume Analysis**: Current vs 10-day average comparison

### Sentiment Analysis Algorithm
```
Combined Score = (Finnhub × 0.4) + (NewsAPI × 0.35) + (Reddit × 0.25)

Classification:
- Positive: Score > 15
- Negative: Score < -15
- Neutral: -15 ≤ Score ≤ 15
```

### AI Analysis
- **Model**: Google Gemini 2.5 Flash
- **Max Tokens**: 20,480
- **Temperature**: 0.3 (focused, consistent)
- **Includes**:
  - Market position summary
  - Technical indicator interpretation
  - Multi-source sentiment analysis
  - Signal alignment/divergence analysis
  - Risk assessment
  - Price targets (short & medium term)
  - Trading strategies
  - Confidence levels

## 📊 API Rate Limits

| Service | Free Tier Limit | Notes |
|---------|----------------|-------|
| Alpha Vantage | 25 requests/day | 500/day with free premium key |
| Google Gemini | 60 requests/min | 1,500 requests/day |
| Finnhub | 60 requests/min | 30 requests/sec |
| NewsAPI | 100 requests/day | 100 articles per request |
| Reddit API | 60 requests/min | More than sufficient |

## 🎨 Features Breakdown

### Real-Time Chart
- **Type**: Line chart with area fill
- **Data**: 5-minute intervals
- **Lines**: Price, SMA(5), SMA(20)
- **Bars**: Volume (secondary axis)
- **Interactive**: Hover tooltips, zoom controls
- **Responsive**: Adapts to screen size

### Sentiment Sources
1. **Finnhub**: Company news, earnings, products, regulations
2. **NewsAPI**: Broad media coverage, diverse sources
3. **Reddit**: r/wallstreetbets, r/stocks, r/investing, r/StockMarket

### Signal Alignment
- ✅ **ALIGNED**: Technical + Sentiment agree (High confidence)
- ⚠️ **DIVERGENCE**: Signals conflict (Caution advised)
- 📊 **MIXED**: Neutral or sideways movement

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide for Python
- Use meaningful variable names
- Add comments for complex logic
- Test thoroughly before submitting

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for **educational and informational purposes only**. It should not be considered financial advice. Always:
- Do your own research (DYOR)
- Consult with qualified financial advisors
- Never invest more than you can afford to lose
- Past performance does not guarantee future results

## 🙏 Acknowledgments

- [Alpha Vantage](https://www.alphavantage.co/) - Stock market data
- [Google Gemini](https://ai.google.dev/) - AI analysis
- [Finnhub](https://finnhub.io/) - Premium financial news
- [NewsAPI](https://newsapi.org/) - News articles
- [Reddit API](https://www.reddit.com/dev/api/) - Social media data
- [Chart.js](https://www.chartjs.org/) - Beautiful charts
- [TextBlob](https://textblob.readthedocs.io/) - Sentiment analysis

## 📧 Contact

Your Name - Bojian Zhou - neofastio@gmail.com

Project Link: [https://github.com/mklljj/ai-stock-analyzer](https://github.com/mklljj/ai-stock-analyzer)

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=YOUR_USERNAME/ai-stock-analyzer&type=Date)](https://star-history.com/#YOUR_USERNAME/ai-stock-analyzer&Date)

---

**Made with ❤️ and Python**

*Last Updated: October 2025*
