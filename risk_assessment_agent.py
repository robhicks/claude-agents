import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from scipy import stats
from orchestrator import BaseAgent, AgentType, Task, InvestmentContext


@dataclass
class RiskMetrics:
    volatility: float
    beta: float
    sharpe_ratio: float
    max_drawdown: float
    value_at_risk: float
    conditional_value_at_risk: float
    correlation_risk: float
    liquidity_risk: float
    concentration_risk: float


@dataclass
class MarketRiskFactors:
    interest_rate_risk: float
    inflation_risk: float
    currency_risk: float
    geopolitical_risk: float
    regulatory_risk: float
    sector_risk: float


class RiskModel:
    def __init__(self):
        self.risk_free_rate = 0.04
        self.market_return = 0.10
        self.confidence_level = 0.95
    
    def calculate_volatility(self, returns: pd.Series) -> float:
        if len(returns) < 2:
            return 0.0
        return returns.std() * np.sqrt(252)
    
    def calculate_beta(self, asset_returns: pd.Series, market_returns: pd.Series) -> float:
        if len(asset_returns) < 2 or len(market_returns) < 2:
            return 1.0
        
        covariance = np.cov(asset_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return 1.0
        
        return covariance / market_variance
    
    def calculate_sharpe_ratio(self, returns: pd.Series, volatility: float) -> float:
        if volatility == 0:
            return 0.0
        
        mean_return = returns.mean() * 252
        excess_return = mean_return - self.risk_free_rate
        
        return excess_return / volatility
    
    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        if len(prices) < 2:
            return 0.0
        
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        
        return abs(drawdown.min())
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        if len(returns) < 2:
            return 0.0
        
        return -np.percentile(returns, (1 - confidence_level) * 100)
    
    def calculate_cvar(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        var = self.calculate_var(returns, confidence_level)
        
        tail_returns = returns[returns <= -var]
        
        if len(tail_returns) == 0:
            return var
        
        return -tail_returns.mean()
    
    def monte_carlo_simulation(self, initial_value: float, volatility: float, 
                             drift: float, days: int = 252, 
                             simulations: int = 1000) -> np.ndarray:
        
        dt = 1 / 252
        
        results = []
        
        for _ in range(simulations):
            prices = [initial_value]
            
            for _ in range(days):
                shock = np.random.normal(0, 1)
                drift_component = drift * dt
                diffusion_component = volatility * np.sqrt(dt) * shock
                new_price = prices[-1] * (1 + drift_component + diffusion_component)
                prices.append(new_price)
            
            results.append(prices)
        
        return np.array(results)


class StressTestEngine:
    def __init__(self):
        self.scenarios = {
            "market_crash": {
                "equity_shock": -0.30,
                "volatility_spike": 2.5,
                "correlation_increase": 0.3
            },
            "recession": {
                "equity_shock": -0.20,
                "credit_spread_widening": 0.02,
                "gdp_decline": -0.03
            },
            "inflation_spike": {
                "rate_increase": 0.02,
                "equity_shock": -0.10,
                "commodity_spike": 0.25
            },
            "geopolitical_crisis": {
                "equity_shock": -0.15,
                "volatility_spike": 2.0,
                "oil_spike": 0.30
            }
        }
    
    def run_stress_test(self, portfolio_value: float, 
                       asset_allocation: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        results = {}
        
        for scenario_name, shocks in self.scenarios.items():
            scenario_impact = self._calculate_scenario_impact(
                portfolio_value, asset_allocation, shocks
            )
            results[scenario_name] = scenario_impact
        
        return results
    
    def _calculate_scenario_impact(self, portfolio_value: float,
                                  asset_allocation: Dict[str, float],
                                  shocks: Dict[str, float]) -> Dict[str, float]:
        
        equity_exposure = asset_allocation.get("equities", 0)
        bond_exposure = asset_allocation.get("bonds", 0)
        commodity_exposure = asset_allocation.get("commodities", 0)
        
        equity_impact = equity_exposure * shocks.get("equity_shock", 0)
        
        if "rate_increase" in shocks:
            bond_duration = 5
            bond_impact = -bond_exposure * bond_duration * shocks["rate_increase"]
        else:
            bond_impact = bond_exposure * shocks.get("credit_spread_widening", 0) * -5
        
        commodity_impact = commodity_exposure * shocks.get("commodity_spike", 0)
        
        total_impact = equity_impact + bond_impact + commodity_impact
        
        new_portfolio_value = portfolio_value * (1 + total_impact)
        loss = portfolio_value - new_portfolio_value
        
        return {
            "portfolio_value": new_portfolio_value,
            "loss": loss,
            "percentage_loss": (loss / portfolio_value) * 100,
            "equity_impact": equity_impact,
            "bond_impact": bond_impact,
            "commodity_impact": commodity_impact
        }


class RiskAssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__("RiskAssessmentAgent", AgentType.RISK_ASSESSMENT)
        self.risk_model = RiskModel()
        self.stress_test_engine = StressTestEngine()
    
    async def process(self, task: Task, context: InvestmentContext) -> Dict[str, Any]:
        self.logger.info(f"Processing risk assessment task: {task.task_id}")
        
        audit_log = self.log_audit("RISK_ASSESSMENT_STARTED", context, {
            "task_id": task.task_id,
            "risk_tolerance": context.risk_tolerance
        })
        task.audit_trail.append(audit_log)
        
        try:
            risk_tolerance = context.risk_tolerance
            capital = context.capital_available
            
            simulated_data = self._generate_simulated_market_data()
            
            risk_metrics = self._calculate_risk_metrics(simulated_data)
            
            market_risk_factors = self._assess_market_risks()
            
            portfolio_allocation = self._suggest_allocation_based_on_risk(
                risk_tolerance, risk_metrics
            )
            
            stress_test_results = self.stress_test_engine.run_stress_test(
                capital, portfolio_allocation
            )
            
            risk_score = self._calculate_overall_risk_score(
                risk_metrics, market_risk_factors
            )
            
            recommendations = self._generate_risk_recommendations(
                risk_tolerance, risk_score, stress_test_results
            )
            
            result = {
                "metrics": {
                    "volatility": risk_metrics.volatility,
                    "beta": risk_metrics.beta,
                    "sharpe_ratio": risk_metrics.sharpe_ratio,
                    "max_drawdown": risk_metrics.max_drawdown,
                    "value_at_risk": risk_metrics.value_at_risk,
                    "conditional_value_at_risk": risk_metrics.conditional_value_at_risk
                },
                "market_risk_factors": {
                    "interest_rate_risk": market_risk_factors.interest_rate_risk,
                    "inflation_risk": market_risk_factors.inflation_risk,
                    "currency_risk": market_risk_factors.currency_risk,
                    "geopolitical_risk": market_risk_factors.geopolitical_risk
                },
                "stress_test_results": stress_test_results,
                "suggested_allocation": portfolio_allocation,
                "risk_score": risk_score,
                "level": self._categorize_risk_level(risk_score),
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
            high_risk_detected = risk_score > 0.7
            audit_log = self.log_audit("RISK_ASSESSMENT_COMPLETED", context, {
                "task_id": task.task_id,
                "risk_score": risk_score,
                "high_risk_detected": high_risk_detected,
                "stress_test_scenarios": len(stress_test_results)
            })
            task.audit_trail.append(audit_log)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in risk assessment: {str(e)}")
            audit_log = self.log_audit("RISK_ASSESSMENT_FAILED", context, {
                "task_id": task.task_id,
                "error": str(e)
            })
            task.audit_trail.append(audit_log)
            raise
    
    def _generate_simulated_market_data(self) -> Dict[str, pd.Series]:
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        
        market_returns = np.random.normal(0.0004, 0.01, 252)
        market_prices = pd.Series(100 * (1 + market_returns).cumprod(), index=dates)
        
        asset_returns = market_returns + np.random.normal(0.0001, 0.005, 252)
        asset_prices = pd.Series(50 * (1 + asset_returns).cumprod(), index=dates)
        
        return {
            "market_prices": market_prices,
            "market_returns": pd.Series(market_returns, index=dates),
            "asset_prices": asset_prices,
            "asset_returns": pd.Series(asset_returns, index=dates)
        }
    
    def _calculate_risk_metrics(self, data: Dict[str, pd.Series]) -> RiskMetrics:
        asset_returns = data["asset_returns"]
        market_returns = data["market_returns"]
        asset_prices = data["asset_prices"]
        
        volatility = self.risk_model.calculate_volatility(asset_returns)
        beta = self.risk_model.calculate_beta(asset_returns, market_returns)
        sharpe_ratio = self.risk_model.calculate_sharpe_ratio(asset_returns, volatility)
        max_drawdown = self.risk_model.calculate_max_drawdown(asset_prices)
        var = self.risk_model.calculate_var(asset_returns)
        cvar = self.risk_model.calculate_cvar(asset_returns)
        
        correlation_risk = self._calculate_correlation_risk(asset_returns, market_returns)
        liquidity_risk = self._calculate_liquidity_risk()
        concentration_risk = self._calculate_concentration_risk()
        
        return RiskMetrics(
            volatility=volatility,
            beta=beta,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            value_at_risk=var,
            conditional_value_at_risk=cvar,
            correlation_risk=correlation_risk,
            liquidity_risk=liquidity_risk,
            concentration_risk=concentration_risk
        )
    
    def _calculate_correlation_risk(self, asset_returns: pd.Series, 
                                   market_returns: pd.Series) -> float:
        if len(asset_returns) < 2 or len(market_returns) < 2:
            return 0.5
        
        correlation = asset_returns.corr(market_returns)
        
        if correlation > 0.8:
            return 0.9
        elif correlation > 0.6:
            return 0.7
        elif correlation > 0.4:
            return 0.5
        else:
            return 0.3
    
    def _calculate_liquidity_risk(self) -> float:
        return np.random.uniform(0.1, 0.3)
    
    def _calculate_concentration_risk(self) -> float:
        return np.random.uniform(0.1, 0.4)
    
    def _assess_market_risks(self) -> MarketRiskFactors:
        return MarketRiskFactors(
            interest_rate_risk=np.random.uniform(0.2, 0.5),
            inflation_risk=np.random.uniform(0.3, 0.6),
            currency_risk=np.random.uniform(0.1, 0.3),
            geopolitical_risk=np.random.uniform(0.2, 0.6),
            regulatory_risk=np.random.uniform(0.1, 0.4),
            sector_risk=np.random.uniform(0.2, 0.5)
        )
    
    def _suggest_allocation_based_on_risk(self, risk_tolerance: str,
                                         risk_metrics: RiskMetrics) -> Dict[str, float]:
        
        base_allocations = {
            "conservative": {"equities": 0.3, "bonds": 0.6, "cash": 0.1, "commodities": 0.0},
            "moderate": {"equities": 0.5, "bonds": 0.4, "cash": 0.05, "commodities": 0.05},
            "aggressive": {"equities": 0.7, "bonds": 0.2, "cash": 0.05, "commodities": 0.05},
            "very_aggressive": {"equities": 0.85, "bonds": 0.1, "cash": 0.025, "commodities": 0.025}
        }
        
        allocation = base_allocations.get(risk_tolerance, base_allocations["moderate"])
        
        if risk_metrics.volatility > 0.25:
            allocation["cash"] += 0.05
            allocation["equities"] -= 0.05
        
        if risk_metrics.beta > 1.2:
            allocation["bonds"] += 0.05
            allocation["equities"] -= 0.05
        
        total = sum(allocation.values())
        return {k: v/total for k, v in allocation.items()}
    
    def _calculate_overall_risk_score(self, risk_metrics: RiskMetrics,
                                     market_factors: MarketRiskFactors) -> float:
        
        metric_weights = {
            "volatility": 0.2,
            "beta": 0.15,
            "max_drawdown": 0.15,
            "value_at_risk": 0.15,
            "correlation_risk": 0.1,
            "liquidity_risk": 0.1,
            "concentration_risk": 0.15
        }
        
        normalized_volatility = min(risk_metrics.volatility / 0.4, 1.0)
        normalized_beta = min(abs(risk_metrics.beta - 1.0), 1.0)
        normalized_drawdown = min(risk_metrics.max_drawdown / 0.3, 1.0)
        normalized_var = min(risk_metrics.value_at_risk / 0.1, 1.0)
        
        metric_score = (
            normalized_volatility * metric_weights["volatility"] +
            normalized_beta * metric_weights["beta"] +
            normalized_drawdown * metric_weights["max_drawdown"] +
            normalized_var * metric_weights["value_at_risk"] +
            risk_metrics.correlation_risk * metric_weights["correlation_risk"] +
            risk_metrics.liquidity_risk * metric_weights["liquidity_risk"] +
            risk_metrics.concentration_risk * metric_weights["concentration_risk"]
        )
        
        market_score = (
            market_factors.interest_rate_risk * 0.2 +
            market_factors.inflation_risk * 0.2 +
            market_factors.currency_risk * 0.15 +
            market_factors.geopolitical_risk * 0.25 +
            market_factors.regulatory_risk * 0.1 +
            market_factors.sector_risk * 0.1
        )
        
        overall_score = metric_score * 0.6 + market_score * 0.4
        
        return min(overall_score, 1.0)
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        if risk_score < 0.3:
            return "low"
        elif risk_score < 0.5:
            return "moderate"
        elif risk_score < 0.7:
            return "high"
        else:
            return "very_high"
    
    def _generate_risk_recommendations(self, risk_tolerance: str,
                                      risk_score: float,
                                      stress_test_results: Dict) -> List[str]:
        recommendations = []
        
        if risk_score > 0.6 and risk_tolerance in ["conservative", "moderate"]:
            recommendations.append("Current market risk exceeds your risk tolerance - consider reducing exposure")
        
        worst_scenario = max(stress_test_results.items(), 
                           key=lambda x: x[1]["percentage_loss"])
        if worst_scenario[1]["percentage_loss"] > 20:
            recommendations.append(f"Stress test shows potential {worst_scenario[1]['percentage_loss']:.1f}% loss in {worst_scenario[0]} scenario")
        
        if risk_score > 0.5:
            recommendations.append("Consider implementing stop-loss orders to limit downside risk")
            recommendations.append("Increase portfolio diversification across uncorrelated assets")
        
        if risk_tolerance == "conservative" and risk_score > 0.4:
            recommendations.append("Recommend increasing allocation to fixed income securities")
        
        if risk_score < 0.3 and risk_tolerance in ["aggressive", "very_aggressive"]:
            recommendations.append("Risk levels are low - may consider increasing equity exposure for higher returns")
        
        return recommendations