import json
import logging
import re
from typing import Dict, Any, Optional
from groq import Groq
from backend.app.config import settings

logger = logging.getLogger(__name__)

TASK_PROMPTS = {
    "financial_news": (
        "TASK FOCUS: Financial News Simplification.\n"
        "Transform complex, dense, and jargon-heavy financial reporting into clear, accessible, and reader-friendly insights.\n"
        "Preserve factual numerical figures, percentages, and dates, but translate their practical meaning so any non-expert instantly understands the core message."
    ),
    "market_event": (
        "TASK FOCUS: Market Event Explanation.\n"
        "Analyze this specific market catalyst, earnings surprise, trading anomaly, rate decision, or geopolitical trigger.\n"
        "Explain the causal mechanism: what triggered the event, which sectors or assets reacted most sharply, and what forward-looking signals market participants are monitoring."
    ),
    "economic": (
        "TASK FOCUS: Economic News Summarization.\n"
        "Deconstruct macroeconomic developments involving the Federal Reserve, global central banks, interest rate trajectories, inflation indicators (CPI, PPI, Core PCE), GDP growth, and employment data.\n"
        "Explain the macroeconomic transmission mechanism: how central bank actions and policy shifts directly filter down to everyday loan rates, mortgage costs, business hiring, and consumer purchasing power."
    ),
    "business": (
        "TASK FOCUS: Business News Interpretation.\n"
        "Interpret corporate developments, strategic reorganizations, earnings reports, Capital Expenditures (CapEx), revenue margins, cash reserves, and mergers & acquisitions (M&A).\n"
        "Highlight operational health, strategic moat, enterprise risk factors, and long-term shareholder value."
    ),
    "jargon_free": (
        "TASK FOCUS: Jargon-Free Content Generation.\n"
        "Strip away opaque Wall Street slang, financial acronyms, and institutional terminology.\n"
        "Use vivid, intuitive real-world analogies (e.g. comparing market liquidity to water pressure, balance sheets to family household budgets) so that any beginner grasps the concept effortlessly without confusion."
    )
}

PERSONA_PROMPTS = {
    "retail_investor": (
        "You are FinNews AI specializing for Everyday Retail Investors. "
        "Explain how the news impacts individual stock portfolios, 401(k) / retirement funds, sector rotations, and personal wealth. "
        "Avoid institutional trading jargon and provide clear, actionable insights for long-term investors."
    ),
    "student": (
        "You are FinNews AI serving as an inspiring Finance Professor & Mentor for college students. "
        "Break down macroeconomic principles, interest rate dynamics, central bank mechanics, and corporate valuation theories in intuitive educational terms. "
        "Use clear analogies, define financial formulas conceptually, and help the student connect headline news to academic principles."
    ),
    "professional": (
        "You are FinNews AI delivering a high-velocity 60-Second Executive Briefing for busy executives, directors, and managers. "
        "Focus on bottom-line business implications, capital allocation (CapEx), operating margins, enterprise risk exposure, counterparty risk, and strategic boardroom takeaways. "
        "Provide razor-sharp, zero-fluff bullet points."
    ),
    "volatility": (
        "You are FinNews AI High-Volatility & Breaking Risk Intelligence. "
        "Analyze sudden market drawdowns, volatility spikes (VIX), liquidation cascades, order-book liquidity shifts, and major economic surprises. "
        "Deliver rapid catalyst breakdowns, immediate risk thresholds, and critical support levels."
    )
}

COMMON_FINANCIAL_JARGON = {
    "basis points": "A standard unit of measure in finance where 1 basis point equals 0.01% (so 25 basis points = 0.25%).",
    "quantitative tightening": "A central bank policy where it reduces the money supply and shrinks its balance sheet to tame inflation.",
    "quantitative easing": "A central bank policy where it injects liquidity into the banking system by purchasing government bonds.",
    "yield curve": "A chart graphing interest rates on government bonds across different maturities; an inverted curve often signals recession fears.",
    "inverted yield curve": "A rare market condition where short-term interest rates are higher than long-term rates, historically preceding recessions.",
    "capex": "Capital Expenditures — funds used by a company to acquire, upgrade, and maintain physical assets such as data centers and AI chips.",
    "free cash flow": "The actual cash a company generates after accounting for cash outflows that support operations and maintain capital assets.",
    "liquidations": "The automated closing of leveraged trading positions by an exchange when a trader's margin balance falls below required levels.",
    "disinflation": "A slowdown in the inflation rate (prices are still rising, but at a slower pace).",
    "stagflation": "A toxic economic condition marked by stagnant economic growth, high unemployment, and persistently high inflation.",
    "high-bandwidth memory": "Ultra-fast, stacked computer memory architecture crucial for powering modern AI accelerators and graphics processors.",
    "dual mandate": "The statutory objectives of the Federal Reserve: pursuing maximum employment while maintaining price stability (low inflation).",
    "hawkish": "An economic policy stance prioritizing fighting inflation, typically by raising or holding interest rates high.",
    "dovish": "A policy stance favoring lower interest rates to encourage economic borrowing, investment, and job creation.",
    "ebitda": "Earnings Before Interest, Taxes, Depreciation, and Amortization — an indicator of pure operational profitability.",
    "p/e ratio": "Price-to-Earnings Ratio — measuring how much investors are willing to pay for every dollar of annual company earnings.",
    "bear market": "A prolonged period of falling asset prices, typically defined as a decline of 20% or more from recent highs.",
    "bull market": "A sustained market upswing characterized by widespread investor confidence and rising stock valuations.",
    "margin call": "A broker's demand that an investor deposit additional money or securities to bring a margin account up to minimum required value.",
    "etf": "Exchange-Traded Fund — a marketable security tracking an index, sector, commodity, or bundle of assets that trades like a common stock."
}

class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL or "llama-3.3-70b-versatile"
        self._client: Optional[Groq] = None

    def _get_client(self) -> Optional[Groq]:
        key = settings.GROQ_API_KEY
        if key and len(key.strip()) > 10:
            return Groq(api_key=key.strip())
        return None

    def is_configured(self) -> bool:
        return bool(settings.GROQ_API_KEY and len(settings.GROQ_API_KEY.strip()) > 10)

    async def simplify_article(
        self, 
        title: str, 
        content: str, 
        persona: str = "retail_investor",
        mode: str = "financial_news",
        article_id: str = "custom"
    ) -> Dict[str, Any]:
        """
        Uses Groq's high-speed LLM (LLaMA 3.3-70B Versatile) to produce a structured, simplified summary.
        Falls back to intelligent algorithmic generation if API key is not configured or unavailable.
        """
        client = self._get_client()

        if client:
            try:
                return await self._call_groq(client, title, content, persona, mode, article_id)
            except Exception as e:
                logger.warning(f"Groq API call failed: {e}. Falling back to intelligent heuristic summarization engine.")

        # Heuristic / Fallback engine
        return self._generate_fallback_summary(title, content, persona, mode, article_id)

    async def _call_groq(
        self, 
        client: Groq, 
        title: str, 
        content: str, 
        persona: str,
        mode: str,
        article_id: str
    ) -> Dict[str, Any]:
        task_instruction = TASK_PROMPTS.get(mode, TASK_PROMPTS["financial_news"])
        persona_role = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["retail_investor"])
        
        system_prompt = f"""
You are FinNews AI, an advanced AI-powered financial news simplification platform powered by Groq LLaMA 3.3-70B Versatile.

{task_instruction}

AUDIENCE LENS:
{persona_role}

You MUST respond strictly with a valid JSON object matching this schema:
{{
  "executive_summary": "2 to 3 concise, clear sentences in plain English explaining the big picture.",
  "what_happened": "A factual, simplified breakdown of the core event without dense market jargon.",
  "why_it_matters": "Real-world impact explaining how this affects individuals, investors, or the broader economy.",
  "jargon_demystified": {{
    "Term Name": "Clear plain English explanation in 1 sentence",
    "Another Term": "Clear plain English explanation"
  }},
  "key_takeaways": [
    "High-impact key takeaway 1",
    "High-impact key takeaway 2",
    "High-impact key takeaway 3"
  ],
  "market_sentiment": "Bullish" | "Bearish" | "Neutral",
  "sentiment_score": 0.85,
  "read_time": "1 min read"
}}

Guidelines:
- Identify and demystify at least 2 relevant financial or economic terms in 'jargon_demystified'.
- Ensure sentiment is accurate: positive market news is 'Bullish', negative/warning news is 'Bearish', mixed/policy news is 'Neutral'.
- Keep all explanations crystal clear, engaging, and jargon-free while preserving critical financial facts.
"""

        user_prompt = f"""
Article Title: {title}
Article Content / Excerpt:
{content[:2500]}

Simplify this article now following the specified JSON format.
"""

        candidate_models = [
            settings.GROQ_MODEL,
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama3-70b-8192",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b"
        ]
        # Deduplicate while preserving order
        candidate_models = [m for i, m in enumerate(candidate_models) if m and m not in candidate_models[:i]]

        raw_response = None
        last_err = None
        used_model = candidate_models[0]

        for model_name in candidate_models:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=1024
                )
                raw_response = completion.choices[0].message.content
                if raw_response:
                    used_model = model_name
                    self.model = model_name
                    break
            except Exception as err:
                last_err = err
                logger.warning(f"Groq model {model_name} failed: {err}. Trying next candidate...")

        if not raw_response:
            raise last_err or Exception("All Groq model attempts failed.")

        # Clean JSON if wrapped in markdown code blocks
        clean_text = raw_response.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        data = json.loads(clean_text)

        return {
            "article_id": article_id,
            "persona": persona,
            "mode": mode,
            "model_used": used_model,
            "executive_summary": data.get("executive_summary", "Summary unavailable."),
            "what_happened": data.get("what_happened", ""),
            "why_it_matters": data.get("why_it_matters", ""),
            "jargon_demystified": data.get("jargon_demystified", {}),
            "key_takeaways": data.get("key_takeaways", []),
            "market_sentiment": data.get("market_sentiment", "Neutral"),
            "sentiment_score": float(data.get("sentiment_score", 0.5)),
            "read_time": data.get("read_time", "1 min read")
        }

    def _generate_fallback_summary(
        self, 
        title: str, 
        content: str, 
        persona: str = "retail_investor",
        mode: str = "financial_news",
        article_id: str = "custom"
    ) -> Dict[str, Any]:
        """
        Provides high-fidelity, scenario-tailored simplified summaries when Groq API key is pending or network unavailable.
        """
        title_lower = title.lower()
        content_lower = content.lower()

        # Extract identified jargon terms from the text
        detected_jargon: Dict[str, str] = {}
        for term, definition in COMMON_FINANCIAL_JARGON.items():
            if term in title_lower or term in content_lower:
                detected_jargon[term.title()] = definition

        if not detected_jargon:
            detected_jargon["Inflation"] = "The rate at which prices for goods and services rise, reducing purchasing power."
            detected_jargon["Market Capitalization"] = "The total market value of a company's outstanding shares of stock."

        # Detect Sentiment
        bullish_words = ["rally", "surge", "gains", "beat", "higher", "record", "advance", "growth", "cut rates", "rebound"]
        bearish_words = ["liquidations", "crash", "plunge", "loss", "recession", "drawdown", "fall", "pressure", "delinquency"]

        bull_count = sum(1 for w in bullish_words if w in title_lower or w in content_lower)
        bear_count = sum(1 for w in bearish_words if w in title_lower or w in content_lower)

        if bull_count > bear_count:
            sentiment = "Bullish"
            sentiment_score = min(0.6 + (bull_count * 0.1), 0.95)
        elif bear_count > bull_count:
            sentiment = "Bearish"
            sentiment_score = max(0.4 - (bear_count * 0.1), 0.15)
        else:
            sentiment = "Neutral"
            sentiment_score = 0.50

        # Mode and Persona-tailored framing
        mode_prefix = {
            "financial_news": "Financial Simplification",
            "market_event": "Market Event Analysis",
            "economic": "Macroeconomic Overview",
            "business": "Business Intelligence",
            "jargon_free": "Plain-English Translation"
        }.get(mode, "Financial Simplification")

        if persona == "student":
            exec_summary = (
                f"[{mode_prefix}] In this economic event, policymakers and markets responded directly to changes in macroeconomic indicators. "
                f"Understanding this headline helps demonstrate how interest rates, corporate balance sheets, and real inflation intersect."
            )
            what_happened = (
                f"The core event centers on '{title}'. Rather than focusing on complex terminology, the central theme is how supply, "
                f"capital demand, and market expectations dictate valuations across industries."
            )
            why_it_matters = (
                "For students of economics and business, this illustrates the transmission mechanism: how central bank or corporate decisions "
                "ripple from institutional balance sheets down to everyday consumer prices, loan rates, and hiring plans."
            )
            takeaways = [
                "Economic shifts directly influence borrowing costs and institutional risk appetite.",
                "Market pricing reflects forward expectations rather than solely backward-looking metrics.",
                "Mastering financial vocabulary reveals the underlying mechanics behind global market stability."
            ]
        elif persona == "professional":
            exec_summary = (
                f"[{mode_prefix}] Executive Briefing: '{title}'. Key operational drivers highlight shifting capital allocations, "
                f"margin considerations, and evolving regulatory/macro risk profiles."
            )
            what_happened = (
                f"Market desks reported decisive movements tied to recent headline disclosures. "
                f"Organizations are recalibrating budgets and risk exposure to accommodate these baseline shifts."
            )
            why_it_matters = (
                "Directly impacts corporate cash reserves, strategic borrowing facilities, vendor contracts, "
                "and enterprise hurdle rates for near-term capital projects."
            )
            takeaways = [
                "Strategic hurdle rates and budget forecasts should account for current liquidity trends.",
                "Competitive dynamics are accelerating capital redeployment toward high-efficiency assets.",
                "Review enterprise counterparty exposures and financing terms in light of the announcement."
            ]
        elif persona == "volatility":
            exec_summary = (
                f"[{mode_prefix}] High-Volatility Alert: Rapid market repricing triggered by '{title}'. "
                f"Elevated trading volume and liquidity shifts require cautious position management."
            )
            what_happened = (
                "A sharp divergence between expectations and incoming data triggered accelerated order flow, "
                "testing key technical support and resistance thresholds across major asset classes."
            )
            why_it_matters = (
                "Spikes in intraday volatility can cause sudden stop-losses, wider bid-ask spreads, "
                "and increased price slippage for both retail and institutional market participants."
            )
            takeaways = [
                "Heightened volatility necessitates disciplined risk management and tighter exposure controls.",
                "Watch key institutional support levels for signs of liquidity stabilization.",
                "Derivative funding rates and open interest signal potential secondary price swings."
            ]
        else:  # Retail Investor default
            exec_summary = (
                f"[{mode_prefix}] Here is what everyday investors need to know: '{title}'. "
                f"This shift signals important changes in market momentum and how major assets are being valued right now."
            )
            what_happened = (
                f"Investors are reacting to new economic and business data. Key sectors saw immediate movement as traders "
                f"repositioned their portfolios to prepare for the next quarter."
            )
            why_it_matters = (
                "Changes like these influence your 401(k), retirement index funds, savings interest rates, "
                "and the prices of common tech and blue-chip stocks you may hold."
            )
            takeaways = [
                "Consider the long-term fundamentals of your holdings rather than knee-jerk daily price swings.",
                "Diversified index portfolios naturally cushion against single-sector volatility.",
                "Keep an eye on interest rate trends, as they drive borrowing costs for everyday consumers."
            ]

        return {
            "article_id": article_id,
            "persona": persona,
            "mode": mode,
            "model_used": "Heuristic Financial NLP Engine",
            "executive_summary": exec_summary,
            "what_happened": what_happened,
            "why_it_matters": why_it_matters,
            "jargon_demystified": detected_jargon,
            "key_takeaways": takeaways,
            "market_sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "read_time": "1 min read"
        }

groq_service = GroqService()
