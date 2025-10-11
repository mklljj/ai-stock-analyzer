from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import time
from functools import lru_cache
import json
import praw
from textblob import TextBlob
from newsapi import NewsApiClient
import finnhub
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# API Keys
API_KEY = os.getenv('API_KEY', 'my-secret-stock-api-key-2024')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', 'demo')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID', '')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET', '')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'stock_analyzer_bot/1.0')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')

# API Endpoints
ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

def calculate_sma(data, period):
    """Calculate Simple Moving Average"""
    return data.rolling(window=period).mean()

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    ema_fast = data.ewm(span=fast).mean()
    ema_slow = data.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calculate_rsi(data, period=14):
    """Calculate RSI indicator"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_alpha_vantage_symbol(stock_code, market_type):
    """Convert stock code to Alpha Vantage format"""
    if market_type == 'A-share':
        if stock_code.startswith('6'):
            return f"{stock_code}.SHH"
        else:
            return f"{stock_code}.SHZ"
    elif market_type == 'HK':
        return f"{stock_code}.HKG"
    else:
        return stock_code

@lru_cache(maxsize=100)
def fetch_stock_data_cached(stock_code, market_type, cache_key):
    """Cached version to avoid repeated API calls"""
    return fetch_stock_data(stock_code, market_type)

def fetch_stock_data(stock_code, market_type):
    """Fetch INTRADAY stock data from Alpha Vantage"""
    try:
        symbol = get_alpha_vantage_symbol(stock_code, market_type)
        print(f"Fetching INTRADAY data for symbol: {symbol}")
        
        interval = '5min'

        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': 'compact',
            'apikey': ALPHA_VANTAGE_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE, params=params, timeout=10)
        data = response.json()
        
        if 'Error Message' in data:
            return {'error': f'Invalid symbol: {stock_code}'}
        
        if 'Note' in data:
            return {'error': 'API rate limit reached. Wait 1 minute or check daily limit.'}
        
        json_key = f'Time Series ({interval})'
        if json_key not in data:
            return {'error': f"No '{interval}' intraday data available for this symbol."}
        
        time_series = data[json_key]
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        for col in ['Open', 'High', 'Low', 'Close']:
            df[col] = df[col].astype(float)
        df['Volume'] = df['Volume'].astype(int)
        
        if df.empty:
            return {'error': f'No data found for {stock_code}'}
        
        # Calculate indicators
        df['SMA_5'] = calculate_sma(df['Close'], 5)
        df['SMA_10'] = calculate_sma(df['Close'], 10)
        df['SMA_20'] = calculate_sma(df['Close'], 20)
        df['SMA_60'] = calculate_sma(df['Close'], 60)
        
        macd, signal, histogram = calculate_macd(df['Close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Histogram'] = histogram
        df['RSI'] = calculate_rsi(df['Close'])
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        price_change = latest['Close'] - prev['Close']
        price_change_pct = (price_change / prev['Close']) * 100
        
        if latest['Close'] > latest['SMA_5'] > latest['SMA_10'] > latest['SMA_20']:
            trend = "Strong Uptrend"
        elif latest['Close'] > latest['SMA_10']:
            trend = "Uptrend"
        elif latest['Close'] < latest['SMA_10']:
            trend = "Downtrend"
        else:
            trend = "Sideways"
        
        return {
            'stock_code': stock_code,
            'market_type': market_type,
            'ticker': symbol,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': round(latest['Close'], 2),
            'price_change': round(price_change, 2),
            'price_change_percent': round(price_change_pct, 2),
            'volume': int(latest['Volume']),
            'high': round(latest['High'], 2),
            'low': round(latest['Low'], 2),
            'open': round(latest['Open'], 2),
            'trend': trend,
            'technical_indicators': {
                'SMA_5': round(latest['SMA_5'], 2) if pd.notna(latest['SMA_5']) else None,
                'SMA_10': round(latest['SMA_10'], 2) if pd.notna(latest['SMA_10']) else None,
                'SMA_20': round(latest['SMA_20'], 2) if pd.notna(latest['SMA_20']) else None,
                'SMA_60': round(latest['SMA_60'], 2) if pd.notna(latest['SMA_60']) else None,
                'MACD': round(latest['MACD'], 4) if pd.notna(latest['MACD']) else None,
                'MACD_Signal': round(latest['MACD_Signal'], 4) if pd.notna(latest['MACD_Signal']) else None,
                'MACD_Histogram': round(latest['MACD_Histogram'], 4) if pd.notna(latest['MACD_Histogram']) else None,
                'RSI': round(latest['RSI'], 2) if pd.notna(latest['RSI']) else None
            },
            'support_resistance': {
                'support_1': round(latest['Low'], 2),
                'support_2': round(df['Low'].tail(10).min(), 2),
                'resistance_1': round(latest['High'], 2),
                'resistance_2': round(df['High'].tail(10).max(), 2)
            },
            'volume_analysis': {
                'current_volume': int(latest['Volume']),
                'avg_volume_10d': int(df['Volume'].tail(10).mean()),
                'volume_ratio': round(latest['Volume'] / df['Volume'].tail(10).mean(), 2) if df['Volume'].tail(10).mean() > 0 else 0
            }
        }
        
    except Exception as e:
        return {'error': str(e)}

def analyze_sentiment(text):
    """Analyze sentiment of text using TextBlob"""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        
        # Convert to -100 to 100 scale
        score = int(polarity * 100)
        
        if polarity > 0.1:
            label = "Positive"
        elif polarity < -0.1:
            label = "Negative"
        else:
            label = "Neutral"
            
        return score, label
    except:
        return 0, "Neutral"

def fetch_finnhub_sentiment(stock_code):
    """Fetch sentiment and news from Finnhub"""
    if not FINNHUB_API_KEY:
        return {
            'error': 'Finnhub API key not configured',
            'message': 'Get FREE key from https://finnhub.io/register'
        }
    
    try:
        print(f"📊 Fetching Finnhub data for {stock_code}...")
        
        finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
        
        # Get company news (last 7 days)
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        news = finnhub_client.company_news(stock_code, _from=from_date, to=to_date)
        
        if not news or len(news) == 0:
            print(f"⚠️ No Finnhub news found for {stock_code}")
            return {
                'source': 'finnhub',
                'news_count': 0,
                'sentiment_score': 0,
                'sentiment_label': 'Neutral',
                'news_items': [],
                'message': 'No recent news found'
            }
        
        # Analyze sentiment of news headlines and summaries
        sentiments = []
        news_items = []
        
        for article in news[:15]:  # Top 15 articles
            headline = article.get('headline', '')
            summary = article.get('summary', '')
            text = f"{headline}. {summary}"
            
            score, label = analyze_sentiment(text)
            sentiments.append(score)
            
            news_items.append({
                'headline': headline,
                'source': article.get('source', 'Unknown'),
                'url': article.get('url', ''),
                'datetime': datetime.fromtimestamp(article.get('datetime', 0)).strftime('%Y-%m-%d %H:%M'),
                'sentiment': label,
                'category': article.get('category', 'general')
            })
        
        # Calculate average sentiment
        avg_sentiment = int(np.mean(sentiments)) if sentiments else 0
        
        if avg_sentiment > 10:
            sentiment_label = "Positive"
        elif avg_sentiment < -10:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        
        # Try to get news sentiment score from Finnhub (if available)
        try:
            sentiment_data = finnhub_client.news_sentiment(stock_code)
            if sentiment_data and 'sentiment' in sentiment_data:
                # Finnhub provides scores, we can use them
                finnhub_score = sentiment_data['sentiment'].get('bullishPercent', 0) - sentiment_data['sentiment'].get('bearishPercent', 0)
                # Combine with our analysis
                avg_sentiment = int((avg_sentiment + finnhub_score) / 2)
        except:
            pass  # If news sentiment not available, use our calculated sentiment
        
        print(f"✅ Finnhub sentiment: {sentiment_label} ({avg_sentiment}/100) from {len(news_items)} articles")
        
        return {
            'source': 'finnhub',
            'news_count': len(news_items),
            'sentiment_score': avg_sentiment,
            'sentiment_label': sentiment_label,
            'news_items': news_items[:10],  # Return top 10
            'confidence': 'high' if len(news_items) >= 5 else 'medium'
        }
        
    except Exception as e:
        print(f"❌ Finnhub sentiment error: {str(e)}")
        return {'error': f'Finnhub sentiment error: {str(e)}'}

def fetch_news_sentiment(stock_code, company_name=None):
    """Fetch real news and analyze sentiment using NewsAPI"""
    if not NEWS_API_KEY:
        return {
            'error': 'NewsAPI key not configured',
            'message': 'Get FREE key from https://newsapi.org/register'
        }
    
    try:
        print(f"📰 Fetching news for {stock_code}...")
        
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        
        query = stock_code
        if company_name:
            query = f"{stock_code} OR {company_name}"
        
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        articles = newsapi.get_everything(
            q=query,
            from_param=from_date,
            language='en',
            sort_by='relevancy',
            page_size=20
        )
        
        if articles['status'] != 'ok' or articles['totalResults'] == 0:
            print(f"⚠️ No news found for {stock_code}")
            return {
                'source': 'news',
                'articles_count': 0,
                'sentiment_score': 0,
                'sentiment_label': 'Neutral',
                'headlines': [],
                'message': 'No recent news found'
            }
        
        sentiments = []
        headlines = []
        
        for article in articles['articles'][:15]:
            title = article.get('title', '')
            description = article.get('description', '')
            text = f"{title}. {description}"
            
            score, label = analyze_sentiment(text)
            sentiments.append(score)
            
            headlines.append({
                'title': title,
                'source': article.get('source', {}).get('name', 'Unknown'),
                'url': article.get('url', ''),
                'published': article.get('publishedAt', ''),
                'sentiment': label
            })
        
        avg_sentiment = int(np.mean(sentiments)) if sentiments else 0
        
        if avg_sentiment > 10:
            sentiment_label = "Positive"
        elif avg_sentiment < -10:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        
        print(f"✅ News sentiment: {sentiment_label} ({avg_sentiment}/100) from {len(headlines)} articles")
        
        return {
            'source': 'news',
            'articles_count': len(headlines),
            'sentiment_score': avg_sentiment,
            'sentiment_label': sentiment_label,
            'headlines': headlines[:10],
            'confidence': 'high' if len(headlines) >= 5 else 'medium'
        }
        
    except Exception as e:
        print(f"❌ News sentiment error: {str(e)}")
        return {'error': f'News sentiment error: {str(e)}'}

def fetch_reddit_sentiment(stock_code):
    """Fetch Reddit sentiment from r/wallstreetbets and r/stocks"""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return {
            'error': 'Reddit API credentials not configured',
            'message': 'Register app at https://www.reddit.com/prefs/apps'
        }
    
    try:
        print(f"🔥 Fetching Reddit sentiment for ${stock_code}...")
        
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        
        subreddits = ['wallstreetbets', 'stocks', 'investing', 'StockMarket']
        
        all_posts = []
        sentiments = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                for post in subreddit.search(stock_code, time_filter='week', limit=10):
                    title = post.title
                    text = f"{title}. {post.selftext[:200]}"
                    
                    score, label = analyze_sentiment(text)
                    sentiments.append(score)
                    
                    all_posts.append({
                        'title': title,
                        'subreddit': subreddit_name,
                        'score': post.score,
                        'comments': post.num_comments,
                        'url': f"https://reddit.com{post.permalink}",
                        'created': datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M'),
                        'sentiment': label
                    })
            except Exception as e:
                print(f"⚠️ Error fetching from r/{subreddit_name}: {str(e)}")
                continue
        
        if not sentiments:
            print(f"⚠️ No Reddit posts found for ${stock_code}")
            return {
                'source': 'reddit',
                'posts_count': 0,
                'sentiment_score': 0,
                'sentiment_label': 'Neutral',
                'top_posts': [],
                'message': f'No recent Reddit discussions found for ${stock_code}'
            }
        
        avg_sentiment = int(np.mean(sentiments))
        
        if avg_sentiment > 15:
            sentiment_label = "Positive"
        elif avg_sentiment < -15:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        
        all_posts.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"✅ Reddit sentiment: {sentiment_label} ({avg_sentiment}/100) from {len(all_posts)} posts")
        
        return {
            'source': 'reddit',
            'posts_count': len(all_posts),
            'sentiment_score': avg_sentiment,
            'sentiment_label': sentiment_label,
            'top_posts': all_posts[:10],
            'subreddits_searched': subreddits,
            'confidence': 'high' if len(all_posts) >= 5 else 'medium'
        }
        
    except Exception as e:
        print(f"❌ Reddit sentiment error: {str(e)}")
        return {'error': f'Reddit sentiment error: {str(e)}'}

def combine_sentiment_sources(finnhub_sentiment, news_sentiment, reddit_sentiment):
    """Combine Finnhub, news, and Reddit sentiment into unified analysis"""
    
    sources_data = []
    total_weight = 0
    weighted_score = 0
    
    # Finnhub sentiment (weight: 40%)
    if finnhub_sentiment and 'error' not in finnhub_sentiment and finnhub_sentiment.get('news_count', 0) > 0:
        weight = 0.4
        sources_data.append({
            'source': 'Finnhub (Premium)',
            'sentiment': finnhub_sentiment['sentiment_label'],
            'score': finnhub_sentiment['sentiment_score'],
            'count': finnhub_sentiment['news_count'],
            'weight': '40%'
        })
        weighted_score += finnhub_sentiment['sentiment_score'] * weight
        total_weight += weight
    
    # News sentiment (weight: 35%)
    if news_sentiment and 'error' not in news_sentiment and news_sentiment.get('articles_count', 0) > 0:
        weight = 0.35
        sources_data.append({
            'source': 'News Media',
            'sentiment': news_sentiment['sentiment_label'],
            'score': news_sentiment['sentiment_score'],
            'count': news_sentiment['articles_count'],
            'weight': '35%'
        })
        weighted_score += news_sentiment['sentiment_score'] * weight
        total_weight += weight
    
    # Reddit sentiment (weight: 25%)
    if reddit_sentiment and 'error' not in reddit_sentiment and reddit_sentiment.get('posts_count', 0) > 0:
        weight = 0.25
        sources_data.append({
            'source': 'Reddit Community',
            'sentiment': reddit_sentiment['sentiment_label'],
            'score': reddit_sentiment['sentiment_score'],
            'count': reddit_sentiment['posts_count'],
            'weight': '25%'
        })
        weighted_score += reddit_sentiment['sentiment_score'] * weight
        total_weight += weight
    
    if total_weight == 0:
        return {
            'combined_score': 0,
            'combined_label': 'Neutral',
            'confidence': 'low',
            'sources': sources_data,
            'message': 'Insufficient data from news and social media'
        }
    
    # Calculate combined score
    combined_score = int(weighted_score / total_weight)
    
    if combined_score > 15:
        combined_label = "Positive"
    elif combined_score < -15:
        combined_label = "Negative"
    else:
        combined_label = "Neutral"
    
    # Determine confidence
    if len(sources_data) >= 3:
        confidence = 'very high'
    elif len(sources_data) == 2:
        confidence = 'high'
    elif len(sources_data) == 1:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return {
        'combined_score': combined_score,
        'combined_label': combined_label,
        'confidence': confidence,
        'sources': sources_data,
        'finnhub_data': finnhub_sentiment if finnhub_sentiment and 'error' not in finnhub_sentiment else None,
        'news_data': news_sentiment if news_sentiment and 'error' not in news_sentiment else None,
        'reddit_data': reddit_sentiment if reddit_sentiment and 'error' not in reddit_sentiment else None
    }

def get_enhanced_analysis_with_real_sentiment(stock_data, sentiment_data):
    """Generate AI analysis combining technical + real sentiment data"""
    if not GEMINI_API_KEY:
        return {'error': 'Gemini API key not configured'}
    
    # Build sentiment section
    sentiment_section = ""
    if sentiment_data and 'combined_score' in sentiment_data:
        sources_text = "\n".join([
            f"  - {s['source']}: {s['sentiment']} ({s['score']}/100) - {s['count']} items - Weight: {s['weight']}"
            for s in sentiment_data.get('sources', [])
        ])
        
        sentiment_section = f"""

**REAL-TIME SENTIMENT ANALYSIS:**
Combined Sentiment: {sentiment_data['combined_label']} ({sentiment_data['combined_score']}/100)
Confidence: {sentiment_data['confidence'].upper()}

Sources:
{sources_text}

"""
        # Add Finnhub news if available
        if sentiment_data.get('finnhub_data') and sentiment_data['finnhub_data'].get('news_items'):
            news = sentiment_data['finnhub_data']['news_items'][:3]
            news_text = "\n".join([f"  • {n['headline']} ({n['source']}) - {n['sentiment']}" for n in news])
            sentiment_section += f"\nTop Finnhub News:\n{news_text}\n"
        
        # Add other news headlines if available
        if sentiment_data.get('news_data') and sentiment_data['news_data'].get('headlines'):
            headlines = sentiment_data['news_data']['headlines'][:3]
            headlines_text = "\n".join([f"  • {h['title']} ({h['source']})" for h in headlines])
            sentiment_section += f"\nTop News Headlines:\n{headlines_text}\n"
        
        # Add top Reddit posts if available
        if sentiment_data.get('reddit_data') and sentiment_data['reddit_data'].get('top_posts'):
            posts = sentiment_data['reddit_data']['top_posts'][:3]
            posts_text = "\n".join([f"  • r/{p['subreddit']}: {p['title']} ({p['score']} upvotes)" for p in posts])
            sentiment_section += f"\nTop Reddit Discussions:\n{posts_text}\n"
    
    prompt = f"""You are a professional stock analyst. Analyze this stock using technical indicators AND real-time sentiment from Finnhub, news, and social media.

**Stock Information:**
- Stock: {stock_data['stock_code']} ({stock_data['market_type']})
- Current Price: ${stock_data['current_price']}
- Price Change: {stock_data['price_change']} ({stock_data['price_change_percent']}%)
- Trend: {stock_data['trend']}

**Technical Indicators:**
- RSI: {stock_data['technical_indicators']['RSI']}
- MACD: {stock_data['technical_indicators']['MACD']}
- MACD Signal: {stock_data['technical_indicators']['MACD_Signal']}
- SMA(5): ${stock_data['technical_indicators']['SMA_5']}
- SMA(10): ${stock_data['technical_indicators']['SMA_10']}
- SMA(20): ${stock_data['technical_indicators']['SMA_20']}
- Volume Ratio: {stock_data['volume_analysis']['volume_ratio']}x

**Support & Resistance:**
- Support: ${stock_data['support_resistance']['support_1']} / ${stock_data['support_resistance']['support_2']}
- Resistance: ${stock_data['support_resistance']['resistance_1']} / ${stock_data['support_resistance']['resistance_2']}
{sentiment_section}

**PROVIDE COMPREHENSIVE ANALYSIS:**

1. **Market Position Summary** (Combine technical + real sentiment data from multiple sources)
2. **Technical Analysis** (RSI, MACD, Moving Averages interpretation)
3. **Multi-Source Sentiment Analysis** (What Finnhub, news, and social media sentiment tells us)
4. **Technical vs Sentiment Alignment** 
   - Do they agree or conflict?
   - Which signal is stronger?
   - What does divergence/convergence mean?
5. **Risk Assessment** (Low/Medium/High with specific reasons from both technical and sentiment)
6. **Price Targets** (Short-term and medium-term based on combined signals)
7. **Trading Strategy** 
   - Entry points considering both technical and sentiment
   - Stop-loss levels
   - Profit targets
8. **Confidence Level** (High/Medium/Low - explain why based on signal alignment and data sources)
9. **Action Plan** (Specific next steps for traders)

**Be specific with numbers. If technical and sentiment diverge, explain which to prioritize and why.**"""

    try:
        url = f"{GEMINI_API_BASE}/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'temperature': 0.3,
                'maxOutputTokens': 20480,
                'topK': 40,
                'topP': 0.95,
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            return {'error': f'Analysis API error: {response.status_code}'}
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            analysis = result['candidates'][0]['content']['parts'][0]['text']
            return {
                'analysis': analysis,
                'model': 'gemini-2.5-flash',
                'includes_real_sentiment': True
            }
        
        return {'error': 'Could not generate analysis'}
        
    except Exception as e:
        return {'error': f'Analysis error: {str(e)}'}

@app.route('/analyze_with_sentiment', methods=['POST'])
def analyze_stock_with_sentiment():
    """Complete stock analysis with REAL Finnhub, news and Reddit sentiment"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {API_KEY}":
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    stock_code = data.get('stock_code')
    market_type = data.get('market_type', 'US')
    include_sentiment = data.get('include_sentiment', True)
    
    if not stock_code:
        return jsonify({'error': 'Stock code is required'}), 400
    
    if ALPHA_VANTAGE_KEY == 'demo':
        return jsonify({'error': 'Alpha Vantage API key not configured'}), 400
    
    print(f"\n{'='*60}")
    print(f"🔍 Analyzing {stock_code} with MULTI-SOURCE SENTIMENT")
    print('='*60)
    
    # Fetch stock data
    cache_key = datetime.now().strftime('%Y-%m-%d-%H')
    time.sleep(1)
    
    stock_data = fetch_stock_data_cached(stock_code, market_type, cache_key)
    
    if 'error' in stock_data:
        return jsonify(stock_data), 400
    
    print(f"✅ Stock data fetched")
    print(f"   Price: ${stock_data['current_price']} ({stock_data['price_change_percent']:+.2f}%)")
    
    # Fetch REAL sentiment from multiple sources
    sentiment_data = None
    if include_sentiment:
        # Fetch Finnhub sentiment
        finnhub_sentiment = fetch_finnhub_sentiment(stock_code)
        time.sleep(1)
        
        # Fetch news sentiment
        news_sentiment = fetch_news_sentiment(stock_code)
        time.sleep(1)
        
        # Fetch Reddit sentiment
        reddit_sentiment = fetch_reddit_sentiment(stock_code)
        time.sleep(1)
        
        # Combine all sentiments
        sentiment_data = combine_sentiment_sources(finnhub_sentiment, news_sentiment, reddit_sentiment)
        
        print(f"✅ Multi-source sentiment analysis complete")
        print(f"   Combined: {sentiment_data.get('combined_label', 'N/A')} ({sentiment_data.get('combined_score', 0)}/100)")
        print(f"   Confidence: {sentiment_data.get('confidence', 'N/A').upper()}")
        print(f"   Sources: {len(sentiment_data.get('sources', []))}")
    
    # Get AI analysis with real sentiment
    print(f"🤖 Generating AI analysis with multi-source sentiment data...")
    ai_result = get_enhanced_analysis_with_real_sentiment(stock_data, sentiment_data)
    
    if 'error' in ai_result:
        return jsonify({
            'stock_data': stock_data,
            'sentiment_data': sentiment_data,
            'ai_analysis': None,
            'warning': ai_result['error']
        }), 200
    
    print(f"✅ Analysis complete")
    
    # Combine results
    sentiment_sources = []
    if sentiment_data:
        sentiment_sources = [s['source'] for s in sentiment_data.get('sources', [])]
    
    result = {
        'stock_data': stock_data,
        'sentiment_data': sentiment_data,
        'ai_analysis': ai_result['analysis'],
        'model_info': {
            'provider': 'Google Gemini',
            'model': 'gemini-2.5-flash',
            'includes_real_sentiment': True,
            'sentiment_sources': sentiment_sources,
            'free': True
        },
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(result), 200

@app.route('/analyze', methods=['POST'])
def analyze_stock():
    """Stock analysis WITHOUT sentiment (technical only)"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {API_KEY}":
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    stock_code = data.get('stock_code')
    market_type = data.get('market_type', 'US')
    
    if not stock_code:
        return jsonify({'error': 'Stock code is required'}), 400
    
    if ALPHA_VANTAGE_KEY == 'demo':
        return jsonify({'error': 'Alpha Vantage API key not configured'}), 400
    
    cache_key = datetime.now().strftime('%Y-%m-%d-%H')
    time.sleep(1)
    
    stock_data = fetch_stock_data_cached(stock_code, market_type, cache_key)
    
    if 'error' in stock_data:
        return jsonify(stock_data), 400
    
    # Simple technical analysis without sentiment
    result = {
        'stock_data': stock_data,
        'sentiment_data': None,
        'ai_analysis': "Technical analysis only. Enable sentiment analysis for comprehensive insights.",
        'model_info': {
            'provider': 'Technical Indicators',
            'model': 'SMA, RSI, MACD',
            'includes_real_sentiment': False
        },
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(result), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'alpha_vantage': ALPHA_VANTAGE_KEY != 'demo',
            'gemini_ai': bool(GEMINI_API_KEY),
            'finnhub': bool(FINNHUB_API_KEY),
            'news_api': bool(NEWS_API_KEY),
            'reddit_api': bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)
        },
        'free_tier': True
    }), 200

@app.route('/')
def home():
    """Home page"""
    has_av = ALPHA_VANTAGE_KEY != 'demo'
    has_gemini = bool(GEMINI_API_KEY)
    has_finnhub = bool(FINNHUB_API_KEY)
    has_news = bool(NEWS_API_KEY)
    has_reddit = bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)
    
    return f'''
    <h1>🤖 Stock Analysis with Multi-Source Sentiment</h1>
    
    <h2>✨ Status:</h2>
    <ul>
        <li>Alpha Vantage: {'✅ Configured' if has_av else '❌ Not Set'}</li>
        <li>Google Gemini: {'✅ Configured (FREE!)' if has_gemini else '❌ Not Set'}</li>
        <li>Finnhub: {'✅ Configured (FREE!)' if has_finnhub else '❌ Not Set'}</li>
        <li>NewsAPI: {'✅ Configured (FREE!)' if has_news else '❌ Not Set'}</li>
        <li>Reddit API: {'✅ Configured (FREE!)' if has_reddit else '❌ Not Set'}</li>
    </ul>
    
    <h2>🎯 Features:</h2>
    <ul>
        <li>📈 Real-time stock technical analysis</li>
        <li>📊 REAL Finnhub sentiment (premium news source)</li>
        <li>📰 REAL news sentiment from NewsAPI</li>
        <li>🔥 REAL Reddit sentiment from r/wallstreetbets, r/stocks, etc.</li>
        <li>🤖 AI-powered comprehensive analysis</li>
        <li>✅ 100% FREE APIs - No credit card!</li>
    </ul>
    
    <h2>📡 Endpoints:</h2>
    <ul>
        <li><strong>POST /analyze_with_sentiment</strong> - Full analysis with multi-source sentiment</li>
        <li><strong>POST /analyze</strong> - Technical analysis only</li>
        <li><strong>GET /health</strong> - Health check</li>
    </ul>
    
    <h2>🔧 Setup:</h2>
    <ol>
        <li>Alpha Vantage: <a href="https://www.alphavantage.co/support/#api-key" target="_blank">Get Key</a></li>
        <li>Google Gemini: <a href="https://ai.google.dev/" target="_blank">Get Key</a></li>
        <li>Finnhub: <a href="https://finnhub.io/register" target="_blank">Get Key</a></li>
        <li>NewsAPI: <a href="https://newsapi.org/register" target="_blank">Get Key</a></li>
        <li>Reddit API: <a href="https://www.reddit.com/prefs/apps" target="_blank">Create App</a></li>
    </ol>
    
    <h2>🔐 Environment Variables:</h2>
    <pre>
export ALPHA_VANTAGE_KEY=your_key
export GEMINI_API_KEY=your_key
export FINNHUB_API_KEY=your_key
export NEWS_API_KEY=your_key
export REDDIT_CLIENT_ID=your_id
export REDDIT_CLIENT_SECRET=your_secret
export REDDIT_USER_AGENT="stock_analyzer_bot/1.0"
    </pre>
    
    <h2>💎 Why Multiple Sources?</h2>
    <ul>
        <li><strong>Finnhub (40%)</strong>: Premium financial news, high reliability</li>
        <li><strong>NewsAPI (35%)</strong>: Broad news coverage, diverse sources</li>
        <li><strong>Reddit (25%)</strong>: Retail investor sentiment, trending stocks</li>
    </ul>
    
    <p><strong>🎉 All APIs are completely FREE!</strong></p>
    '''

@app.route('/chart_data', methods=['POST'])
def get_chart_data():
    """Get detailed chart data for stock"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {API_KEY}":
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    stock_code = data.get('stock_code')
    market_type = data.get('market_type', 'US')
    
    if not stock_code:
        return jsonify({'error': 'Stock code is required'}), 400
    
    if ALPHA_VANTAGE_KEY == 'demo':
        return jsonify({'error': 'Alpha Vantage API key not configured'}), 400
    
    try:
        symbol = get_alpha_vantage_symbol(stock_code, market_type)
        interval = '5min'
        
        print(f"📈 Fetching chart data for {symbol}...")
        
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': 'full',  # Get more data for chart
            'apikey': ALPHA_VANTAGE_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE, params=params, timeout=10)
        chart_response = response.json()
        
        json_key = f'Time Series ({interval})'
        if json_key not in chart_response:
            return jsonify({'error': 'No chart data available'}), 400
        
        time_series = chart_response[json_key]
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        for col in ['Open', 'High', 'Low', 'Close']:
            df[col] = df[col].astype(float)
        df['Volume'] = df['Volume'].astype(int)
        
        # Calculate moving averages
        df['SMA_5'] = calculate_sma(df['Close'], 5)
        df['SMA_20'] = calculate_sma(df['Close'], 20)
        
        # Prepare data for chart
        chart_data = {
            'timestamps': df.index.strftime('%Y-%m-%d %H:%M').tolist(),
            'prices': df['Close'].round(2).tolist(),
            'volumes': df['Volume'].tolist(),
            'sma5': df['SMA_5'].fillna(0).round(2).tolist(),
            'sma20': df['SMA_20'].fillna(0).round(2).tolist(),
            'highs': df['High'].round(2).tolist(),
            'lows': df['Low'].round(2).tolist()
        }
        
        print(f"✅ Chart data ready: {len(chart_data['timestamps'])} data points")
        
        return jsonify(chart_data), 200
        
    except Exception as e:
        print(f"❌ Chart data error: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print("🚀 Stock Analysis Server with MULTI-SOURCE Sentiment Starting...")
    print(f"📊 Server: http://localhost:8080")
    print(f"🔑 API Key: {API_KEY}")
    print(f"📡 Alpha Vantage: {'✅' if ALPHA_VANTAGE_KEY != 'demo' else '❌'}")
    print(f"🤖 Google Gemini: {'✅' if GEMINI_API_KEY else '❌'}")
    print(f"📊 Finnhub: {'✅' if FINNHUB_API_KEY else '❌'}")
    print(f"📰 NewsAPI: {'✅' if NEWS_API_KEY else '❌'}")
    print(f"🔥 Reddit API: {'✅' if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET else '❌'}")
    
    if not FINNHUB_API_KEY:
        print("\n⚠️  Finnhub API key not set!")
        print("   Get FREE key: https://finnhub.io/register")
        print("   Set: export FINNHUB_API_KEY=your_key")
    
    if not NEWS_API_KEY:
        print("\n⚠️  NewsAPI key not set!")
        print("   Get FREE key: https://newsapi.org/register")
        print("   Set: export NEWS_API_KEY=your_key")
    
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("\n⚠️  Reddit API not configured!")
        print("   Create app: https://www.reddit.com/prefs/apps")
        print("   Set: export REDDIT_CLIENT_ID=your_id")
        print("   Set: export REDDIT_CLIENT_SECRET=your_secret")
    
    print("\n" + "="*60)
    app.run(host='0.0.0.0', port=8080, debug=True)
