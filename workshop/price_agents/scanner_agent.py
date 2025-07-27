# scanner_agent.py

import os
import json
from typing import List, Optional
from dotenv import load_dotenv

from agents import AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig
from price_agents.deals import ScrapedDeal, DealSelection
from price_agents.agent import Agent
from openai import OpenAI
import requests

class ScannerAgent(Agent):

    MODEL = "gemini-2.5-flash-lite"

    SYSTEM_PROMPT = """You identify and summarize the 5 most detailed deals from a list, by selecting deals
that have the most detailed, high quality description and the most clear price.
Respond strictly in JSON with no explanation, using this format. You should provide the price as
a number derived from the description. If the price of a deal isn't clear, do not include that deal
in your response. Most important is that you respond with the 5 deals that have the most detailed
product description with price. It's not important to mention the terms of the deal; most important
is a thorough description of the product. Be careful with products that are described as "$XXX off"
or "reduced by $XXX"—this isn't the actual price of the product. Only respond with products when
you are highly confident about the price.

{"deals": [
    {
        "product_description": "Your clearly expressed summary of the product in 3-4 sentences…",
        "price": 99.99,
        "url": "the url as provided"
    },
    …
]}"""

    USER_PROMPT_PREFIX = """Respond with the most promising 5 deals from this list, selecting those which
have the most detailed, high quality product description and a clear price that is greater than 0.
Respond strictly in JSON, and only JSON. You should rephrase the description to be a summary of the
product itself, not the terms of the deal. Remember to respond with a short paragraph of text in
the product_description field for each of the 5 items that you select. Be careful with products
that are described as "$XXX off" or "reduced by $XXX"—this isn't the actual price of the product.
Only respond with products when you are highly confident about the price.

Deals:
"""

    USER_PROMPT_SUFFIX = "\n\nStrictly respond in JSON and include exactly 5 deals, no more."

    name = "Scanner Agent"
    color = Agent.CYAN

    def __init__(self):
        self.MODEL = "gemini-2.5-flash-lite"
        self.log("Scanner Agent is initializing")
        load_dotenv()  # loads GEMINI_API_KEY into os.environ
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing in .env")

        # Create an OpenAI-compatible client that points at the Gemini endpoint:
        self.openai = OpenAI(
            api_key=gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        # Wrap it in the OpenAIChatCompletionsModel for convenience:
        self.model = OpenAIChatCompletionsModel(
            model=self.MODEL,
            openai_client=self.openai
        )
        # (we won't need Runner here, but if you did:)
        self.run_config = RunConfig(
            model=self.model,
            model_provider=self.openai,
            tracing_disabled=True
        )

        self.log("Scanner Agent is ready with Gemini Flash")

    def fetch_deals(self, memory) -> List[ScrapedDeal]:
        self.log("Scanner Agent is about to fetch deals from RSS feed")
        urls = [opp.deal.url for opp in memory]
        scraped = ScrapedDeal.fetch()
        new = [scr for scr in scraped if scr.url not in urls]
        self.log(f"Scanner Agent received {len(new)} new deals")
        return new

    def make_user_prompt(self, scraped: List[ScrapedDeal]) -> str:
        prompt = self.USER_PROMPT_PREFIX
        prompt += "\n\n".join(s.describe() for s in scraped)
        prompt += self.USER_PROMPT_SUFFIX
        return prompt


    def scan(self, memory: List[str] = []) -> Optional[DealSelection]:
        scraped = self.fetch_deals(memory)
        if not scraped:
            return None

        user_prompt = self.make_user_prompt(scraped)
        self.log("Scanner Agent is calling Gemini Flash")
        self.log("=== USER GEMINI REQUEST BEGIN ===\n" + user_prompt + "\n=== USER GEMINI REQUEST END ===")

        try:
            response = self.openai.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
                max_tokens=1000
            )
            raw = response.choices[0].message.content
        except Exception as e:
            self.log(f"❌ Gemini failed: {e}. Falling back to local Ollama.")
            # Send to Ollama instead:
            ollama_url = "http://127.0.0.1:11436/api/chat"
            ollama_model = "llama3.2"  # Or your preferred Ollama model
            ollama_payload = {
                "model": ollama_model,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            }
            try:
                ollama_resp = requests.post(ollama_url, json=ollama_payload)
                ollama_resp.raise_for_status()
                # You may need to adjust this based on Ollama's chat output structure:
                ollama_json = ollama_resp.json()
                raw = ollama_json.get("message", {}).get("content", "")
            except Exception as ollama_e:
                self.log(f"❌ Ollama fallback also failed: {ollama_e}")
                return None

        # Unwrap markdown (same as before)
        if raw.strip().startswith("```"):
            lines = raw.strip().splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw = "\n".join(lines)

        self.log("=== RAW RESPONSE BEGIN ===\n" + raw + "\n=== RAW RESPONSE END ===")
        try:
            parsed = json.loads(raw.strip())
            result = DealSelection(**parsed)
            result.deals = [d for d in result.deals if d.price > 0]
            self.log(f"Scanner Agent selected {len(result.deals)} deals with price>0")
            return result
        except Exception as e:
            self.log(f"❌ Failed to parse response: {e}")
            return None



    def test_scan(self, memory: List[str] = []) -> Optional[DealSelection]:
        # a stub for local testing if you need it
        sample = {
            "deals": [
                {
                    "product_description": "Sample product summary…",
                    "price": 123.45,
                    "url": "http://example.com"
                }
            ]
        }
        return DealSelection(**sample)
