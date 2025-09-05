import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from orchestrator import OrchestratorAgent, InvestmentContext
from market_research_agent import MarketResearchAgent
from sentiment_analysis_agent import SentimentAnalysisAgent
from risk_assessment_agent import RiskAssessmentAgent
from portfolio_construction_agent import PortfolioConstructionAgent


class FinancialInvestmentSubagent:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self._register_agents()
    
    def _register_agents(self):
        self.orchestrator.register_agent(MarketResearchAgent())
        self.orchestrator.register_agent(SentimentAnalysisAgent())
        self.orchestrator.register_agent(RiskAssessmentAgent())
        self.orchestrator.register_agent(PortfolioConstructionAgent())
    
    async def process_investment_query(self, query: str, **kwargs) -> Dict[str, Any]:
        
        context = self._build_context_from_query(query, **kwargs)
        
        recommendation = await self.orchestrator.process_request(query, context)
        
        formatted_result = self._format_recommendation(recommendation)
        
        return formatted_result
    
    def _build_context_from_query(self, query: str, **kwargs) -> InvestmentContext:
        
        capital = kwargs.get('capital', 30000)
        if '$' in query:
            import re
            amounts = re.findall(r'\$([0-9,]+)', query)
            if amounts:
                capital = float(amounts[0].replace(',', ''))
        
        risk_tolerance = kwargs.get('risk_tolerance', 'moderate')
        if 'conservative' in query.lower():
            risk_tolerance = 'conservative'
        elif 'aggressive' in query.lower():
            risk_tolerance = 'aggressive'
        
        beta_range = kwargs.get('beta_range', None)
        if 'beta' in query.lower():
            import re
            beta_matches = re.findall(r'beta[s]?\s+(?:ranging\s+from\s+)?([0-9.]+)\s+to\s+([0-9.]+)', query.lower())
            if beta_matches:
                beta_range = (float(beta_matches[0][0]), float(beta_matches[0][1]))
        
        context = InvestmentContext(
            user_id=kwargs.get('user_id', 'demo_user'),
            risk_tolerance=risk_tolerance,
            investment_horizon=kwargs.get('investment_horizon', '5 years'),
            capital_available=capital,
            investment_goals=kwargs.get('goals', ['growth', 'diversification']),
            restrictions=kwargs.get('restrictions', []),
            regulatory_jurisdiction=kwargs.get('jurisdiction', 'US')
        )
        
        if beta_range:
            context.beta_constraints = beta_range
        
        return context
    
    def _format_recommendation(self, recommendation) -> Dict[str, Any]:
        
        portfolio = recommendation.portfolio
        
        if portfolio:
            print("\n" + "="*60)
            print("INVESTMENT RECOMMENDATION")
            print("="*60)
            print(f"\nRecommendation ID: {recommendation.recommendation_id}")
            print(f"Timestamp: {recommendation.timestamp}")
            print(f"Confidence Score: {recommendation.confidence_score:.2%}")
            
            if recommendation.human_review_required:
                print("\n⚠️  HUMAN REVIEW REQUIRED")
            
            print("\n" + "-"*40)
            print("PORTFOLIO ALLOCATION")
            print("-"*40)
            
            for symbol, allocation in portfolio.items():
                amount = recommendation.context.capital_available * allocation
                print(f"{symbol:10} {allocation:>7.2%}  ${amount:>12,.2f}")
            
            print("\n" + "-"*40)
            print("RISK METRICS")
            print("-"*40)
            for metric, value in recommendation.risk_metrics.items():
                if isinstance(value, float):
                    print(f"{metric:25} {value:>10.4f}")
            
            print("\n" + "-"*40)
            print("EXPECTED RETURNS")
            print("-"*40)
            for metric, value in recommendation.expected_returns.items():
                if isinstance(value, float):
                    if 'dollar' in metric.lower():
                        print(f"{metric:25} ${value:>10,.2f}")
                    else:
                        print(f"{metric:25} {value:>10.2%}")
            
            if recommendation.warnings:
                print("\n" + "-"*40)
                print("WARNINGS")
                print("-"*40)
                for warning in recommendation.warnings:
                    print(f"• {warning}")
            
            if recommendation.reasoning:
                print("\n" + "-"*40)
                print("ANALYSIS")
                print("-"*40)
                for reason in recommendation.reasoning:
                    print(f"• {reason}")
        
        return {
            "recommendation_id": recommendation.recommendation_id,
            "portfolio": recommendation.portfolio,
            "risk_metrics": recommendation.risk_metrics,
            "expected_returns": recommendation.expected_returns,
            "confidence_score": recommendation.confidence_score,
            "warnings": recommendation.warnings,
            "human_review_required": recommendation.human_review_required
        }


async def example_beta_constrained_query():
    
    subagent = FinancialInvestmentSubagent()
    
    query = """I have $30,000 that I want to invest in highly liquid financial 
    investment vehicles in the United States with betas ranging from 0.4 to 0.8. 
    Please generate a list of potential investments and the amount I should invest 
    in each of them in order to obtain good diversification."""
    
    result = await subagent.process_investment_query(query)
    
    return result


async def example_conservative_query():
    
    subagent = FinancialInvestmentSubagent()
    
    query = """I have $50,000 for conservative investment. I'm near retirement 
    and need stable income with minimal risk."""
    
    result = await subagent.process_investment_query(
        query,
        user_id="conservative_investor",
        investment_horizon="3 years",
        goals=["income", "capital_preservation"]
    )
    
    return result


async def example_growth_query():
    
    subagent = FinancialInvestmentSubagent()
    
    query = """I want to invest $100,000 aggressively for long-term growth. 
    I can tolerate significant volatility."""
    
    result = await subagent.process_investment_query(
        query,
        user_id="growth_investor",
        risk_tolerance="aggressive",
        investment_horizon="10 years",
        goals=["growth", "wealth_accumulation"]
    )
    
    return result


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FINANCIAL INVESTMENT SUBAGENT DEMO")
    print("="*60)
    
    print("\nExample 1: Beta-Constrained Portfolio (0.4-0.8)")
    print("-"*60)
    asyncio.run(example_beta_constrained_query())
    
    print("\n\nExample 2: Conservative Retirement Portfolio")
    print("-"*60)
    asyncio.run(example_conservative_query())
    
    print("\n\nExample 3: Aggressive Growth Portfolio")
    print("-"*60)
    asyncio.run(example_growth_query())