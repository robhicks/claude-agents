from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import asyncio
import logging
import json
from uuid import uuid4


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class AgentType(Enum):
    MARKET_RESEARCH = "market_research"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    PORTFOLIO_CONSTRUCTION = "portfolio_construction"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AuditLog:
    timestamp: datetime
    action: str
    agent: str
    user_id: str
    details: Dict[str, Any]
    request_id: str
    compliance_flags: List[str] = field(default_factory=list)


@dataclass
class Task:
    task_id: str
    agent_type: AgentType
    priority: TaskPriority
    payload: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    parent_task_id: Optional[str] = None
    audit_trail: List[AuditLog] = field(default_factory=list)


@dataclass
class InvestmentContext:
    user_id: str
    risk_tolerance: str
    investment_horizon: str
    capital_available: float
    investment_goals: List[str]
    restrictions: List[str] = field(default_factory=list)
    regulatory_jurisdiction: str = "US"
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class InvestmentRecommendation:
    recommendation_id: str
    context: InvestmentContext
    portfolio: Dict[str, float]
    risk_metrics: Dict[str, float]
    expected_returns: Dict[str, float]
    confidence_score: float
    reasoning: List[str]
    data_sources: List[str]
    warnings: List[str]
    timestamp: datetime
    human_review_required: bool = True
    audit_trail: List[AuditLog] = field(default_factory=list)


class BaseAgent(ABC):
    def __init__(self, name: str, agent_type: AgentType):
        self.name = name
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.audit_logger = logging.getLogger(f"audit.{name}")
    
    @abstractmethod
    async def process(self, task: Task, context: InvestmentContext) -> Any:
        pass
    
    def log_audit(self, action: str, context: InvestmentContext, details: Dict[str, Any]):
        audit_entry = AuditLog(
            timestamp=datetime.now(),
            action=action,
            agent=self.name,
            user_id=context.user_id,
            details=details,
            request_id=context.request_id,
            compliance_flags=self._check_compliance_flags(details)
        )
        self.audit_logger.info(json.dumps({
            "timestamp": audit_entry.timestamp.isoformat(),
            "action": audit_entry.action,
            "agent": audit_entry.agent,
            "user_id": audit_entry.user_id,
            "request_id": audit_entry.request_id,
            "details": audit_entry.details,
            "compliance_flags": audit_entry.compliance_flags
        }))
        return audit_entry
    
    def _check_compliance_flags(self, details: Dict[str, Any]) -> List[str]:
        flags = []
        if details.get("high_risk_detected"):
            flags.append("HIGH_RISK_TRANSACTION")
        if details.get("large_position_size"):
            flags.append("CONCENTRATION_RISK")
        if details.get("restricted_security"):
            flags.append("RESTRICTED_SECURITY")
        return flags


class OrchestratorAgent:
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.logger = logging.getLogger(__name__)
        self.audit_logger = logging.getLogger("audit.orchestrator")
        self._setup_logging()
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        audit_handler = logging.FileHandler('audit.log')
        audit_handler.setLevel(logging.INFO)
        audit_formatter = logging.Formatter('%(message)s')
        audit_handler.setFormatter(audit_formatter)
        self.audit_logger.addHandler(audit_handler)
    
    def register_agent(self, agent: BaseAgent):
        self.agents[agent.agent_type] = agent
        self.logger.info(f"Registered agent: {agent.name} of type {agent.agent_type.value}")
    
    async def process_request(self, query: str, context: InvestmentContext) -> InvestmentRecommendation:
        self.logger.info(f"Processing request: {context.request_id}")
        
        self._log_audit("REQUEST_INITIATED", context, {"query": query})
        
        try:
            tasks = self._decompose_request(query, context)
            
            for task in tasks:
                self.task_queue.append(task)
            
            results = await self._execute_tasks(context)
            
            recommendation = await self._synthesize_results(results, context)
            
            self._log_audit("REQUEST_COMPLETED", context, {
                "recommendation_id": recommendation.recommendation_id,
                "confidence": recommendation.confidence_score
            })
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error processing request {context.request_id}: {str(e)}")
            self._log_audit("REQUEST_FAILED", context, {"error": str(e)})
            raise
    
    def _decompose_request(self, query: str, context: InvestmentContext) -> List[Task]:
        tasks = []
        
        market_research_task = Task(
            task_id=str(uuid4()),
            agent_type=AgentType.MARKET_RESEARCH,
            priority=TaskPriority.HIGH,
            payload={"query": query, "symbols": self._extract_symbols(query)},
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        tasks.append(market_research_task)
        
        sentiment_task = Task(
            task_id=str(uuid4()),
            agent_type=AgentType.SENTIMENT_ANALYSIS,
            priority=TaskPriority.MEDIUM,
            payload={"query": query, "symbols": self._extract_symbols(query)},
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        tasks.append(sentiment_task)
        
        risk_task = Task(
            task_id=str(uuid4()),
            agent_type=AgentType.RISK_ASSESSMENT,
            priority=TaskPriority.HIGH,
            payload={"risk_tolerance": context.risk_tolerance},
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            parent_task_id=market_research_task.task_id
        )
        tasks.append(risk_task)
        
        portfolio_task = Task(
            task_id=str(uuid4()),
            agent_type=AgentType.PORTFOLIO_CONSTRUCTION,
            priority=TaskPriority.CRITICAL,
            payload={"capital": context.capital_available},
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            parent_task_id=risk_task.task_id
        )
        tasks.append(portfolio_task)
        
        return tasks
    
    async def _execute_tasks(self, context: InvestmentContext) -> Dict[AgentType, Any]:
        results = {}
        
        sorted_tasks = sorted(self.task_queue, key=lambda t: t.priority.value, reverse=True)
        
        pending_tasks = []
        for task in sorted_tasks:
            if task.parent_task_id:
                parent_completed = any(
                    t.task_id == task.parent_task_id and t.status == TaskStatus.COMPLETED
                    for t in self.completed_tasks
                )
                if not parent_completed:
                    pending_tasks.append(task)
                    continue
            
            task.status = TaskStatus.IN_PROGRESS
            self.logger.info(f"Executing task {task.task_id} with agent {task.agent_type.value}")
            
            try:
                agent = self.agents.get(task.agent_type)
                if not agent:
                    raise ValueError(f"No agent registered for type {task.agent_type}")
                
                result = await agent.process(task, context)
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                results[task.agent_type] = result
                self.completed_tasks.append(task)
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                self.logger.error(f"Task {task.task_id} failed: {str(e)}")
        
        if pending_tasks:
            self.task_queue = pending_tasks
            additional_results = await self._execute_tasks(context)
            results.update(additional_results)
        else:
            self.task_queue = []
        
        return results
    
    async def _synthesize_results(self, results: Dict[AgentType, Any], 
                                 context: InvestmentContext) -> InvestmentRecommendation:
        
        portfolio = results.get(AgentType.PORTFOLIO_CONSTRUCTION, {})
        risk_metrics = results.get(AgentType.RISK_ASSESSMENT, {})
        market_data = results.get(AgentType.MARKET_RESEARCH, {})
        sentiment_data = results.get(AgentType.SENTIMENT_ANALYSIS, {})
        
        confidence_score = self._calculate_confidence(results)
        
        recommendation = InvestmentRecommendation(
            recommendation_id=str(uuid4()),
            context=context,
            portfolio=portfolio.get("allocation", {}),
            risk_metrics=risk_metrics.get("metrics", {}),
            expected_returns=portfolio.get("expected_returns", {}),
            confidence_score=confidence_score,
            reasoning=self._generate_reasoning(results),
            data_sources=self._collect_data_sources(results),
            warnings=self._generate_warnings(results, context),
            timestamp=datetime.now(),
            human_review_required=self._requires_human_review(confidence_score, context)
        )
        
        return recommendation
    
    def _calculate_confidence(self, results: Dict[AgentType, Any]) -> float:
        base_confidence = 0.5
        
        if AgentType.MARKET_RESEARCH in results:
            base_confidence += 0.2
        if AgentType.SENTIMENT_ANALYSIS in results:
            base_confidence += 0.15
        if AgentType.RISK_ASSESSMENT in results:
            base_confidence += 0.15
        
        return min(base_confidence, 0.95)
    
    def _generate_reasoning(self, results: Dict[AgentType, Any]) -> List[str]:
        reasoning = []
        
        if market_data := results.get(AgentType.MARKET_RESEARCH):
            reasoning.append(f"Market analysis indicates {market_data.get('trend', 'stable')} conditions")
        
        if sentiment := results.get(AgentType.SENTIMENT_ANALYSIS):
            reasoning.append(f"Sentiment analysis shows {sentiment.get('overall', 'neutral')} market sentiment")
        
        if risk := results.get(AgentType.RISK_ASSESSMENT):
            reasoning.append(f"Risk assessment identifies {risk.get('level', 'moderate')} risk level")
        
        return reasoning
    
    def _collect_data_sources(self, results: Dict[AgentType, Any]) -> List[str]:
        sources = []
        for agent_type, result in results.items():
            if isinstance(result, dict) and "sources" in result:
                sources.extend(result["sources"])
        return list(set(sources))
    
    def _generate_warnings(self, results: Dict[AgentType, Any], 
                          context: InvestmentContext) -> List[str]:
        warnings = []
        
        if context.risk_tolerance == "conservative":
            if risk := results.get(AgentType.RISK_ASSESSMENT):
                if risk.get("volatility", 0) > 0.2:
                    warnings.append("Portfolio volatility exceeds conservative risk tolerance")
        
        if context.regulatory_jurisdiction == "US":
            warnings.append("This recommendation is for informational purposes only and not financial advice")
        
        return warnings
    
    def _requires_human_review(self, confidence: float, context: InvestmentContext) -> bool:
        if confidence < 0.7:
            return True
        if context.capital_available > 100000:
            return True
        if context.risk_tolerance == "aggressive":
            return True
        return False
    
    def _extract_symbols(self, query: str) -> List[str]:
        import re
        pattern = r'\b[A-Z]{1,5}\b'
        potential_symbols = re.findall(pattern, query)
        return [s for s in potential_symbols if len(s) >= 2]
    
    def _log_audit(self, action: str, context: InvestmentContext, details: Dict[str, Any]):
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "agent": "orchestrator",
            "user_id": context.user_id,
            "request_id": context.request_id,
            "details": details
        }
        self.audit_logger.info(json.dumps(audit_entry))