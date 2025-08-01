from typing import Optional, List, Dict
from price_agents.agent import Agent as BaseAgent
from price_agents.deals import ScrapedDeal, DealSelection, Deal, Opportunity
from price_agents.scanner_agent import ScannerAgent
from price_agents.frontier_agent import FrontierAgent
from price_agents.specialist_agent import SpecialistAgent
from price_agents.messaging_agent import MessagingAgent
from agents import Agent, Runner, function_tool
import json
import asyncio
import os
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig
from agents.mcp import MCPServerStdio

sandbox_path = os.path.abspath(os.path.join(os.getcwd(), "sandbox"))
files_params = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path]}

planner = None
# Create an asynchronous OpenAI-style client for calling external APIs (e.g., Gemini)
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Define the model wrapper that communicates with the LLM using OpenAI-compatible schema
model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=external_client
)

# Runtime execution configuration (used to attach model, disable tracing, etc.)
config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True
)

@function_tool
def scan_the_internet_for_bargains() -> Dict:
    """
    This tool scans the internet for bargains and returns a curated list of top deals
    """
    planner.log("Autonomous Planning agent is calling scanner")
    results = planner.scanner.scan(memory=planner.memory)
    return results.model_dump() if results else {}

@function_tool
def estimate_true_value(description: str) -> Dict:
    """
    This tool estimates the true value of a product based on a text description of it
    """
    planner.log(f"Autonomous Planning agent is estimating value")
    estimate1 = planner.frontier.price(description)
    estimate2 = planner.specialist.price(description)
    estimate = (estimate1 + estimate2) / 2.0
    return {"description": description, "estimated_true_value": estimate}

@function_tool
def notify_user_of_deal(description: str, deal_price: float, estimated_true_value: float, url: str) -> Dict:
    """
    This tool notifies the user of a great deal, given a description of it, the price of the deal, and the estimated true value
    """
    if planner.opportunity:
        planner.log("Autonomous Planning agent is trying to notify the user a 2nd time; ignoring")
    else:
        planner.log("Autonomous Planning agent is notifying user")
        planner.messenger.notify(description, deal_price, estimated_true_value, url)
        deal = Deal(product_description=description, price=deal_price, url=url)
        discount = estimated_true_value - deal_price
        planner.opportunity = Opportunity(deal=deal, estimate=estimated_true_value, discount=discount)
    return {"notification_sent": "ok"}


class AutonomousPlanningAgent(BaseAgent):

    name = "Autonomous Planning Agent"
    color = BaseAgent.GREEN

    def __init__(self, collection):
        """
        Create instances of the 3 Agents that this planner coordinates across
        """
        self.log("Autonomous Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.frontier = FrontierAgent(collection)
        self.specialist = SpecialistAgent()
        self.messenger = MessagingAgent()
        self.memory = None
        self.opportunity = None
        self.log("Autonomous Planning Agent is ready")

    def get_tools(self):
        """
        Return the json for the tools to be used
        """
        return [scan_the_internet_for_bargains, estimate_true_value, notify_user_of_deal]

    system_message = """
    Your mission is to find great deals on bargain products using your tools, and notify the user when you find them
    by sending a push notification and by writing a file in markdown with a summary.

    IMPORTANT:
    - When outputting JSON (for any tool, API, or response), make sure all double-quote characters inside string values are escaped as \\" (for example, 14\\" instead of 14").
    - This is especially important for product descriptions or any text that might include inch symbols (").
    - Never output unescaped double quotes inside any JSON value.
    - Only output valid JSON that can be loaded with json.loads in Python.

    If you need to output markdown or other formats, keep those sections valid as well.
    """

    user_message = """
Your mission is to discover great deals on products. First you should use your tool to scan the internet for bargain deals.
Then for each deal, you should use your tool to estimate its true value - how much it's actually worth.
Finally, you should pick the single most compelling deal where the deal price is much lower than the estimated true value, 
and use your tool to send the user a push notification about that deal, and also use your tool to write this to the file sandbox/deals.md with a summary in markdown,
adding to the end of the file if it already exists.

You must only notify the user about one deal, and be sure to pick the most compelling deal, where the deal price is much lower than the estimated true value.
Only notify the user for the one best deal. Then just respond OK to indicate success."""
    
    messages = [{"role": "system", "content": system_message},{"role": "user", "content": user_message}]

    def run_async_task(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        else:
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)

    async def go(self):
        async with MCPServerStdio(params=files_params, client_session_timeout_seconds=60) as server:
            file_tools = await server.list_tools()
            agent = Agent(name="Planner", instructions=self.system_message, model=model, tools=self.get_tools(), mcp_servers=[server])
            reply = await Runner.run(agent, self.user_message, run_config=config)
        return reply
        

    def plan(self, memory: List[str] = []) -> Optional[Opportunity]:
        """
        Run the full workflow, providing the LLM with tools to surface scraped deals to the user
        :param memory: a list of URLs that have been surfaced in the past
        :return: an Opportunity if one was surfaced, otherwise None
        """
        self.log("Autonomous Planning Agent is kicking off a run")
        self.memory = memory
        self.opportunity = None
        global planner # TODO find a better way to do this without globals!!
        planner = self
        reply = self.run_async_task(self.go())
        self.log(f"Autonomous Planning Agent completed with: {reply}")
        return self.opportunity