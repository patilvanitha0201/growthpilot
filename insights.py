import anthropic
import os
import json
from dotenv import load_dotenv
from tools import TOOL_DEFINITIONS, dispatch_tool

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are GrowthPilot, an AI agent for B2B SaaS Customer Success teams.

Your job: assess a single account's churn risk and recommend one specific action.

You have tools to call. Use them to gather the context you need — don't guess.
Think step by step:
1. Get current health signals
2. Check score trajectory (is this a sustained decline or a one-week dip?)
3. Check support tickets if score is low
4. Check champion status and renewal urgency
5. Check last CSM touchpoint — did previous interventions work?

Once you have enough context, respond in EXACTLY this format:

RISK REASON:
[2 sentences max. Be specific — mention which signals are most alarming and the trajectory if declining.]

RECOMMENDED ACTION:
[1 sentence. Tell the CSM exactly what to do THIS WEEK. Be direct.]

REASONING TRAIL:
[2-3 sentences explaining what tools you called and why you reached this conclusion.]
"""


def get_insight(row) -> dict:
    """
    V2 Agent loop — Claude calls tools autonomously to assess account risk.
    Returns dict with risk_reason, recommended_action, reasoning_trail.
    """
    account_id = row["account_id"]

    messages = [
        {
            "role": "user",
            "content": f"Assess the churn risk for account ID: {account_id} — {row['company_name']}. "
                       f"Use your tools to gather what you need, then give me your assessment."
        }
    ]

    # ── Agentic loop ──────────────────────────────────────
    max_iterations = 6
    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages
        )

        # Claude is done — extract final text
        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
                    break
            return _parse_insight(final_text)

        # Claude wants to call tools
        if response.stop_reason == "tool_use":
            # Add Claude's response to messages
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     json.dumps(result)
                    })

            # Feed results back to Claude
            messages.append({"role": "user", "content": tool_results})

    # Fallback if loop maxes out
    return {
        "risk_reason":        "Agent loop exceeded maximum iterations.",
        "recommended_action": "Please review this account manually.",
        "reasoning_trail":    "Too many tool calls — check account data."
    }


def _parse_insight(raw: str) -> dict:
    """Parses Claude's structured response into dict."""
    risk_reason        = "Unable to generate risk reason."
    recommended_action = "Please review this account manually."
    reasoning_trail    = ""

    try:
        if "RISK REASON:" in raw and "RECOMMENDED ACTION:" in raw:
            parts              = raw.split("RECOMMENDED ACTION:")
            risk_reason        = parts[0].replace("RISK REASON:", "").strip()
            rest               = parts[1].split("REASONING TRAIL:")
            recommended_action = rest[0].strip()
            if len(rest) > 1:
                reasoning_trail = rest[1].strip()
    except Exception:
        pass

    return {
        "risk_reason":        risk_reason,
        "recommended_action": recommended_action,
        "reasoning_trail":    reasoning_trail
    }


def get_bulk_insights(df, top_n=5) -> dict:
    """Generates insights for top N at-risk accounts."""
    insights     = {}
    top_accounts = df.head(top_n)
    for _, row in top_accounts.iterrows():
        insights[row["account_id"]] = get_insight(row)
    return insights