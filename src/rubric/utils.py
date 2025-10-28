import json
import os
import re

from openai import AsyncOpenAI


def parse_json_to_dict(json_string: str) -> dict:
    """Parse JSON string with various formats (including markdown fences)."""
    cleaned = re.sub(r"^```json\s*|\s*```$", "", json_string.strip(), flags=re.IGNORECASE)

    cleaned = re.sub(r"^\s*json\s*", "", cleaned, flags=re.IGNORECASE)

    if cleaned and cleaned[0] != "{":
        brace = cleaned.find("{")
        if brace != -1:
            cleaned = cleaned[brace:]

    return json.loads(cleaned)


async def default_generate_fn(system_prompt: str, user_prompt: str) -> str:
    """Generate a response from the OpenAI API."""
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""
