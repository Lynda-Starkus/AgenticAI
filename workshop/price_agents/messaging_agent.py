import os
from price_agents.deals import Opportunity
import http.client
import urllib
from price_agents.agent import Agent
import requests

class MessagingAgent(Agent):

    name = "Messaging Agent"
    color = Agent.MAGENTA

    def __init__(self):
        self.log(f"Messaging Agent is initializing")
        self.pushover_user = os.getenv('PUSHOVER_USER', 'your-pushover-user-if-not-using-env')
        self.pushover_token = os.getenv('PUSHOVER_TOKEN', 'your-pushover-user-if-not-using-env')
        self.log("Messaging Agent has initialized Pushover (using Ollama Llama3.2 locally)")

    def push(self, text):
        self.log("Messaging Agent is sending a push notification")
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
          urllib.parse.urlencode({
            "token": self.pushover_token,
            "user": self.pushover_user,
            "message": text,
            "sound": "cashregister"
          }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()

    def alert(self, opportunity: Opportunity):
        text = f"Deal Alert! Price=${opportunity.deal.price:.2f}, "
        text += f"Estimate=${opportunity.estimate:.2f}, "
        text += f"Discount=${opportunity.discount:.2f} :"
        text += opportunity.deal.product_description[:10]+'... '
        text += opportunity.deal.url
        self.push(text)
        self.log("Messaging Agent has completed")

    def craft_message(self, description: str, deal_price: float, estimated_true_value: float) -> str:
        system_prompt = (
            "You are given details of a great deal on special offer, and you summarize it in a short message of 2-3 sentences."
        )
        user_prompt = (
            "Please summarize this great deal in 2-3 sentences.\n"
            f"Item Description: {description}\n"
            f"Offered Price: {deal_price}\n"
            f"Estimated true value: {estimated_true_value}\n\n"
            "Respond only with the 2-3 sentence message which will be used to alert the user about this deal."
        )
        payload = {
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        try:
            resp = requests.post("http://127.0.0.1:11436/api/chat", json=payload, timeout=20)
            resp.raise_for_status()
            result = resp.json()
            content = result.get("message", {}).get("content", "").strip()
            return content or "Great deal available!"
        except Exception as e:
            self.log(f"❌ Ollama message crafting failed: {e}")
            return "Great deal available!"

    def notify(self, description: str, deal_price: float, estimated_true_value: float, url: str):
        self.log("Messaging Agent is using Llama3.2 via Ollama to craft the message")
        text = self.craft_message(description, deal_price, estimated_true_value)
        self.push(text[:200]+"... "+url)
        self.log("Messaging Agent has completed")
