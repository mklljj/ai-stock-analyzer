let priceChart = null;
let fullChartData = null;

document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const stockCodeInput = document.getElementById('stockCode');
    const marketTypeSelect = document.getElementById('marketType');
    const includeSentimentCheckbox = document.getElementById('includeSentiment');
    const resultsDiv = document.getElementById('results');
    const loader = document.getElementById('loader');
    const errorDisplay = document.getElementById('errorDisplay');
    const sentimentSection = document.getElementById('sentimentSection');

    analyzeBtn.addEventListener('click', analyzeStock);
    
    stockCodeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            analyzeStock();
        }
    });

    // Chart period buttons
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            const period = e.target.dataset.period;
            updateChartPeriod(period);
        });
    });

    async function analyzeStock() {
        const stockCode = stockCodeInput.value.trim().toUpperCase();
        const marketType = marketTypeSelect.value;
        const includeSentiment = includeSentimentCheckbox.checked;

        if (!stockCode) {
            showError('Please enter a stock code.');
            return;
        }
        
        loader.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
        errorDisplay.classList.add('hidden');
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';

        try {
            const endpoint = includeSentiment 
                ? 'http://localhost:8080/analyze_with_sentiment'
                : 'http://localhost:8080/analyze';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer my-secret-stock-api-key-2024'
                },
                body: JSON.stringify({
                    stock_code: stockCode,
                    market_type: marketType,
                    include_sentiment: includeSentiment
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            
            // Fetch chart data
            await fetchChartData(stockCode, marketType);
            
            displayResults(data, includeSentiment);

        } catch (error) {
            showError(error.message);
        } finally {
            loader.classList.add('hidden');
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Stock';
        }
    }

    async function fetchChartData(stockCode, marketType) {
        try {
            const response = await fetch('http://localhost:8080/chart_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer my-secret-stock-api-key-2024'
                },
                body: JSON.stringify({
                    stock_code: stockCode,
                    market_type: marketType
                })
            });

            if (response.ok) {
                fullChartData = await response.json();
                createChart(fullChartData);
            } else {
                console.warn('Chart data not available');
            }
        } catch (error) {
            console.error('Error fetching chart data:', error);
        }
    }

    function createChart(chartData) {
        const ctx = document.getElementById('priceChart');
        
        // Destroy existing chart
        if (priceChart) {
            priceChart.destroy();
        }

        // Create gradient for price line
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(102, 126, 234, 0.3)');
        gradient.addColorStop(1, 'rgba(102, 126, 234, 0.01)');

        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.timestamps,
                datasets: [
                    {
                        label: 'Price',
                        data: chartData.prices,
                        borderColor: '#667eea',
                        backgroundColor: gradient,
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        yAxisID: 'y'
                    },
                    {
                        label: 'SMA(5)',
                        data: chartData.sma5,
                        borderColor: '#ffc107',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 0,
                        borderDash: [5, 5],
                        yAxisID: 'y'
                    },
                    {
                        label: 'SMA(20)',
                        data: chartData.sma20,
                        borderColor: '#28a745',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 0,
                        borderDash: [5, 5],
                        yAxisID: 'y'
                    },
                    {
                        label: 'Volume',
                        data: chartData.volumes,
                        type: 'bar',
                        backgroundColor: 'rgba(102, 126, 234, 0.3)',
                        borderColor: 'rgba(102, 126, 234, 0.5)',
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.dataset.yAxisID === 'y1') {
                                    label += new Intl.NumberFormat().format(context.parsed.y);
                                } else {
                                    label += '$' + context.parsed.y.toFixed(2);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10,
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            },
                            font: {
                                size: 11
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        ticks: {
                            callback: function(value) {
                                return new Intl.NumberFormat('en-US', {
                                    notation: 'compact',
                                    compactDisplay: 'short'
                                }).format(value);
                            },
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });
    }

    function updateChartPeriod(period) {
        if (!fullChartData || !priceChart) return;

        const now = new Date();
        let startIndex = 0;

        switch(period) {
            case '1h':
                // Last 12 data points (1 hour at 5-min intervals)
                startIndex = Math.max(0, fullChartData.timestamps.length - 12);
                break;
            case '3h':
                // Last 36 data points (3 hours)
                startIndex = Math.max(0, fullChartData.timestamps.length - 36);
                break;
            case 'today':
                // Find start of current day
                const todayStr = now.toISOString().split('T')[0];
                startIndex = fullChartData.timestamps.findIndex(ts => ts.startsWith(todayStr));
                if (startIndex === -1) startIndex = 0;
                break;
            case 'all':
            default:
                startIndex = 0;
                break;
        }

        // Update chart data
        priceChart.data.labels = fullChartData.timestamps.slice(startIndex);
        priceChart.data.datasets[0].data = fullChartData.prices.slice(startIndex);
        priceChart.data.datasets[1].data = fullChartData.sma5.slice(startIndex);
        priceChart.data.datasets[2].data = fullChartData.sma20.slice(startIndex);
        priceChart.data.datasets[3].data = fullChartData.volumes.slice(startIndex);
        
        priceChart.update('none'); // Update without animation
    }

    function displayResults(data, includeSentiment) {
        if (data.warning) {
            showWarning(data.warning);
        }

        const stockData = data.stock_data;

        // Update stock information
        document.getElementById('ticker').textContent = stockData.ticker;
        document.getElementById('currentPrice').textContent = `$${stockData.current_price.toFixed(2)}`;
        document.getElementById('rsi').textContent = stockData.technical_indicators.RSI 
            ? stockData.technical_indicators.RSI.toFixed(2) 
            : 'N/A';
        
        const volumeRatio = stockData.volume_analysis.volume_ratio;
        document.getElementById('volume').textContent = `${volumeRatio.toFixed(2)}x`;
        
        // Price change with color
        const priceChangeSpan = document.getElementById('priceChange');
        const change = stockData.price_change;
        const percentChange = stockData.price_change_percent;
        priceChangeSpan.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${percentChange.toFixed(2)}%)`;
        priceChangeSpan.className = `value ${change >= 0 ? 'positive' : 'negative'}`;

        // Trend with color-coded badge
        const trendSpan = document.getElementById('trend');
        trendSpan.textContent = stockData.trend;
        trendSpan.className = 'value trend-badge ' + getTrendClass(stockData.trend);

        // Display sentiment if included
        if (includeSentiment && data.sentiment_data) {
            displaySentiment(data.sentiment_data, stockData);
            sentimentSection.classList.remove('hidden');
            
            document.getElementById('analysisType').textContent = 'Technical + Multi-Source Sentiment';
            document.getElementById('analysisTypeBadge').classList.add('enhanced');
        } else {
            sentimentSection.classList.add('hidden');
            document.getElementById('analysisType').textContent = 'Technical Analysis Only';
            document.getElementById('analysisTypeBadge').classList.remove('enhanced');
        }

        // AI Analysis
        document.getElementById('aiAnalysis').textContent = data.ai_analysis || "AI analysis was not available.";
        
        // Model info
        if (data.model_info) {
            const provider = data.model_info.includes_real_sentiment 
                ? `${data.model_info.provider} + Multi-Source Sentiment`
                : data.model_info.provider;
            
            document.getElementById('modelProvider').textContent = `Provider: ${provider}`;
            document.getElementById('modelName').textContent = `Model: ${data.model_info.model || 'gemini-2.5-flash'}`;
            
            if (data.model_info.sentiment_sources && data.model_info.sentiment_sources.length > 0) {
                document.getElementById('tokensUsed').textContent = 
                    `Sources: ${data.model_info.sentiment_sources.join(', ')}`;
            }
        }
        
        resultsDiv.classList.remove('hidden');
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function displaySentiment(sentimentData, stockData) {
        const sentimentLabel = sentimentData.combined_label || sentimentData.sentiment_label || 'Neutral';
        const sentimentScore = sentimentData.combined_score !== undefined 
            ? sentimentData.combined_score 
            : (sentimentData.sentiment_score || 0);
        
        document.getElementById('sentimentLabel').textContent = sentimentLabel;
        document.getElementById('sentimentLabel').className = 'sentiment-value ' + getSentimentClass(sentimentLabel);
        
        document.getElementById('sentimentScore').textContent = `Score: ${sentimentScore}/100`;
        
        const barPercentage = ((sentimentScore + 100) / 2);
        const sentimentBar = document.getElementById('sentimentBar');
        sentimentBar.style.width = `${barPercentage}%`;
        sentimentBar.className = 'sentiment-bar-fill ' + getSentimentClass(sentimentLabel);
        
        let sentimentText = '';
        
        if (sentimentData.confidence) {
            sentimentText += `Confidence: ${sentimentData.confidence.toUpperCase()}\n\n`;
        }
        
        if (sentimentData.sources && sentimentData.sources.length > 0) {
            sentimentText += '📊 SENTIMENT SOURCES:\n';
            sentimentData.sources.forEach(source => {
                sentimentText += `\n${source.source}: ${source.sentiment} (${source.score}/100)\n`;
                sentimentText += `  • ${source.count} items analyzed\n`;
                sentimentText += `  • Weight: ${source.weight}\n`;
            });
            sentimentText += '\n';
        }
        
        if (sentimentData.finnhub_data && sentimentData.finnhub_data.news_items) {
            sentimentText += '📊 FINNHUB PREMIUM NEWS:\n\n';
            sentimentData.finnhub_data.news_items.slice(0, 5).forEach((item, idx) => {
                sentimentText += `${idx + 1}. ${item.headline}\n`;
                sentimentText += `   Source: ${item.source} | Sentiment: ${item.sentiment}\n`;
                sentimentText += `   Category: ${item.category} | Time: ${item.datetime}\n\n`;
            });
        }
        
        if (sentimentData.news_data && sentimentData.news_data.headlines) {
            sentimentText += '📰 TOP NEWS HEADLINES:\n\n';
            sentimentData.news_data.headlines.slice(0, 5).forEach((headline, idx) => {
                sentimentText += `${idx + 1}. ${headline.title}\n`;
                sentimentText += `   Source: ${headline.source} | Sentiment: ${headline.sentiment}\n\n`;
            });
        }
        
        if (sentimentData.reddit_data && sentimentData.reddit_data.top_posts) {
            sentimentText += '🔥 TOP REDDIT DISCUSSIONS:\n\n';
            sentimentData.reddit_data.top_posts.slice(0, 5).forEach((post, idx) => {
                sentimentText += `${idx + 1}. ${post.title}\n`;
                sentimentText += `   r/${post.subreddit} | ${post.score} upvotes | ${post.comments} comments\n`;
                sentimentText += `   Sentiment: ${post.sentiment}\n\n`;
            });
        }
        
        if (sentimentData.message) {
            sentimentText += `\n${sentimentData.message}\n`;
        }
        
        document.getElementById('sentimentAnalysis').textContent = 
            sentimentText || 'No detailed sentiment analysis available.';
        
        displayAlignment(sentimentLabel, stockData.trend);
    }

    function displayAlignment(sentimentLabel, technicalTrend) {
        const alignmentIcon = document.getElementById('alignmentIcon');
        const alignmentText = document.getElementById('alignmentText');
        
        const isPositiveSentiment = sentimentLabel === 'Positive';
        const isNegativeSentiment = sentimentLabel === 'Negative';
        const isUptrend = technicalTrend.includes('Uptrend');
        const isDowntrend = technicalTrend.includes('Downtrend');
        
        if ((isPositiveSentiment && isUptrend) || (isNegativeSentiment && isDowntrend)) {
            alignmentIcon.textContent = '✅';
            alignmentText.textContent = 'ALIGNED: Technical and sentiment signals agree (High Confidence)';
            alignmentText.className = 'aligned';
        } else if ((isPositiveSentiment && isDowntrend) || (isNegativeSentiment && isUptrend)) {
            alignmentIcon.textContent = '⚠️';
            alignmentText.textContent = 'DIVERGENCE: Technical and sentiment signals disagree (Caution Advised)';
            alignmentText.className = 'diverged';
        } else {
            alignmentIcon.textContent = '📊';
            alignmentText.textContent = 'MIXED: Neutral signals or sideways movement';
            alignmentText.className = 'mixed';
        }
    }

    function getTrendClass(trend) {
        if (trend.includes('Strong Uptrend')) return 'strong-uptrend';
        if (trend.includes('Uptrend')) return 'uptrend';
        if (trend.includes('Downtrend')) return 'downtrend';
        return 'sideways';
    }

    function getSentimentClass(sentiment) {
        if (sentiment === 'Positive') return 'positive';
        if (sentiment === 'Negative') return 'negative';
        return 'neutral';
    }

    function showError(message) {
        errorDisplay.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = message;
        resultsDiv.classList.add('hidden');
    }

    function showWarning(message) {
        console.warn('Warning:', message);
    }
});