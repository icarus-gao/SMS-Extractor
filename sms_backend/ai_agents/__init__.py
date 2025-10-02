"""
AI Agent System for SMS Extractor
Advanced intelligent agents for automated research tasks
"""

from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
from openai import OpenAI
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, name: str, description: str, model: str = "gpt-4"):
        self.name = name
        self.description = description
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_history = []
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return result"""
        pass
    
    def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """Send a message and get response"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            *self.conversation_history,
            {"role": "user", "content": message}
        ]
        
        if context:
            messages.insert(1, {
                "role": "system", 
                "content": f"Context: {json.dumps(context)}"
            })
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message.content
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        # Keep only last 10 messages to avoid token limits
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return assistant_message
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


class ExtractionAgent(BaseAgent):
    """Intelligent agent for automated feature extraction"""
    
    def __init__(self):
        super().__init__(
            name="Extraction Agent",
            description="Intelligent agent for analyzing papers and extracting features",
            model=os.getenv("OPENAI_MODEL", "gpt-4")
        )
    
    def get_system_prompt(self) -> str:
        return """You are an expert research assistant specialized in systematic literature reviews.
Your task is to analyze academic papers and extract relevant information according to specified schemas.
You should:
1. Carefully read and understand the paper content
2. Identify relevant information for each requested field
3. Extract data accurately and consistently
4. Handle missing or unclear information appropriately
5. Provide structured JSON responses

Always be precise, thorough, and maintain high quality standards."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extraction request
        
        Args:
            input_data: {
                "paper_text": str,
                "fields": List[str],
                "instructions": Optional[str]
            }
        
        Returns:
            Dict with extracted data
        """
        paper_text = input_data.get("paper_text", "")
        fields = input_data.get("fields", [])
        instructions = input_data.get("instructions", "")
        
        prompt = f"""Please extract the following information from this paper:

Fields to extract: {', '.join(fields)}

{instructions}

Paper content:
{paper_text[:8000]}  # Limit to avoid token limits

Provide your response as a JSON object with each field as a key."""
        
        response = self.chat(prompt)
        
        try:
            # Try to parse JSON from response
            extracted_data = json.loads(response)
        except json.JSONDecodeError:
            # If not valid JSON, wrap it
            extracted_data = {"raw_response": response}
        
        return {
            "status": "success",
            "data": extracted_data,
            "timestamp": datetime.now().isoformat()
        }
    
    def suggest_fields(self, paper_text: str) -> List[str]:
        """Suggest relevant fields to extract based on paper content"""
        prompt = f"""Based on this academic paper, suggest 8-12 relevant fields that should be extracted for a systematic review.

Paper excerpt:
{paper_text[:3000]}

Return a JSON array of field names (e.g., ["study_design", "sample_size", "intervention", ...])"""
        
        response = self.chat(prompt)
        
        try:
            fields = json.loads(response)
            return fields if isinstance(fields, list) else []
        except:
            return []


class ConversationAgent(BaseAgent):
    """Conversational agent for natural language queries"""
    
    def __init__(self, project_context: Optional[Dict] = None):
        super().__init__(
            name="Research Assistant",
            description="Conversational AI for answering questions about your research project",
            model=os.getenv("OPENAI_MODEL", "gpt-4")
        )
        self.project_context = project_context or {}
    
    def get_system_prompt(self) -> str:
        return """You are a helpful research assistant for the SMS Extractor systematic review tool.
You help researchers with:
- Understanding their data and results
- Generating reports and summaries
- Providing insights and recommendations
- Answering questions about their projects
- Suggesting next steps in their research workflow

Be friendly, professional, and focused on helping with systematic reviews and meta-analyses."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a conversational query"""
        query = input_data.get("query", "")
        context = input_data.get("context", self.project_context)
        
        response = self.chat(query, context=context)
        
        return {
            "status": "success",
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_project(self, project_data: Dict) -> str:
        """Provide analysis and insights about a project"""
        prompt = f"""Analyze this research project and provide insights:

Project: {project_data.get('name')}
Papers: {project_data.get('paper_count')} papers
Extractions: {project_data.get('extraction_count')} completed
Feature Groups: {project_data.get('groups', [])}

Provide:
1. Summary of project status
2. Data quality assessment
3. Recommendations for next steps
4. Potential insights or patterns"""
        
        return self.chat(prompt)


class WorkflowAgent(BaseAgent):
    """Agent for workflow automation and task management"""
    
    def __init__(self):
        super().__init__(
            name="Workflow Agent",
            description="Intelligent automation for research workflows",
            model=os.getenv("OPENAI_MODEL", "gpt-4")
        )
    
    def get_system_prompt(self) -> str:
        return """You are an intelligent workflow automation assistant.
You help researchers automate their systematic review process by:
- Suggesting optimal extraction strategies
- Detecting data quality issues
- Recommending automation opportunities
- Planning batch operations
- Identifying missing or incomplete data

Provide actionable, step-by-step recommendations."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process workflow automation request"""
        task_type = input_data.get("task_type")
        data = input_data.get("data", {})
        
        if task_type == "suggest_workflow":
            return self.suggest_workflow(data)
        elif task_type == "detect_issues":
            return self.detect_issues(data)
        elif task_type == "plan_batch":
            return self.plan_batch_operation(data)
        else:
            return {"status": "error", "message": "Unknown task type"}
    
    def suggest_workflow(self, project_data: Dict) -> Dict[str, Any]:
        """Suggest optimal workflow for a project"""
        prompt = f"""Based on this project setup, suggest an optimal workflow:

Papers: {project_data.get('paper_count')}
Feature Groups: {len(project_data.get('groups', []))}
Status: {project_data.get('status')}

Suggest:
1. Order of operations
2. Batch processing strategy
3. Quality control steps
4. Estimated timeline"""
        
        response = self.chat(prompt)
        
        return {
            "status": "success",
            "workflow": response,
            "timestamp": datetime.now().isoformat()
        }
    
    def detect_issues(self, extraction_data: List[Dict]) -> Dict[str, Any]:
        """Detect quality issues in extraction data"""
        prompt = f"""Analyze these extraction results for quality issues:

Number of extractions: {len(extraction_data)}
Sample data: {json.dumps(extraction_data[:5], indent=2)}

Identify:
1. Missing or incomplete data
2. Inconsistencies
3. Potential errors
4. Recommendations for improvement"""
        
        response = self.chat(prompt)
        
        return {
            "status": "success",
            "issues": response,
            "timestamp": datetime.now().isoformat()
        }
    
    def plan_batch_operation(self, operation_data: Dict) -> Dict[str, Any]:
        """Plan and optimize batch operations"""
        prompt = f"""Plan this batch operation:

Operation: {operation_data.get('operation')}
Items: {operation_data.get('item_count')}
Constraints: {operation_data.get('constraints', {})}

Provide:
1. Execution plan
2. Resource requirements
3. Estimated time
4. Risk mitigation"""
        
        response = self.chat(prompt)
        
        return {
            "status": "success",
            "plan": response,
            "timestamp": datetime.now().isoformat()
        }


class AgentOrchestrator:
    """Orchestrates multiple agents for complex tasks"""
    
    def __init__(self):
        self.agents = {
            "extraction": ExtractionAgent(),
            "conversation": ConversationAgent(),
            "workflow": WorkflowAgent()
        }
    
    def get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Get an agent by type"""
        return self.agents.get(agent_type)
    
    def route_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate agent"""
        agent_type = request.get("agent_type")
        
        if agent_type not in self.agents:
            return {
                "status": "error",
                "message": f"Unknown agent type: {agent_type}"
            }
        
        agent = self.agents[agent_type]
        return agent.process(request.get("data", {}))
    
    def chat_with_agent(self, agent_type: str, message: str, context: Optional[Dict] = None) -> str:
        """Send a chat message to an agent"""
        agent = self.get_agent(agent_type)
        if not agent:
            return f"Error: Agent '{agent_type}' not found"
        
        return agent.chat(message, context=context)
