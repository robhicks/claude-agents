import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import re
from dataclasses import dataclass
from collections import Counter
import numpy as np
from orchestrator import BaseAgent, AgentType, Task, InvestmentContext


@dataclass
class SentimentScore:
    positive: float
    negative: float
    neutral: float
    compound: float
    confidence: float


@dataclass
class NewsItem:
    title: str
    source: str
    url: str
    published_date: datetime
    content: str
    sentiment: SentimentScore
    entities: List[str]
    keywords: List[str]


@dataclass
class SocialMediaPost:
    platform: str
    author: str
    content: str
    timestamp: datetime
    engagement: int
    sentiment: SentimentScore
    influence_score: float


class TextAnalyzer:
    def __init__(self):
        self.positive_words = {
            'bullish', 'growth', 'profit', 'gain', 'rise', 'increase', 'strong',
            'outperform', 'beat', 'exceed', 'surge', 'rally', 'breakthrough',
            'innovative', 'expansion', 'success', 'optimistic', 'favorable',
            'upgrade', 'positive', 'boom', 'soar', 'jump', 'climb', 'advance'
        }
        
        self.negative_words = {
            'bearish', 'loss', 'decline', 'fall', 'drop', 'decrease', 'weak',
            'underperform', 'miss', 'deficit', 'crash', 'plunge', 'collapse',
            'concern', 'risk', 'failure', 'pessimistic', 'unfavorable',
            'downgrade', 'negative', 'recession', 'sink', 'tumble', 'retreat'
        }
        
        self.neutral_words = {
            'steady', 'unchanged', 'flat', 'stable', 'maintain', 'hold',
            'moderate', 'average', 'normal', 'typical', 'standard', 'regular'
        }
    
    def analyze_sentiment(self, text: str) -> SentimentScore:
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        neutral_count = sum(1 for word in words if word in self.neutral_words)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return SentimentScore(
                positive=0.0,
                negative=0.0,
                neutral=1.0,
                compound=0.0,
                confidence=0.3
            )
        
        positive_score = positive_count / total_sentiment_words
        negative_score = negative_count / total_sentiment_words
        neutral_score = neutral_count / total_sentiment_words
        
        compound_score = (positive_score - negative_score)
        
        confidence = min(total_sentiment_words / len(words), 1.0) if words else 0.0
        
        return SentimentScore(
            positive=positive_score,
            negative=negative_score,
            neutral=neutral_score,
            compound=compound_score,
            confidence=confidence
        )
    
    def extract_entities(self, text: str) -> List[str]:
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b|\b[A-Z]{2,5}\b'
        entities = re.findall(pattern, text)
        
        filtered_entities = []
        for entity in entities:
            if len(entity) > 1 and entity not in ['The', 'This', 'That', 'These', 'Those']:
                filtered_entities.append(entity)
        
        return list(set(filtered_entities))
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        stopwords = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was',
            'were', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall',
            'to', 'of', 'in', 'for', 'with', 'from', 'up', 'about', 'into',
            'through', 'during', 'before', 'after', 'above', 'below', 'between'
        }
        
        filtered_words = [w for w in words if w not in stopwords and len(w) > 3]
        
        word_freq = Counter(filtered_words)
        
        return [word for word, _ in word_freq.most_common(top_n)]


class NewsDataProvider:
    def __init__(self):
        self.sources = [
            "Financial Times", "Wall Street Journal", "Bloomberg",
            "Reuters", "CNBC", "MarketWatch", "The Economist"
        ]
        self.cache = {}
        self.cache_expiry = {}
    
    async def fetch_news(self, symbols: List[str], days: int = 7) -> List[NewsItem]:
        cache_key = f"news_{'_'.join(sorted(symbols))}_{days}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        news_items = []
        analyzer = TextAnalyzer()
        
        for symbol in symbols:
            for i in range(np.random.randint(3, 8)):
                title = self._generate_news_title(symbol)
                content = self._generate_news_content(symbol, title)
                
                news_item = NewsItem(
                    title=title,
                    source=np.random.choice(self.sources),
                    url=f"https://news.example.com/{symbol}/{i}",
                    published_date=datetime.now() - timedelta(
                        days=np.random.randint(0, days),
                        hours=np.random.randint(0, 24)
                    ),
                    content=content,
                    sentiment=analyzer.analyze_sentiment(content),
                    entities=analyzer.extract_entities(content),
                    keywords=analyzer.extract_keywords(content)
                )
                
                news_items.append(news_item)
        
        self._cache_data(cache_key, news_items, 1800)
        return news_items
    
    def _generate_news_title(self, symbol: str) -> str:
        templates = [
            f"{symbol} Reports Strong Quarterly Earnings",
            f"Analysts Upgrade {symbol} Following Product Launch",
            f"{symbol} Faces Regulatory Scrutiny",
            f"Market Volatility Impacts {symbol} Trading",
            f"{symbol} Announces Strategic Partnership",
            f"Investors Eye {symbol} Ahead of Fed Decision",
            f"{symbol} Stock Rallies on Positive Guidance"
        ]
        return np.random.choice(templates)
    
    def _generate_news_content(self, symbol: str, title: str) -> str:
        sentiment_type = np.random.choice(['positive', 'negative', 'neutral'], p=[0.4, 0.3, 0.3])
        
        if sentiment_type == 'positive':
            content = f"{title}. {symbol} has shown strong performance with revenue growth " \
                     f"exceeding analyst expectations. The company's innovative approach and " \
                     f"strategic expansion plans have positioned it well for future growth. " \
                     f"Investors remain bullish on the stock's prospects."
        elif sentiment_type == 'negative':
            content = f"{title}. {symbol} faces challenges as market conditions remain uncertain. " \
                     f"Concerns about regulatory compliance and increasing competition have " \
                     f"led to a bearish outlook. Analysts suggest caution as the company " \
                     f"navigates through these headwinds."
        else:
            content = f"{title}. {symbol} maintains steady operations amid mixed market signals. " \
                     f"The company continues to execute its business plan while monitoring " \
                     f"market conditions. Analysts maintain a neutral stance as they await " \
                     f"further developments."
        
        return content
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        if datetime.now() > self.cache_expiry[key]:
            del self.cache[key]
            del self.cache_expiry[key]
            return False
        return True
    
    def _cache_data(self, key: str, data: Any, ttl_seconds: int):
        self.cache[key] = data
        self.cache_expiry[key] = datetime.now() + timedelta(seconds=ttl_seconds)


class SocialMediaAnalyzer:
    def __init__(self):
        self.platforms = ["Twitter", "Reddit", "StockTwits", "LinkedIn"]
        self.influencer_threshold = 10000
    
    async def fetch_social_sentiment(self, symbols: List[str]) -> List[SocialMediaPost]:
        posts = []
        analyzer = TextAnalyzer()
        
        for symbol in symbols:
            for _ in range(np.random.randint(5, 15)):
                content = self._generate_post_content(symbol)
                platform = np.random.choice(self.platforms)
                
                post = SocialMediaPost(
                    platform=platform,
                    author=f"user_{np.random.randint(1000, 9999)}",
                    content=content,
                    timestamp=datetime.now() - timedelta(
                        hours=np.random.randint(0, 72),
                        minutes=np.random.randint(0, 60)
                    ),
                    engagement=np.random.randint(10, 10000),
                    sentiment=analyzer.analyze_sentiment(content),
                    influence_score=self._calculate_influence_score(platform)
                )
                
                posts.append(post)
        
        return posts
    
    def _generate_post_content(self, symbol: str) -> str:
        templates = [
            f"${symbol} looking strong today! Breakout incoming? 🚀",
            f"Time to take profits on ${symbol}? Getting overextended here",
            f"${symbol} holding support well. Adding to position",
            f"Bearish on ${symbol} short term. Too much resistance overhead",
            f"${symbol} chart setup is perfect for a swing trade",
            f"Watching ${symbol} closely. Key levels to watch...",
            f"${symbol} earnings next week. Playing it safe",
            f"Long ${symbol} here. Fundamentals are solid"
        ]
        return np.random.choice(templates)
    
    def _calculate_influence_score(self, platform: str) -> float:
        base_scores = {
            "Twitter": 0.7,
            "Reddit": 0.6,
            "StockTwits": 0.5,
            "LinkedIn": 0.8
        }
        
        base_score = base_scores.get(platform, 0.5)
        
        follower_factor = np.random.uniform(0.1, 1.0)
        
        return base_score * follower_factor


class SentimentAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("SentimentAnalysisAgent", AgentType.SENTIMENT_ANALYSIS)
        self.news_provider = NewsDataProvider()
        self.social_analyzer = SocialMediaAnalyzer()
        self.text_analyzer = TextAnalyzer()
    
    async def process(self, task: Task, context: InvestmentContext) -> Dict[str, Any]:
        self.logger.info(f"Processing sentiment analysis task: {task.task_id}")
        
        audit_log = self.log_audit("SENTIMENT_ANALYSIS_STARTED", context, {
            "task_id": task.task_id,
            "symbols": task.payload.get("symbols", [])
        })
        task.audit_trail.append(audit_log)
        
        try:
            symbols = task.payload.get("symbols", [])
            if not symbols:
                symbols = ["AAPL", "GOOGL", "MSFT"]
            
            news_task = self.news_provider.fetch_news(symbols)
            social_task = self.social_analyzer.fetch_social_sentiment(symbols)
            
            news_items, social_posts = await asyncio.gather(news_task, social_task)
            
            news_sentiment = self._aggregate_news_sentiment(news_items)
            social_sentiment = self._aggregate_social_sentiment(social_posts)
            overall_sentiment = self._calculate_overall_sentiment(news_sentiment, social_sentiment)
            
            trend_analysis = self._analyze_sentiment_trends(news_items, social_posts)
            
            key_topics = self._extract_key_topics(news_items)
            
            result = {
                "overall": overall_sentiment,
                "news_sentiment": news_sentiment,
                "social_sentiment": social_sentiment,
                "trend_analysis": trend_analysis,
                "key_topics": key_topics,
                "news_items_analyzed": len(news_items),
                "social_posts_analyzed": len(social_posts),
                "sources": list(set([item.source for item in news_items])),
                "timestamp": datetime.now().isoformat()
            }
            
            audit_log = self.log_audit("SENTIMENT_ANALYSIS_COMPLETED", context, {
                "task_id": task.task_id,
                "overall_sentiment": overall_sentiment,
                "items_analyzed": len(news_items) + len(social_posts)
            })
            task.audit_trail.append(audit_log)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {str(e)}")
            audit_log = self.log_audit("SENTIMENT_ANALYSIS_FAILED", context, {
                "task_id": task.task_id,
                "error": str(e)
            })
            task.audit_trail.append(audit_log)
            raise
    
    def _aggregate_news_sentiment(self, news_items: List[NewsItem]) -> Dict[str, float]:
        if not news_items:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0}
        
        weighted_sentiments = []
        weights = []
        
        for item in news_items:
            recency_weight = self._calculate_recency_weight(item.published_date)
            
            source_weight = 1.2 if item.source in ["Financial Times", "Wall Street Journal"] else 1.0
            
            weight = recency_weight * source_weight * item.sentiment.confidence
            
            weighted_sentiments.append(item.sentiment)
            weights.append(weight)
        
        total_weight = sum(weights)
        
        if total_weight == 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0}
        
        aggregate = {
            "positive": sum(s.positive * w for s, w in zip(weighted_sentiments, weights)) / total_weight,
            "negative": sum(s.negative * w for s, w in zip(weighted_sentiments, weights)) / total_weight,
            "neutral": sum(s.neutral * w for s, w in zip(weighted_sentiments, weights)) / total_weight,
            "compound": sum(s.compound * w for s, w in zip(weighted_sentiments, weights)) / total_weight
        }
        
        return aggregate
    
    def _aggregate_social_sentiment(self, posts: List[SocialMediaPost]) -> Dict[str, float]:
        if not posts:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0}
        
        weighted_sentiments = []
        weights = []
        
        for post in posts:
            recency_weight = self._calculate_recency_weight(post.timestamp)
            
            engagement_weight = min(np.log1p(post.engagement) / 10, 2.0)
            
            weight = recency_weight * engagement_weight * post.influence_score
            
            weighted_sentiments.append(post.sentiment)
            weights.append(weight)
        
        total_weight = sum(weights)
        
        if total_weight == 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0}
        
        aggregate = {
            "positive": sum(s.positive * w for s, w in zip(weighted_sentiments, weights)) / total_weight,
            "negative": sum(s.negative * w for s, w in zip(weighted_sentiments, weights)) / total_weight,
            "neutral": sum(s.neutral * w for s, w in zip(weighted_sentiments, weights)) / total_weight,
            "compound": sum(s.compound * w for s, w in zip(weighted_sentiments, weights)) / total_weight
        }
        
        return aggregate
    
    def _calculate_recency_weight(self, timestamp: datetime) -> float:
        hours_ago = (datetime.now() - timestamp).total_seconds() / 3600
        
        if hours_ago < 24:
            return 1.0
        elif hours_ago < 72:
            return 0.8
        elif hours_ago < 168:
            return 0.6
        else:
            return 0.4
    
    def _calculate_overall_sentiment(self, news: Dict[str, float], 
                                    social: Dict[str, float]) -> str:
        
        news_weight = 0.6
        social_weight = 0.4
        
        compound = (news["compound"] * news_weight + social["compound"] * social_weight)
        
        if compound > 0.3:
            return "very_positive"
        elif compound > 0.1:
            return "positive"
        elif compound < -0.3:
            return "very_negative"
        elif compound < -0.1:
            return "negative"
        else:
            return "neutral"
    
    def _analyze_sentiment_trends(self, news_items: List[NewsItem], 
                                 social_posts: List[SocialMediaPost]) -> Dict[str, Any]:
        
        all_items = []
        
        for item in news_items:
            all_items.append((item.published_date, item.sentiment.compound))
        
        for post in social_posts:
            all_items.append((post.timestamp, post.sentiment.compound))
        
        all_items.sort(key=lambda x: x[0])
        
        if len(all_items) < 2:
            return {"trend": "insufficient_data", "momentum": 0.0}
        
        recent_sentiment = np.mean([s for _, s in all_items[-len(all_items)//3:]])
        older_sentiment = np.mean([s for _, s in all_items[:len(all_items)//3]])
        
        momentum = recent_sentiment - older_sentiment
        
        if momentum > 0.2:
            trend = "improving"
        elif momentum < -0.2:
            trend = "deteriorating"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "momentum": momentum,
            "recent_sentiment": recent_sentiment,
            "older_sentiment": older_sentiment
        }
    
    def _extract_key_topics(self, news_items: List[NewsItem]) -> List[Tuple[str, int]]:
        all_keywords = []
        
        for item in news_items:
            all_keywords.extend(item.keywords)
        
        keyword_counts = Counter(all_keywords)
        
        return keyword_counts.most_common(10)