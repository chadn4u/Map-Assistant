from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import os
from dotenv import load_dotenv
from utils.gmaps import query_google_maps, get_direction

load_dotenv()

app = FastAPI()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


class MessageInput(BaseModel):
    prompt: str


@app.post("/send-message")
async def send_message(data: MessageInput):
    # Prompt utama ke Ollama
    prompt = f"""
You are an AI assistant that extracts structured data from user messages related to places, directions, or recommendations.  
Your task is to return a valid JSON object summarizing the user's intent, suitable for further automation.

🎯 OUTPUT FORMAT (JSON only):
{{
  "intent": "<one of: store_locator, map_place_search, place_recommendation, direction_request, general>",
  "query": "<what the user is searching for, like 'coffee shop', 'nearest ATM', etc.>",
  "store_name": "<store name if mentioned, e.g., 'Lotte Mart'>",
  "location": "<general location such as 'Bekasi', 'Jakarta', 'South Korea'>",
  "address": "<full address if mentioned>",
  "origin": "<starting point for direction_request. Leave empty if unclear or vague like 'my place', 'from here', 'tempat gw'>",
  "destination": "<destination for direction_request. If store_name is filled and destination is missing, use store_name as destination>",
  "raw_response": "<exactly repeat the original user message>",
  "needs_origin": <true | false>  // Only true if intent is 'direction_request' AND origin is unclear or missing
}}

⚠️ RULES:
- Output must be valid JSON only. No Markdown, no code block, no explanation.
- Include all fields in the correct order.
- Always use double quotes for string values.
- If a field is not applicable or unknown, return it as empty string "".
- If intent is 'direction_request':
  - If user origin is vague (e.g., 'my place', 'tempat gw', 'from here'), then:
    - set "origin" = ""
    - set "needs_origin" = true
  - If destination is empty but store_name is filled, use store_name as destination.

Now read the user message and return only the JSON object:

User: "{data.prompt}"
"""


    try:
        # Kirim ke Ollama (stream)
        ollama_response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt},
            stream=True
        )

        if ollama_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get response from Ollama")

        result = ""
        for line in ollama_response.iter_lines():
            if line:
                try:
                    line_json = json.loads(line.decode("utf-8"))
                    result += line_json.get("response", "")
                except Exception:
                    continue

        result = result.strip()
        print("OLLAMA FINAL RAW:", result)

        mcp_response = json.loads(result)
        intent = mcp_response.get("intent", "")
        gmap_result = {"message": "Intent not handled."}

        # Logic intent handling
        if intent in ["store_locator", "map_place_search", "place_recommendation"]:
            address = (
                mcp_response.get("address")
                or mcp_response.get("store_name")
                or mcp_response.get("query")
            )
            query = mcp_response.get("query", "")
            location = mcp_response.get("location", "")
            full_query = f"{query} in {location}".strip() if query else location

            gmap_result = query_google_maps(full_query) if full_query else {"message": "No address or query provided"}

        elif intent == "direction_request":
            origin = mcp_response.get("origin")
            destination = mcp_response.get("destination")
            
            if mcp_response.get("needs_origin") is True:
                gmap_result = {"message": "Origin Info not Found"}
            else:
                if origin and destination:
                    gmap_result = get_direction(origin, destination)
                else:
                    gmap_result = {"message": "Direction intent needs both origin and destination."}

        elif intent == "general":
            # Prompt natural response
            followup_response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": (
                        f"You are a helpful assistant specialized in location-related tasks. "
                        f"The user said: \"{data.prompt}\". "
                        "Reply naturally, but only explain what you can do related to places, store locator, map searches, and directions. "
                        "Do not mention setting reminders, sending emails, or other general assistant tasks."
                    )
                },
                stream=True
            )

            if followup_response.status_code == 200:
                followup_text = ""
                for line in followup_response.iter_lines():
                    if line:
                        try:
                            line_json = json.loads(line.decode("utf-8"))
                            followup_text += line_json.get("response", "")
                        except Exception:
                            continue

                gmap_result = {
                    "message": followup_text.strip()
                }
            else:
                gmap_result = {
                    "message": "Sorry, I couldn't respond naturally."
                }

        return {
            "llm_response": mcp_response,
            "gmap_result": gmap_result,
            "response_followup": generate_natural_response(mcp_response, gmap_result)
        }

    except json.JSONDecodeError as e:
        return {
            "error": "Failed to parse JSON from LLM.",
            "llm_raw": result,
            "reason": str(e)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def generate_natural_response(llm_response: dict, gmap_result):
    intent = llm_response.get("intent")
    needs_origin = llm_response.get("needs_origin", False)

    # --- CASE 1: Direction request missing origin
    if intent == "direction_request" and needs_origin:
        system_prompt = f"""
You are a friendly AI assistant that helps users with directions. The user asked for a direction, but they didn't clearly mention the starting point.

🧠 Your job is to write a natural-sounding follow-up message asking the user to specify their starting location.

Here’s the original message from the user:
"{llm_response.get('raw_response')}"

Write a friendly and casual follow-up, like:
"Sure, I can help! Just let me know where you're starting from, like 'Galaxy Bekasi' or 'my office'."

💬 Output format: Plain text only (no JSON, no markdown).
"""

    # --- CASE 2: Place list response (place_recommendation, store_locator, map_place_search)
    elif isinstance(gmap_result, list) and intent in [
        "place_recommendation", "store_locator", "map_place_search"
    ]:
        system_prompt = f"""
You are a helpful assistant. Your job is to create a friendly and natural response for a user based on structured location data.

Here is the user's intent: {llm_response.get("intent")}
Here is the structured query: {llm_response}
Here is the data retrieved from Google Maps: {gmap_result}

🧠 Instructions:
- If gmap_result is a list of places (up to 5), then show ALL of them.
- Use a friendly and helpful tone.
- For each place, mention:
    - Place name
    - Address
    - A clickable link from the "maps_url" field
- Number the list (1., 2., etc.)
- Always thank the user at the end.

Output should be plain text only (no markdown or JSON).

Now write your answer:
"""
    # --- CASE 3: Direction OK (show info)
    elif intent == "direction_request" and isinstance(gmap_result, dict) and gmap_result.get("summary"):
        system_prompt = f"""
You are a helpful assistant. Your job is to generate a friendly and clear response based on Google Maps directions.

Here is the user's query: {llm_response.get("raw_response")}
Here is the directions data: {gmap_result}

🧭 Instructions:
- Mention the start and end address clearly.
- State distance and estimated time.
- Mention the route summary (e.g., via Toll XYZ).
- End the message with a friendly encouragement like "Have a safe trip!" or similar and add clickable link from the "maps_url" field.

Output should be plain text only (no markdown or JSON).
"""
    # --- CASE 4: Fallback generic
    else:
        return (
            "Terima kasih! Aku bisa bantu cari tempat, arah, dan rekomendasi di sekitar kamu. "
            "Coba kasih tahu kamu mau cari apa ya 😊"
        )

    # Kirim ke Ollama
    ollama_resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": system_prompt},
        stream=True
    )

    if ollama_resp.status_code != 200:
        return "Maaf, sistem sedang sibuk. Coba lagi sebentar ya."

    response_text = ""
    for line in ollama_resp.iter_lines():
        if line:
            try:
                chunk = json.loads(line.decode("utf-8"))
                response_text += chunk.get("response", "")
            except Exception:
                continue

    return response_text.strip()
