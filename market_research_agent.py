import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass
import json
import os
from orchestrator import BaseAgent, AgentType, Task, InvestmentContext


@dataclass
class MarketData:
    symbol: str
    current_price: float
    volume: int
    market_cap: float
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    beta: float
    price_change_1d: float
    price_change_1w: float
    price_change_1m: float
    price_change_3m: float
    price_change_1y: float
    moving_avg_50: float
    moving_avg_200: float
    rsi: float
    support_level: float
    resistance_level: float
    timestamp: datetime


@dataclass
class CompanyFundamentals:
    symbol: str
    revenue: float
    earnings: float
    revenue_growth: float
    earnings_growth: float
    debt_to_equity: float
    current_ratio: float
    roe: float
    gross_margin: float
    operating_margin: float
    free_cash_flow: float
    
    
class DataProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("MARKET_DATA_API_KEY")
        self.base_url = "https://api.marketdata.provider"
        self.cache = {}
        self.cache_expiry = {}
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        cache_key = f"quote_{symbol}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        simulated_data = {
            "symbol": symbol,
            "price": np.random.uniform(10, 500),
            "volume": np.random.randint(1000000, 50000000),
            "marketCap": np.random.uniform(1e9, 1e12),
            "peRatio": np.random.uniform(10, 40),
            "dividendYield": np.random.uniform(0, 0.05),
            "beta": np.random.uniform(0.5, 2.0),
            "changePercent": np.random.uniform(-0.05, 0.05),
            "week52High": np.random.uniform(100, 600),
            "week52Low": np.random.uniform(50, 300)
        }
        
        self._cache_data(cache_key, simulated_data, 300)
        return simulated_data
    
    async def get_historical_prices(self, symbol: str, days: int = 365) -> pd.DataFrame:
        cache_key = f"historical_{symbol}_{days}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        prices = np.random.randn(days).cumsum() + 100
        prices = np.abs(prices)
        
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'open': prices * np.random.uniform(0.98, 1.02, days),
            'high': prices * np.random.uniform(1.01, 1.05, days),
            'low': prices * np.random.uniform(0.95, 0.99, days),
            'volume': np.random.randint(1000000, 50000000, days)
        })
        
        self._cache_data(cache_key, df, 3600)
        return df
    
    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        cache_key = f"fundamentals_{symbol}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        simulated_data = {
            "symbol": symbol,
            "revenue": np.random.uniform(1e9, 1e11),
            "earnings": np.random.uniform(1e8, 1e10),
            "revenueGrowth": np.random.uniform(-0.1, 0.3),
            "earningsGrowth": np.random.uniform(-0.2, 0.4),
            "debtToEquity": np.random.uniform(0.1, 2.0),
            "currentRatio": np.random.uniform(0.8, 3.0),
            "roe": np.random.uniform(0.05, 0.35),
            "grossMargin": np.random.uniform(0.2, 0.6),
            "operatingMargin": np.random.uniform(0.05, 0.3),
            "freeCashFlow": np.random.uniform(1e8, 1e10)
        }
        
        self._cache_data(cache_key, simulated_data, 3600)
        return simulated_data
    
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


class TechnicalAnalyzer:
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    @staticmethod
    def calculate_moving_averages(prices: pd.Series) -> Dict[str, float]:
        return {
            "ma_50": prices.rolling(window=50).mean().iloc[-1],
            "ma_200": prices.rolling(window=200).mean().iloc[-1]
        }
    
    @staticmethod
    def calculate_support_resistance(prices: pd.Series) -> Dict[str, float]:
        recent_prices = prices.tail(20)
        return {
            "support": recent_prices.min(),
            "resistance": recent_prices.max()
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20) -> Dict[str, float]:
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        return {
            "upper_band": upper_band.iloc[-1],
            "middle_band": sma.iloc[-1],
            "lower_band": lower_band.iloc[-1]
        }


class MarketResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("MarketResearchAgent", AgentType.MARKET_RESEARCH)
        self.data_provider = DataProvider()
        self.analyzer = TechnicalAnalyzer()
    
    async def process(self, task: Task, context: InvestmentContext) -> Dict[str, Any]:
        self.logger.info(f"Processing market research task: {task.task_id}")
        
        audit_log = self.log_audit("MARKET_RESEARCH_STARTED", context, {
            "task_id": task.task_id,
            "symbols": task.payload.get("symbols", [])
        })
        task.audit_trail.append(audit_log)
        
        try:
            symbols = task.payload.get("symbols", [])
            if not symbols:
                symbols = ["SPY", "QQQ", "DIA"]
            
            market_data = await self._gather_market_data(symbols)
            
            analysis = self._analyze_market_conditions(market_data)
            
            recommendations = self._generate_recommendations(analysis, context)
            
            result = {
                "market_data": market_data,
                "analysis": analysis,
                "recommendations": recommendations,
                "sources": ["MarketDataProvider API", "Technical Analysis"],
                "timestamp": datetime.now().isoformat()
            }
            
            audit_log = self.log_audit("MARKET_RESEARCH_COMPLETED", context, {
                "task_id": task.task_id,
                "symbols_analyzed": len(symbols),
                "recommendations_count": len(recommendations)
            })
            task.audit_trail.append(audit_log)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in market research: {str(e)}")
            audit_log = self.log_audit("MARKET_RESEARCH_FAILED", context, {
                "task_id": task.task_id,
                "error": str(e)
            })
            task.audit_trail.append(audit_log)
            raise
    
    async def _gather_market_data(self, symbols: List[str]) -> List[MarketData]:
        market_data = []
        
        for symbol in symbols:
            try:
                quote_task = self.data_provider.get_quote(symbol)
                historical_task = self.data_provider.get_historical_prices(symbol)
                fundamentals_task = self.data_provider.get_fundamentals(symbol)
                
                quote, historical, fundamentals = await asyncio.gather(
                    quote_task, historical_task, fundamentals_task
                )
                
                prices = historical['close']
                
                rsi = self.analyzer.calculate_rsi(prices)
                mas = self.analyzer.calculate_moving_averages(prices)
                support_resistance = self.analyzer.calculate_support_resistance(prices)
                
                price_changes = self._calculate_price_changes(prices)
                
                data = MarketData(
                    symbol=symbol,
                    current_price=quote['price'],
                    volume=quote['volume'],
                    market_cap=quote['marketCap'],
                    pe_ratio=quote.get('peRatio'),
                    dividend_yield=quote.get('dividendYield'),
                    beta=quote['beta'],
                    price_change_1d=price_changes['1d'],
                    price_change_1w=price_changes['1w'],
                    price_change_1m=price_changes['1m'],
                    price_change_3m=price_changes['3m'],
                    price_change_1y=price_changes['1y'],
                    moving_avg_50=mas['ma_50'],
                    moving_avg_200=mas['ma_200'],
                    rsi=rsi,
                    support_level=support_resistance['support'],
                    resistance_level=support_resistance['resistance'],
                    timestamp=datetime.now()
                )
                
                market_data.append(data)
                
            except Exception as e:
                self.logger.warning(f"Failed to get data for {symbol}: {str(e)}")
                continue
        
        return market_data
    
    def _calculate_price_changes(self, prices: pd.Series) -> Dict[str, float]:
        current_price = prices.iloc[-1]
        
        changes = {}
        periods = {'1d': 1, '1w': 7, '1m': 30, '3m': 90, '1y': 365}
        
        for label, days in periods.items():
            if len(prices) > days:
                past_price = prices.iloc[-days-1]
                changes[label] = (current_price - past_price) / past_price
            else:
                changes[label] = 0.0
        
        return changes
    
    def _analyze_market_conditions(self, market_data: List[MarketData]) -> Dict[str, Any]:
        if not market_data:
            return {"status": "no_data", "trend": "unknown"}
        
        avg_rsi = np.mean([d.rsi for d in market_data])
        avg_price_change_1m = np.mean([d.price_change_1m for d in market_data])
        
        above_ma50 = sum(1 for d in market_data if d.current_price > d.moving_avg_50)
        above_ma200 = sum(1 for d in market_data if d.current_price > d.moving_avg_200)
        
        total = len(market_data)
        
        trend = "neutral"
        if above_ma50 / total > 0.7 and above_ma200 / total > 0.6:
            trend = "bullish"
        elif above_ma50 / total < 0.3 and above_ma200 / total < 0.4:
            trend = "bearish"
        
        momentum = "neutral"
        if avg_rsi > 70:
            momentum = "overbought"
        elif avg_rsi < 30:
            momentum = "oversold"
        elif 50 < avg_rsi < 60:
            momentum = "positive"
        elif 40 < avg_rsi < 50:
            momentum = "negative"
        
        volatility = np.std([d.price_change_1d for d in market_data])
        
        analysis = {
            "trend": trend,
            "momentum": momentum,
            "avg_rsi": avg_rsi,
            "avg_price_change_1m": avg_price_change_1m,
            "above_ma50_pct": above_ma50 / total,
            "above_ma200_pct": above_ma200 / total,
            "volatility": volatility,
            "market_breadth": self._calculate_market_breadth(market_data)
        }
        
        return analysis
    
    def _calculate_market_breadth(self, market_data: List[MarketData]) -> str:
        advancing = sum(1 for d in market_data if d.price_change_1d > 0)
        declining = sum(1 for d in market_data if d.price_change_1d < 0)
        
        if advancing > declining * 2:
            return "very_positive"
        elif advancing > declining:
            return "positive"
        elif declining > advancing * 2:
            return "very_negative"
        elif declining > advancing:
            return "negative"
        else:
            return "neutral"
    
    def _generate_recommendations(self, analysis: Dict[str, Any], 
                                 context: InvestmentContext) -> List[str]:
        recommendations = []
        
        if analysis.get("trend") == "bullish" and analysis.get("momentum") != "overbought":
            recommendations.append("Market conditions favorable for equity positions")
        elif analysis.get("trend") == "bearish":
            recommendations.append("Consider defensive positions or cash allocation")
        
        if analysis.get("momentum") == "oversold":
            recommendations.append("Potential buying opportunity for contrarian investors")
        elif analysis.get("momentum") == "overbought":
            recommendations.append("Exercise caution with new long positions")
        
        if analysis.get("volatility", 0) > 0.02:
            recommendations.append("High volatility detected - consider position sizing adjustments")
        
        if context.risk_tolerance == "conservative" and analysis.get("volatility", 0) > 0.015:
            recommendations.append("Current market volatility may exceed risk tolerance")
        
        return recommendations