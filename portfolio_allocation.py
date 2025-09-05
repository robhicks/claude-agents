"""
Diversified Portfolio Allocation for $30,000
Using Modern Portfolio Theory and Liquid ETFs
"""

import math
from datetime import datetime

# Portfolio Configuration
TOTAL_PORTFOLIO_VALUE = 30000
RISK_FREE_RATE = 0.045  # Current 3-month T-bill rate approximately

def create_portfolio_allocation():
    """
    Create a diversified portfolio allocation using liquid ETFs
    Based on moderate risk tolerance and modern portfolio theory
    """
    
    # Define ETF universe with characteristics
    etfs = [
        {
            'ticker': 'SPY',
            'name': 'SPDR S&P 500 ETF',
            'asset_class': 'US Large Cap Equity',
            'expense_ratio': 0.0945,
            'avg_daily_volume': 75_000_000,  # Shares
            'expected_return': 0.10,  # Historical average
            'volatility': 0.16,
            'allocation': 0.25,  # 25%
            'rationale': 'Core US equity exposure with excellent liquidity and broad market representation'
        },
        {
            'ticker': 'QQQ',
            'name': 'Invesco QQQ Trust',
            'asset_class': 'US Large Cap Growth',
            'expense_ratio': 0.20,
            'avg_daily_volume': 45_000_000,
            'expected_return': 0.12,
            'volatility': 0.20,
            'allocation': 0.10,  # 10%
            'rationale': 'Technology and growth exposure for higher returns potential'
        },
        {
            'ticker': 'IWM',
            'name': 'iShares Russell 2000 ETF',
            'asset_class': 'US Small Cap Equity',
            'expense_ratio': 0.19,
            'avg_daily_volume': 35_000_000,
            'expected_return': 0.11,
            'volatility': 0.22,
            'allocation': 0.05,  # 5%
            'rationale': 'Small cap exposure for diversification and growth potential'
        },
        {
            'ticker': 'IEFA',
            'name': 'iShares Core MSCI EAFE ETF',
            'asset_class': 'International Developed Markets',
            'expense_ratio': 0.07,
            'avg_daily_volume': 8_000_000,
            'expected_return': 0.08,
            'volatility': 0.18,
            'allocation': 0.10,  # 10%
            'rationale': 'Developed international markets exposure for geographic diversification'
        },
        {
            'ticker': 'IEMG',
            'name': 'iShares Core MSCI Emerging Markets ETF',
            'asset_class': 'Emerging Markets Equity',
            'expense_ratio': 0.11,
            'avg_daily_volume': 12_000_000,
            'expected_return': 0.12,
            'volatility': 0.24,
            'allocation': 0.05,  # 5%
            'rationale': 'Emerging markets for higher growth potential and diversification'
        },
        {
            'ticker': 'AGG',
            'name': 'iShares Core U.S. Aggregate Bond ETF',
            'asset_class': 'US Investment Grade Bonds',
            'expense_ratio': 0.03,
            'avg_daily_volume': 6_000_000,
            'expected_return': 0.045,
            'volatility': 0.04,
            'allocation': 0.20,  # 20%
            'rationale': 'Core bond allocation for stability and income generation'
        },
        {
            'ticker': 'TIP',
            'name': 'iShares TIPS Bond ETF',
            'asset_class': 'Inflation-Protected Bonds',
            'expense_ratio': 0.19,
            'avg_daily_volume': 2_500_000,
            'expected_return': 0.05,
            'volatility': 0.06,
            'allocation': 0.05,  # 5%
            'rationale': 'Inflation protection through Treasury Inflation-Protected Securities'
        },
        {
            'ticker': 'HYG',
            'name': 'iShares iBoxx $ High Yield Corporate Bond ETF',
            'asset_class': 'High Yield Bonds',
            'expense_ratio': 0.49,
            'avg_daily_volume': 25_000_000,
            'expected_return': 0.065,
            'volatility': 0.08,
            'allocation': 0.05,  # 5%
            'rationale': 'Higher yield potential with moderate credit risk exposure'
        },
        {
            'ticker': 'VNQ',
            'name': 'Vanguard Real Estate ETF',
            'asset_class': 'Real Estate (REITs)',
            'expense_ratio': 0.12,
            'avg_daily_volume': 4_000_000,
            'expected_return': 0.09,
            'volatility': 0.19,
            'allocation': 0.10,  # 10%
            'rationale': 'Real estate exposure for inflation hedge and income generation'
        },
        {
            'ticker': 'GLD',
            'name': 'SPDR Gold Shares',
            'asset_class': 'Commodities (Gold)',
            'expense_ratio': 0.40,
            'avg_daily_volume': 8_000_000,
            'expected_return': 0.06,
            'volatility': 0.15,
            'allocation': 0.05,  # 5%
            'rationale': 'Gold as portfolio hedge and uncorrelated asset for crisis protection'
        }
    ]
    
    # Add dollar allocation to each ETF
    for etf in etfs:
        etf['dollar_allocation'] = etf['allocation'] * TOTAL_PORTFOLIO_VALUE
    
    # Verify allocations sum to 100%
    total_allocation = sum(etf['allocation'] for etf in etfs)
    assert abs(total_allocation - 1.0) < 0.001, f"Allocations must sum to 100%, got {total_allocation*100:.1f}%"
    
    return etfs

def calculate_portfolio_metrics(etfs):
    """
    Calculate portfolio-level risk and return metrics
    """
    # Calculate weighted returns
    portfolio_return = sum(etf['expected_return'] * etf['allocation'] for etf in etfs)
    
    # Simplified portfolio volatility calculation using correlation assumptions
    # Group ETFs by asset class for correlation
    equity_weight = sum(etf['allocation'] for etf in etfs if 'Equity' in etf['asset_class'] or 'Market' in etf['asset_class'])
    bond_weight = sum(etf['allocation'] for etf in etfs if 'Bond' in etf['asset_class'])
    alt_weight = sum(etf['allocation'] for etf in etfs if 'REIT' in etf['asset_class'] or 'Commodities' in etf['asset_class'])
    
    # Weighted volatilities by asset class
    equity_vol = 0.18  # Average equity volatility
    bond_vol = 0.05    # Average bond volatility
    alt_vol = 0.17     # Average alternative volatility
    
    # Simplified portfolio volatility with diversification benefit
    # Using correlation estimates: equity-bond = -0.1, equity-alt = 0.3, bond-alt = 0.1
    portfolio_variance = (
        (equity_weight * equity_vol) ** 2 +
        (bond_weight * bond_vol) ** 2 +
        (alt_weight * alt_vol) ** 2 +
        2 * equity_weight * bond_weight * equity_vol * bond_vol * (-0.1) +
        2 * equity_weight * alt_weight * equity_vol * alt_vol * 0.3 +
        2 * bond_weight * alt_weight * bond_vol * alt_vol * 0.1
    )
    
    portfolio_volatility = math.sqrt(portfolio_variance)
    
    # Calculate Sharpe Ratio
    sharpe_ratio = (portfolio_return - RISK_FREE_RATE) / portfolio_volatility
    
    # Estimate maximum drawdown (using 2.5 standard deviation event)
    max_drawdown = -2.5 * portfolio_volatility
    
    return {
        'expected_return': portfolio_return,
        'volatility': portfolio_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'risk_free_rate': RISK_FREE_RATE
    }

def display_portfolio_summary():
    """
    Display comprehensive portfolio allocation and metrics
    """
    print("=" * 80)
    print("DIVERSIFIED PORTFOLIO ALLOCATION FOR $30,000")
    print("Investment Strategy: Moderate Risk, Globally Diversified")
    print("=" * 80)
    print()
    
    # Create portfolio
    etfs = create_portfolio_allocation()
    
    # Sort by allocation for display
    etfs.sort(key=lambda x: x['allocation'], reverse=True)
    
    print("PORTFOLIO HOLDINGS:")
    print("-" * 80)
    
    for etf in etfs:
        print(f"\n{etf['ticker']}: {etf['name']}")
        print(f"  Asset Class: {etf['asset_class']}")
        print(f"  Allocation: {etf['allocation']*100:.1f}% (${etf['dollar_allocation']:,.0f})")
        print(f"  Expense Ratio: {etf['expense_ratio']:.3f}%")
        print(f"  Avg Daily Volume: {etf['avg_daily_volume']:,.0f} shares")
        print(f"  Expected Return: {etf['expected_return']*100:.1f}%")
        print(f"  Volatility: {etf['volatility']*100:.1f}%")
        print(f"  Rationale: {etf['rationale']}")
    
    print("\n" + "=" * 80)
    print("PORTFOLIO ALLOCATION SUMMARY:")
    print("-" * 80)
    
    # Calculate category allocations
    equity_allocation = sum(etf['allocation'] for etf in etfs 
                           if 'Equity' in etf['asset_class'] or 'Market' in etf['asset_class'])
    bond_allocation = sum(etf['allocation'] for etf in etfs 
                         if 'Bond' in etf['asset_class'])
    alternative_allocation = sum(etf['allocation'] for etf in etfs 
                                if 'REIT' in etf['asset_class'] or 'Commodities' in etf['asset_class'])
    
    print(f"\nMajor Asset Categories:")
    print(f"  Equities: {equity_allocation*100:.1f}% (${equity_allocation*TOTAL_PORTFOLIO_VALUE:,.0f})")
    print(f"  Fixed Income: {bond_allocation*100:.1f}% (${bond_allocation*TOTAL_PORTFOLIO_VALUE:,.0f})")
    print(f"  Alternatives: {alternative_allocation*100:.1f}% (${alternative_allocation*TOTAL_PORTFOLIO_VALUE:,.0f})")
    
    # Calculate portfolio metrics
    metrics = calculate_portfolio_metrics(etfs)
    
    print("\n" + "=" * 80)
    print("PORTFOLIO RISK/RETURN METRICS:")
    print("-" * 80)
    print(f"Expected Annual Return: {metrics['expected_return']*100:.2f}%")
    print(f"Portfolio Volatility: {metrics['volatility']*100:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    print(f"Maximum Expected Drawdown (95% confidence): {metrics['max_drawdown']*100:.1f}%")
    print(f"Risk-Free Rate (baseline): {metrics['risk_free_rate']*100:.2f}%")
    
    print("\n" + "=" * 80)
    print("PORTFOLIO CHARACTERISTICS:")
    print("-" * 80)
    
    # Calculate weighted expense ratio
    weighted_expense = sum(etf['expense_ratio'] * etf['allocation'] for etf in etfs)
    print(f"Weighted Average Expense Ratio: {weighted_expense:.3f}%")
    
    # Check liquidity
    min_volume = min(etf['avg_daily_volume'] for etf in etfs)
    print(f"Minimum Daily Volume (liquidity check): {min_volume:,.0f} shares")
    print(f"All ETFs meet high liquidity requirements: {'YES' if min_volume > 1_000_000 else 'NO'}")
    
    print("\n" + "=" * 80)
    print("REBALANCING RECOMMENDATIONS:")
    print("-" * 80)
    print("Frequency: Quarterly (every 3 months)")
    print("Threshold: Rebalance when any position deviates >5% from target allocation")
    print("Method: Sell overweight positions first, then buy underweight positions")
    print("Tax Consideration: Use tax-loss harvesting opportunities during rebalancing")
    
    print("\n" + "=" * 80)
    print("IMPLEMENTATION NOTES:")
    print("-" * 80)
    print("1. All ETFs selected have excellent liquidity (>1M shares daily volume)")
    print("2. Expense ratios are competitive (weighted average under 0.15%)")
    print("3. Portfolio is globally diversified across asset classes and geographies")
    print("4. Allocation suitable for moderate risk tolerance with 10+ year horizon")
    print("5. Consider dollar-cost averaging over 2-3 months for initial investment")
    
    return etfs, metrics

def create_efficient_frontier_analysis():
    """
    Additional analysis showing risk-return tradeoffs
    """
    print("\n" + "=" * 80)
    print("RISK-RETURN PROFILE COMPARISON:")
    print("-" * 80)
    
    profiles = {
        'Conservative': {'equity': 0.30, 'bonds': 0.60, 'alternatives': 0.10, 'return': 0.065, 'vol': 0.08},
        'Moderate (Selected)': {'equity': 0.55, 'bonds': 0.30, 'alternatives': 0.15, 'return': 0.082, 'vol': 0.12},
        'Aggressive': {'equity': 0.75, 'bonds': 0.15, 'alternatives': 0.10, 'return': 0.095, 'vol': 0.16}
    }
    
    for profile_name, profile in profiles.items():
        sharpe = (profile['return'] - RISK_FREE_RATE) / profile['vol']
        marker = " <-- YOUR PORTFOLIO" if "Selected" in profile_name else ""
        print(f"\n{profile_name}:{marker}")
        print(f"  Allocation: {profile['equity']*100:.0f}% Equity / {profile['bonds']*100:.0f}% Bonds / {profile['alternatives']*100:.0f}% Alts")
        print(f"  Expected Return: {profile['return']*100:.1f}%")
        print(f"  Volatility: {profile['vol']*100:.1f}%")
        print(f"  Sharpe Ratio: {sharpe:.3f}")

if __name__ == "__main__":
    # Generate complete portfolio analysis
    etfs, metrics = display_portfolio_summary()
    
    # Show risk-return comparison
    create_efficient_frontier_analysis()
    
    print("\n" + "=" * 80)
    print("Portfolio allocation complete. Ready for implementation.")
    print("=" * 80)