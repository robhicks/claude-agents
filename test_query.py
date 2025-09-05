#!/usr/bin/env python3
"""
Test script for the Financial Investment Subagent
Demonstrates handling of beta-constrained portfolio query
"""

import asyncio
from datetime import datetime
from orchestrator import OrchestratorAgent, InvestmentContext
from market_research_agent import MarketResearchAgent
from sentiment_analysis_agent import SentimentAnalysisAgent
from risk_assessment_agent import RiskAssessmentAgent
from portfolio_construction_agent import PortfolioConstructionAgent, AssetScreener


def demonstrate_beta_constrained_portfolio():
    """
    Demonstrates the system's ability to handle a specific investment query
    with beta constraints and liquidity requirements.
    """
    
    print("\n" + "="*80)
    print("BETA-CONSTRAINED PORTFOLIO DEMONSTRATION")
    print("="*80)
    
    # Original user query
    query = """I have $30,000 that I want to invest in highly liquid financial 
    investment vehicles in the United States with betas ranging from 0.4 to 0.8. 
    Please generate a list of potential investments and the amount I should invest 
    in each of them in order to obtain good diversification."""
    
    print(f"\nQuery: {query}")
    print("\n" + "-"*80)
    
    # Initialize the asset screener
    screener = AssetScreener()
    
    # Screen for assets matching the criteria
    eligible_assets = screener.screen_assets(
        min_beta=0.4,
        max_beta=0.8,
        min_liquidity=0.85  # "highly liquid" requirement
    )
    
    print(f"\nFound {len(eligible_assets)} assets matching criteria:")
    print("\n{:<10} {:<50} {:<10} {:<10} {:<10}".format(
        "Symbol", "Description", "Beta", "Liquidity", "Expense"
    ))
    print("-"*100)
    
    for asset in eligible_assets[:15]:  # Show top 15
        print("{:<10} {:<50} {:<10.2f} {:<10.2f} {:<10.4f}".format(
            asset.symbol,
            asset.description[:48] + ".." if len(asset.description) > 48 else asset.description,
            asset.beta,
            asset.liquidity_score,
            asset.expense_ratio
        ))
    
    # Create a simulated optimized portfolio
    from portfolio_construction_agent import PortfolioOptimizer
    optimizer = PortfolioOptimizer()
    
    # Optimize the portfolio
    optimized = optimizer.optimize_portfolio(
        assets=eligible_assets,
        capital=30000,
        target_return=None,  # Let optimizer find best Sharpe ratio
        max_position_size=0.25  # Max 25% in any single asset for diversification
    )
    
    print("\n" + "-"*80)
    print("OPTIMIZED PORTFOLIO ALLOCATION")
    print("-"*80)
    
    print("\n{:<10} {:<40} {:<10} {:<15}".format(
        "Symbol", "Investment", "Weight", "Amount"
    ))
    print("-"*80)
    
    total_invested = 0
    for symbol, weight in optimized.allocations.items():
        amount = 30000 * weight
        total_invested += amount
        
        # Find asset details
        asset_detail = next((a for a in eligible_assets if a.symbol == symbol), None)
        if asset_detail:
            print("{:<10} {:<40} {:<10.2%} ${:<14,.2f}".format(
                symbol,
                asset_detail.description[:38] + ".." if len(asset_detail.description) > 38 else asset_detail.description,
                weight,
                amount
            ))
    
    print("-"*80)
    print("{:<52} {:<10} ${:<14,.2f}".format("TOTAL", "", total_invested))
    
    print("\n" + "-"*80)
    print("PORTFOLIO METRICS")
    print("-"*80)
    
    metrics = [
        ("Expected Annual Return", f"{optimized.expected_return:.2%}"),
        ("Portfolio Volatility", f"{optimized.portfolio_volatility:.2%}"),
        ("Portfolio Beta", f"{optimized.portfolio_beta:.3f}"),
        ("Sharpe Ratio", f"{optimized.sharpe_ratio:.3f}"),
        ("Diversification Score", f"{optimized.diversification_score:.3f}"),
        ("Total Expense Ratio", f"{optimized.total_expense_ratio:.4f}"),
        ("Annual Cost", f"${30000 * optimized.total_expense_ratio:.2f}")
    ]
    
    for metric, value in metrics:
        print(f"{metric:<30} {value}")
    
    print("\n" + "-"*80)
    print("KEY FEATURES DEMONSTRATED")
    print("-"*80)
    
    features = [
        "✓ Beta constraints applied (0.4 - 0.8)",
        "✓ High liquidity filter (score > 0.85)",
        "✓ Diversification enforced (max 25% per position)",
        "✓ Expense ratio optimization",
        "✓ Risk-adjusted returns (Sharpe ratio maximization)",
        "✓ Transparent allocation with dollar amounts"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n" + "-"*80)
    print("COMPLIANCE & RISK NOTICES")
    print("-"*80)
    
    notices = [
        "• This is for informational purposes only, not financial advice",
        "• Past performance does not guarantee future results",
        "• Consult with a qualified financial advisor before investing",
        "• All investments carry risk of loss",
        "• Portfolio requires human review before implementation"
    ]
    
    for notice in notices:
        print(notice)


if __name__ == "__main__":
    demonstrate_beta_constrained_portfolio()
    print("\n")