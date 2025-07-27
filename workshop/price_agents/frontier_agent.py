import os
import re
import math
import json
from typing import List, Dict
from agents import AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
os.environ["OLLAMA_HOST"] = "127.0.0.1:11436"
import ollama
from datasets import load_dataset
import chromadb
from items import Item
from testing import Tester
from price_agents.agent import Agent
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class FrontierAgent(Agent):

    name = "Frontier Agent"
    color = Agent.YELLOW

    MODEL            = "gemini-2.5-chat"
    PREPROCESS_MODEL = "llama3.2"

    def __init__(self, collection):
        """
        Set up this instance by connecting to Gemini for pricing,
        to the Chroma Datastore, and to local Ollama for preprocessing.
        """
        self.MODEL = "gemini-2.5-flash"
        self.log("Scanner Agent is initializing")
        load_dotenv()  # loads GEMINI_API_KEY into os.environ
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing in .env")
        # use Google Gemini
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
        self.log("Frontier Agent is setting up with Gemini")

        # no longer import Ollama class; will invoke via ollama.run()
        self.collection = collection
        self.model      = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.log("Frontier Agent is ready")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        """
        Create context for the price prompt.
        """
        message = "Here are some similar items and their prices:\n\n"
        for similar, price in zip(similars, prices):
            message += f"{similar}\nPrice: ${price:.2f}\n\n"
        return message

    def preprocess(self, item: str) -> str:
        self.log(f"Calling Ollama locally with model={self.PREPROCESS_MODEL} on input: {repr(item[:120])}...")
        try:
            messages = [
                {'role': 'user', 'content': f"Rewrite this more concisely: {item}"}
            ]
            response = ollama.chat(model=self.PREPROCESS_MODEL, messages=messages)
            result = response['message']['content']
            self.log(f"Ollama output: {repr(result[:300])}")
            return result.strip()
        except Exception as e:
            self.log(f"Exception while calling Ollama: {e}")
            raise


    def estimate_price_ollama(description: str) -> float:
        prompt = (
            "You are an expert product pricer. Reply with only the numeric price in USD, no extra text.\n\n"
            f"Product: {description}"
        )
        response = ollama.chat(
            model="llama3:instruct",  # or whatever you have running locally
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response['message']['content'].strip()
        import re
        match = re.search(r"[-+]?\d*\.\d+|\d+", reply)
        return float(match.group()) if match else 0.0


    def find_similars(self, description: str):
        """
        1) Preprocess via Ollama
        2) Embed & search ChromaDB for top 5
        """
        self.log("Frontier Agent preprocessing with local Ollama")
        preprocessed = self.preprocess(description)

        self.log("Frontier Agent vectorizing with SentenceTransformer")
        vector = self.model.encode([preprocessed])

        self.log("Frontier Agent querying Chroma datastore")
        results = self.collection.query(
            query_embeddings=vector.astype(float).tolist(),
            n_results=5
        )
        documents = results['documents'][0]
        prices    = [m['price'] for m in results['metadatas'][0]]
        return documents, prices

    def get_price(self, text: str) -> float:
        """
        Extract a float from the assistant’s reply.
        """
        s = text.replace('$','').replace(',','')
        m = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(m.group()) if m else 0.0

    def price(self, description: str) -> float:
        """
        1) Find 5 similar products
        2) Call Gemini or DeepSeek for a price estimate
        3) If it fails, fallback to local Ollama
        """
        docs, prices = self.find_similars(description)

        self.log("Frontier Agent calling LLM for price estimate")
        messages = [
            {"role": "system",  "content": "You estimate prices. Reply with only the numeric price."},
            {"role": "user",    "content": self.make_context(docs, prices) + "\nEstimate price for:\n" + description}
        ]
        self.log(f"LLM raw request: {messages}")

        try:
            resp = self.openai.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                max_tokens=10
            )
            self.log(f"LLM raw resp: {resp}")
            reply = resp.choices[0].message.content
            # If we get no reply, raise error to trigger fallback
            if not reply:
                raise ValueError("No reply from Gemini")
            result = self.get_price(reply)
            self.log(f"Frontier Agent predicts ${result:.2f}")
            return result
        except Exception as e:
            self.log(f"❌ Gemini failed: {e}. Falling back to Ollama local model...")
            # Fallback to local Ollama inference
            prompt = (
                "You are an expert product pricer. Reply with only the numeric price in USD, no extra text.\n\n"
                f"Product: {description}"
            )
            try:
                response = ollama.chat(
                    model="llama3.2",  # Use your preferred Ollama model
                    messages=[{"role": "user", "content": prompt}]
                )
                reply = response['message']['content'].strip()
                match = re.search(r"[-+]?\d*\.\d+|\d+", reply)
                result = float(match.group()) if match else 0.0
                self.log(f"Ollama local predicts ${result:.2f}")
                return result
            except Exception as ollama_err:
                self.log(f"❌ Ollama fallback also failed: {ollama_err}")
                return 0.0

