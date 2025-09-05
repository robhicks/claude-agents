import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from scipy.optimize import minimize
from orchestrator import BaseAgent, AgentType, Task, InvestmentContext


@dataclass
class AssetCandidate:
    symbol: str
    asset_type: str
    beta: float
    expected_return: float
    volatility: float
    liquidity_score: float
    expense_ratio: float
    market_cap: float
    sector: str
    description: str


@dataclass
class OptimizedPortfolio:
    allocations: Dict[str, float]
    expected_return: float
    portfolio_volatility: float
    portfolio_beta: float
    sharpe_ratio: float
    diversification_score: float
    total_expense_ratio: float


class AssetScreener:
    def __init__(self):
        self.asset_universe = self._initialize_asset_universe()
    
    def _initialize_asset_universe(self) -> List[AssetCandidate]:
        assets = [
            AssetCandidate("AGG", "ETF", 0.4, 0.03, 0.04, 0.95, 0.0003, 100e9, "Bonds", "iShares Core US Aggregate Bond ETF"),
            AssetCandidate("BND", "ETF", 0.42, 0.032, 0.041, 0.94, 0.0003, 95e9, "Bonds", "Vanguard Total Bond Market ETF"),
            AssetCandidate("VCSH", "ETF", 0.25, 0.025, 0.03, 0.93, 0.0004, 50e9, "Bonds", "Vanguard Short-Term Corporate Bond ETF"),
            AssetCandidate("MUB", "ETF", 0.35, 0.028, 0.038, 0.90, 0.0005, 30e9, "Bonds", "iShares National Muni Bond ETF"),
            AssetCandidate("VPU", "ETF", 0.5, 0.06, 0.12, 0.88, 0.001, 15e9, "Utilities", "Vanguard Utilities ETF"),
            AssetCandidate("XLRE", "ETF", 0.65, 0.07, 0.15, 0.89, 0.001, 12e9, "Real Estate", "Real Estate Select Sector SPDR"),
            AssetCandidate("VNQ", "ETF", 0.68, 0.072, 0.16, 0.91, 0.0012, 35e9, "Real Estate", "Vanguard Real Estate ETF"),
            AssetCandidate("DVY", "ETF", 0.75, 0.08, 0.14, 0.92, 0.0038, 20e9, "Dividend", "iShares Select Dividend ETF"),
            AssetCandidate("SCHD", "ETF", 0.72, 0.082, 0.13, 0.93, 0.0006, 45e9, "Dividend", "Schwab US Dividend Equity ETF"),
            AssetCandidate("VIG", "ETF", 0.78, 0.085, 0.135, 0.94, 0.0006, 70e9, "Dividend", "Vanguard Dividend Appreciation ETF"),
            AssetCandidate("XLP", "ETF", 0.55, 0.065, 0.11, 0.93, 0.001, 18e9, "Consumer Staples", "Consumer Staples Select Sector SPDR"),
            AssetCandidate("VDC", "ETF", 0.53, 0.063, 0.108, 0.92, 0.001, 8e9, "Consumer Staples", "Vanguard Consumer Staples ETF"),
            AssetCandidate("XLV", "ETF", 0.60, 0.09, 0.13, 0.94, 0.001, 40e9, "Healthcare", "Health Care Select Sector SPDR"),
            AssetCandidate("USMV", "ETF", 0.70, 0.085, 0.12, 0.95, 0.0015, 35e9, "Low Volatility", "iShares MSCI USA Min Vol Factor ETF"),
            AssetCandidate("SPLV", "ETF", 0.65, 0.075, 0.10, 0.93, 0.0025, 15e9, "Low Volatility", "Invesco S&P 500 Low Volatility ETF"),
            AssetCandidate("GLD", "ETF", 0.0, 0.05, 0.15, 0.96, 0.004, 70e9, "Commodities", "SPDR Gold Shares"),
            AssetCandidate("IAU", "ETF", 0.0, 0.048, 0.148, 0.95, 0.0025, 30e9, "Commodities", "iShares Gold Trust"),
            AssetCandidate("SLV", "ETF", 0.1, 0.06, 0.25, 0.90, 0.005, 10e9, "Commodities", "iShares Silver Trust"),
            AssetCandidate("TIP", "ETF", 0.45, 0.035, 0.06, 0.92, 0.0019, 25e9, "Inflation Protected", "iShares TIPS Bond ETF"),
            AssetCandidate("VTIP", "ETF", 0.30, 0.03, 0.04, 0.91, 0.0004, 8e9, "Inflation Protected", "Vanguard Short-Term Inflation-Protected Securities ETF")
        ]
        return assets
    
    def screen_assets(self, min_beta: float, max_beta: float, 
                     min_liquidity: float = 0.8) -> List[AssetCandidate]:
        
        screened = []
        for asset in self.asset_universe:
            if min_beta <= asset.beta <= max_beta and asset.liquidity_score >= min_liquidity:
                screened.append(asset)
        
        return sorted(screened, key=lambda x: (x.liquidity_score, -x.expense_ratio), reverse=True)


class PortfolioOptimizer:
    def __init__(self):
        self.risk_free_rate = 0.04
    
    def optimize_portfolio(self, assets: List[AssetCandidate], 
                         capital: float, 
                         target_return: Optional[float] = None,
                         max_position_size: float = 0.25) -> OptimizedPortfolio:
        
        n_assets = len(assets)
        
        returns = np.array([asset.expected_return for asset in assets])
        
        cov_matrix = self._estimate_covariance_matrix(assets)
        
        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        def portfolio_return(weights):
            return np.dot(weights, returns)
        
        def sharpe_ratio(weights):
            ret = portfolio_return(weights)
            vol = portfolio_volatility(weights)
            return -(ret - self.risk_free_rate) / vol if vol > 0 else 0
        
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        ]
        
        if target_return:
            constraints.append({
                'type': 'gte', 
                'fun': lambda w: portfolio_return(w) - target_return
            })
        
        bounds = [(0.0, max_position_size) for _ in range(n_assets)]
        
        initial_weights = np.array([1/n_assets] * n_assets)
        
        result = minimize(
            sharpe_ratio,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        optimal_weights = result.x
        
        allocations = {}
        for i, asset in enumerate(assets):
            if optimal_weights[i] > 0.01:
                allocations[asset.symbol] = float(optimal_weights[i])
        
        total_weight = sum(allocations.values())
        allocations = {k: v/total_weight for k, v in allocations.items()}
        
        final_weights = np.array([allocations.get(asset.symbol, 0) for asset in assets])
        portfolio_ret = portfolio_return(final_weights)
        portfolio_vol = portfolio_volatility(final_weights)
        portfolio_beta = self._calculate_portfolio_beta(assets, final_weights)
        sharpe = (portfolio_ret - self.risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0
        diversification = self._calculate_diversification_score(final_weights)
        expense_ratio = self._calculate_weighted_expense_ratio(assets, final_weights)
        
        return OptimizedPortfolio(
            allocations=allocations,
            expected_return=float(portfolio_ret),
            portfolio_volatility=float(portfolio_vol),
            portfolio_beta=float(portfolio_beta),
            sharpe_ratio=float(sharpe),
            diversification_score=float(diversification),
            total_expense_ratio=float(expense_ratio)
        )
    
    def _estimate_covariance_matrix(self, assets: List[AssetCandidate]) -> np.ndarray:
        n = len(assets)
        cov_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    cov_matrix[i, j] = assets[i].volatility ** 2
                else:
                    correlation = self._estimate_correlation(assets[i], assets[j])
                    cov_matrix[i, j] = correlation * assets[i].volatility * assets[j].volatility
        
        return cov_matrix
    
    def _estimate_correlation(self, asset1: AssetCandidate, 
                            asset2: AssetCandidate) -> float:
        
        if asset1.sector == asset2.sector:
            base_correlation = 0.7
        elif asset1.asset_type == asset2.asset_type:
            base_correlation = 0.5
        else:
            base_correlation = 0.3
        
        if asset1.asset_type == "Bonds" and asset2.asset_type == "Bonds":
            return 0.8
        elif asset1.asset_type == "Commodities" and asset2.asset_type == "Commodities":
            return 0.6
        elif (asset1.asset_type == "Bonds" and asset2.asset_type != "Bonds") or \
             (asset2.asset_type == "Bonds" and asset1.asset_type != "Bonds"):
            return 0.1
        
        return base_correlation + np.random.normal(0, 0.1)
    
    def _calculate_portfolio_beta(self, assets: List[AssetCandidate], 
                                 weights: np.ndarray) -> float:
        betas = np.array([asset.beta for asset in assets])
        return np.dot(weights, betas)
    
    def _calculate_diversification_score(self, weights: np.ndarray) -> float:
        non_zero_weights = weights[weights > 0.01]
        if len(non_zero_weights) == 0:
            return 0
        
        herfindahl_index = np.sum(non_zero_weights ** 2)
        
        diversification_score = 1 - herfindahl_index
        
        return diversification_score
    
    def _calculate_weighted_expense_ratio(self, assets: List[AssetCandidate], 
                                         weights: np.ndarray) -> float:
        expense_ratios = np.array([asset.expense_ratio for asset in assets])
        return np.dot(weights, expense_ratios)


class PortfolioConstructionAgent(BaseAgent):
    def __init__(self):
        super().__init__("PortfolioConstructionAgent", AgentType.PORTFOLIO_CONSTRUCTION)
        self.screener = AssetScreener()
        self.optimizer = PortfolioOptimizer()
    
    async def process(self, task: Task, context: InvestmentContext) -> Dict[str, Any]:
        self.logger.info(f"Processing portfolio construction task: {task.task_id}")
        
        audit_log = self.log_audit("PORTFOLIO_CONSTRUCTION_STARTED", context, {
            "task_id": task.task_id,
            "capital": context.capital_available,
            "risk_tolerance": context.risk_tolerance
        })
        task.audit_trail.append(audit_log)
        
        try:
            capital = context.capital_available
            risk_tolerance = context.risk_tolerance
            
            beta_constraints = self._determine_beta_constraints(task.payload, risk_tolerance)
            
            liquidity_requirement = task.payload.get("min_liquidity", 0.85)
            
            eligible_assets = self.screener.screen_assets(
                min_beta=beta_constraints["min"],
                max_beta=beta_constraints["max"],
                min_liquidity=liquidity_requirement
            )
            
            if not eligible_assets:
                raise ValueError("No assets found matching the specified criteria")
            
            target_return = self._determine_target_return(risk_tolerance)
            max_position = self._determine_max_position_size(risk_tolerance)
            
            optimized_portfolio = self.optimizer.optimize_portfolio(
                assets=eligible_assets,
                capital=capital,
                target_return=target_return,
                max_position_size=max_position
            )
            
            allocation_amounts = self._calculate_investment_amounts(
                optimized_portfolio.allocations, capital
            )
            
            asset_details = self._get_asset_details(eligible_assets, optimized_portfolio.allocations)
            
            result = {
                "allocation": optimized_portfolio.allocations,
                "investment_amounts": allocation_amounts,
                "asset_details": asset_details,
                "expected_returns": {
                    "portfolio_return": optimized_portfolio.expected_return,
                    "annualized_return": optimized_portfolio.expected_return * 100,
                    "dollar_return": capital * optimized_portfolio.expected_return
                },
                "risk_metrics": {
                    "portfolio_volatility": optimized_portfolio.portfolio_volatility,
                    "portfolio_beta": optimized_portfolio.portfolio_beta,
                    "sharpe_ratio": optimized_portfolio.sharpe_ratio,
                    "diversification_score": optimized_portfolio.diversification_score
                },
                "costs": {
                    "total_expense_ratio": optimized_portfolio.total_expense_ratio,
                    "annual_cost": capital * optimized_portfolio.total_expense_ratio
                },
                "eligible_assets_count": len(eligible_assets),
                "selected_assets_count": len(optimized_portfolio.allocations),
                "timestamp": datetime.now().isoformat()
            }
            
            large_position_size = any(w > 0.4 for w in optimized_portfolio.allocations.values())
            audit_log = self.log_audit("PORTFOLIO_CONSTRUCTION_COMPLETED", context, {
                "task_id": task.task_id,
                "assets_selected": len(optimized_portfolio.allocations),
                "portfolio_beta": optimized_portfolio.portfolio_beta,
                "large_position_size": large_position_size
            })
            task.audit_trail.append(audit_log)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in portfolio construction: {str(e)}")
            audit_log = self.log_audit("PORTFOLIO_CONSTRUCTION_FAILED", context, {
                "task_id": task.task_id,
                "error": str(e)
            })
            task.audit_trail.append(audit_log)
            raise
    
    def _determine_beta_constraints(self, payload: Dict[str, Any], 
                                   risk_tolerance: str) -> Dict[str, float]:
        
        if "min_beta" in payload and "max_beta" in payload:
            return {
                "min": payload["min_beta"],
                "max": payload["max_beta"]
            }
        
        constraints_map = {
            "conservative": {"min": 0.0, "max": 0.6},
            "moderate": {"min": 0.3, "max": 0.9},
            "aggressive": {"min": 0.7, "max": 1.3},
            "very_aggressive": {"min": 0.9, "max": 2.0}
        }
        
        return constraints_map.get(risk_tolerance, {"min": 0.3, "max": 0.9})
    
    def _determine_target_return(self, risk_tolerance: str) -> float:
        targets = {
            "conservative": 0.05,
            "moderate": 0.07,
            "aggressive": 0.10,
            "very_aggressive": 0.12
        }
        return targets.get(risk_tolerance, 0.07)
    
    def _determine_max_position_size(self, risk_tolerance: str) -> float:
        max_positions = {
            "conservative": 0.20,
            "moderate": 0.25,
            "aggressive": 0.35,
            "very_aggressive": 0.40
        }
        return max_positions.get(risk_tolerance, 0.25)
    
    def _calculate_investment_amounts(self, allocations: Dict[str, float], 
                                     capital: float) -> Dict[str, float]:
        amounts = {}
        for symbol, weight in allocations.items():
            amount = capital * weight
            amounts[symbol] = round(amount, 2)
        
        total_allocated = sum(amounts.values())
        if total_allocated < capital:
            largest_position = max(amounts.keys(), key=lambda k: amounts[k])
            amounts[largest_position] += round(capital - total_allocated, 2)
        
        return amounts
    
    def _get_asset_details(self, assets: List[AssetCandidate], 
                         allocations: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        details = {}
        
        for asset in assets:
            if asset.symbol in allocations:
                details[asset.symbol] = {
                    "name": asset.description,
                    "asset_type": asset.asset_type,
                    "sector": asset.sector,
                    "beta": asset.beta,
                    "expected_return": asset.expected_return,
                    "volatility": asset.volatility,
                    "liquidity_score": asset.liquidity_score,
                    "expense_ratio": asset.expense_ratio,
                    "weight": allocations[asset.symbol]
                }
        
        return details