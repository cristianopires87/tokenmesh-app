import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

import html as html_lib
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from tokenmesh.pricing.pricing_table import MODEL_PRICING as _FALLBACK_PRICING
from tokenmesh.pricing.calculator import calculate_cost
from tokenmesh.pricing.context_windows import CONTEXT_WINDOWS
from tokenmesh.pricing.caching import CACHING, caching_breakeven, caching_cost
from tokenmesh.tokenizers import count_tokens, tokenize as tm_tokenize
from tokenmesh.architect.suggestions import suggest_architecture

st.set_page_config(
    page_title="TokenMesh",
    page_icon="TM",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    #MainMenu, footer, header { visibility: hidden; }

    [data-testid="stAppViewContainer"] {
        background-color: #0a0a0b;
        background-image: radial-gradient(#1f1f23 1.5px, transparent 1.5px);
        background-size: 28px 28px;
    }
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] { background: transparent; }

    .block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: min(1400px, 96vw); }

    .tm-wordmark {
        font-size: clamp(1.5rem, 2.5vw, 2.1rem); font-weight: 800; color: #fafafa;
        letter-spacing: -1px; line-height: 1; margin-bottom: 0.5rem;
        font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
    }
    .tm-wordmark span { color: #f59e0b; }
    .tm-sub {
        font-size: clamp(0.85rem, 1.2vw, 1rem); color: #52525b; margin-bottom: 2.5rem;
        line-height: 1.6; font-family: system-ui, -apple-system, sans-serif;
    }
    .tm-section-label {
        font-size: 0.8rem; font-weight: 500; color: #52525b;
        margin-bottom: 10px; font-family: system-ui, sans-serif;
    }
    .tm-result-title {
        font-size: 1rem; font-weight: 600; color: #a1a1aa; margin-bottom: 1.25rem;
        font-family: system-ui, sans-serif;
    }

    .stat-hero {
        background: #111114; border: 1px solid #27272a;
        border-radius: 10px; padding: 28px 32px;
    }
    .stat-hero-val {
        font-size: clamp(2.5rem, 4vw, 3.5rem); font-weight: 800; color: #fafafa;
        line-height: 1; letter-spacing: -2px;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .stat-hero-lbl { font-size: 0.8rem; color: #52525b; margin-top: 8px; font-family: system-ui, sans-serif; }

    .stat-sec {
        background: #111114; border: 1px solid #27272a;
        border-radius: 10px; padding: 20px 22px; height: 100%;
    }
    .stat-sec-val {
        font-size: 1.75rem; font-weight: 700; color: #71717a;
        line-height: 1; letter-spacing: -0.5px;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .stat-sec-lbl { font-size: 0.75rem; color: #3f3f46; margin-top: 6px; font-family: system-ui, sans-serif; }

    .content-card {
        background: #111114; border: 1px solid #27272a;
        border-radius: 10px; padding: 24px 28px; margin-top: 8px;
    }

    .ctx-card {
        background: #111114; border: 1px solid #27272a;
        border-radius: 10px; padding: 18px 20px;
    }
    .ctx-provider { font-size: 0.7rem; font-weight: 500; color: #52525b; margin-bottom: 2px; font-family: system-ui, sans-serif; }
    .ctx-model-name { font-size: 0.8rem; color: #71717a; font-family: 'SF Mono', 'Fira Code', monospace; margin-bottom: 14px; }
    .ctx-pct-big {
        font-size: 2rem; font-weight: 800; line-height: 1; letter-spacing: -1px;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .ctx-window-size { font-size: 0.75rem; color: #52525b; font-family: 'SF Mono', monospace; }
    .ctx-numbers { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
    .ctx-track { height: 4px; background: #1f1f23; border-radius: 2px; overflow: hidden; margin-bottom: 6px; }
    .ctx-fill { height: 100%; border-radius: 2px; }
    .ctx-tokens-label { font-size: 0.7rem; color: #3f3f46; font-family: 'SF Mono', monospace; }
    .ctx-warning { font-size: 0.75rem; color: #ef4444; margin-top: 4px; font-family: system-ui, sans-serif; }

    .cache-card {
        background: #111114; border: 1px solid #27272a;
        border-radius: 10px; padding: 20px 22px;
    }
    .cache-provider { font-size: 0.7rem; font-weight: 500; color: #52525b; margin-bottom: 2px; font-family: system-ui, sans-serif; }
    .cache-breakeven {
        font-size: 2rem; font-weight: 800; color: #f59e0b;
        line-height: 1; letter-spacing: -1px; margin-bottom: 4px;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .cache-breakeven-lbl { font-size: 0.75rem; color: #52525b; margin-bottom: 14px; font-family: system-ui, sans-serif; }
    .cache-row {
        display: flex; justify-content: space-between;
        border-top: 1px solid #1f1f23; padding: 7px 0;
        font-size: 0.8rem; font-family: system-ui, sans-serif;
    }
    .cache-row-lbl { color: #52525b; }
    .cache-row-val { color: #a1a1aa; font-family: 'SF Mono', monospace; }
    .cache-row-saving { color: #f59e0b; font-family: 'SF Mono', monospace; }
    .cache-disabled { font-size: 0.8rem; color: #3f3f46; font-family: system-ui, sans-serif; padding: 8px 0; }
    .cache-note { font-size: 0.7rem; color: #3f3f46; margin-top: 12px; font-family: system-ui, sans-serif; line-height: 1.5; }

    .step-card {
        background: #0d0d0f; border: 1px solid #27272a;
        border-radius: 8px; padding: 16px 20px; margin-bottom: 8px;
    }
    .step-role { font-size: 0.7rem; font-weight: 600; letter-spacing: .04em; color: #52525b; font-family: system-ui, sans-serif; text-transform: uppercase; }
    .step-model { font-size: 1rem; font-weight: 600; color: #fafafa; font-family: 'SF Mono', 'Fira Code', monospace; margin-top: 2px; }
    .step-desc { font-size: 0.875rem; color: #71717a; margin-top: 4px; font-family: system-ui, sans-serif; line-height: 1.5; }
    .step-why { font-size: 0.825rem; color: #3f3f46; margin-top: 4px; font-family: system-ui, sans-serif; font-style: italic; }
    .step-footer { display: flex; gap: 16px; align-items: baseline; margin-top: 8px; border-top: 1px solid #1f1f23; padding-top: 8px; }
    .step-cost { font-size: 0.875rem; color: #f59e0b; font-weight: 600; font-family: 'SF Mono', monospace; }
    .step-tokens { font-size: 0.75rem; color: #3f3f46; font-family: 'SF Mono', monospace; }

    .tier-card {
        background: #111114; border: 1px solid #27272a;
        border-radius: 10px; padding: 18px 20px; height: 100%;
    }
    .tier-card.active { border-color: rgba(245,158,11,.35); background: rgba(245,158,11,.04); }
    .tier-label { font-size: 0.7rem; font-weight: 600; letter-spacing: .05em; color: #52525b; text-transform: uppercase; font-family: system-ui, sans-serif; margin-bottom: 6px; }
    .tier-model { font-size: 0.95rem; font-weight: 600; color: #fafafa; font-family: 'SF Mono', monospace; }
    .tier-provider { font-size: 0.7rem; color: #3f3f46; font-family: system-ui, sans-serif; margin-bottom: 8px; }
    .tier-cost { font-size: 1.3rem; font-weight: 800; color: #f59e0b; font-family: system-ui, -apple-system, sans-serif; letter-spacing: -0.5px; }
    .tier-note { font-size: 0.75rem; color: #52525b; margin-top: 8px; line-height: 1.5; font-family: system-ui, sans-serif; }

    .arch-warning {
        background: rgba(239,68,68,.07); border: 1px solid rgba(239,68,68,.18);
        border-radius: 6px; padding: 10px 14px; margin-bottom: 6px;
        font-size: 0.825rem; color: #fca5a5; font-family: system-ui, sans-serif; line-height: 1.5;
    }
    .arch-tip {
        display: flex; gap: 10px; align-items: flex-start;
        padding: 8px 0; border-bottom: 1px solid #1a1a1d;
        font-size: 0.825rem; color: #71717a; font-family: system-ui, sans-serif; line-height: 1.5;
    }
    .arch-tip:last-child { border-bottom: none; }
    .arch-tip-dot { color: #f59e0b; flex-shrink: 0; font-size: 0.9rem; line-height: 1.4; }
    .arch-cache-tip {
        background: rgba(99,102,241,.07); border: 1px solid rgba(99,102,241,.2);
        border-radius: 6px; padding: 10px 14px; margin-top: 10px;
        font-size: 0.825rem; color: #a5b4fc; font-family: system-ui, sans-serif; line-height: 1.5;
    }
    .arch-cache-tip-label { font-size: 0.7rem; font-weight: 600; color: #6366f1; letter-spacing: .05em; text-transform: uppercase; margin-bottom: 4px; font-family: system-ui, sans-serif; }

    .badge {
        display: inline-block; border-radius: 4px; padding: 3px 10px;
        font-size: 0.75rem; font-weight: 500; margin-right: 6px;
        background: #1c1c1f; color: #71717a; border: 1px solid #27272a;
        font-family: system-ui, sans-serif;
    }
    .badge-savings { background: rgba(245,158,11,.1); color: #f59e0b; border-color: rgba(245,158,11,.2); }

    .tok-viz {
        font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.875rem; line-height: 2.3;
        background: #fafaf9; color: #1c1917; padding: 22px 26px;
        border-radius: 8px; border: 1px solid #e7e5e4;
        overflow-wrap: break-word; word-break: break-all;
    }
    .tok-meta { font-size: 0.8rem; color: #a1a1aa; margin-bottom: 10px; font-family: system-ui, sans-serif; }
    .tok-meta b { color: #fafafa; }
    .tok-meta code {
        font-family: 'SF Mono', monospace; font-size: 0.75rem;
        background: #1c1c1f; padding: 1px 5px; border-radius: 3px; color: #a1a1aa;
    }

    .eff-metric {
        background: #111114; border: 1px solid #27272a;
        border-radius: 8px; padding: 16px 20px;
    }
    .eff-metric-val {
        font-size: 1.5rem; font-weight: 700; line-height: 1;
        font-family: system-ui, -apple-system, sans-serif; letter-spacing: -0.5px;
    }
    .eff-metric-lbl { font-size: 0.72rem; color: #52525b; margin-top: 6px; font-family: system-ui, sans-serif; }

    .insight-card {
        background: rgba(245,158,11,.05); border: 1px solid rgba(245,158,11,.15);
        border-radius: 8px; padding: 16px 20px;
        font-size: 0.9rem; color: #a1a1aa; font-family: system-ui, sans-serif; line-height: 1.75;
    }

    .receipt {
        background: #0d0d0f; border: 1px solid #1f1f23;
        border-radius: 8px; padding: 18px 22px;
    }
    .receipt-label { font-size: 0.7rem; font-weight: 600; color: #52525b;
        letter-spacing: .05em; text-transform: uppercase; margin-bottom: 6px;
        font-family: system-ui, sans-serif; }
    .receipt-model { font-size: 0.8rem; color: #fafafa; font-family: 'SF Mono', monospace; margin-bottom: 12px; }
    .receipt-line { font-size: 0.75rem; color: #52525b; font-family: 'SF Mono', monospace;
        display: flex; justify-content: space-between; padding: 3px 0; }
    .receipt-line-val { color: #71717a; }
    .receipt-line-result { color: #a1a1aa; padding-left: 14px; }
    .receipt-sep { border: none; border-top: 1px solid #1f1f23; margin: 10px 0; }
    .receipt-total { display: flex; justify-content: space-between;
        font-size: 0.875rem; font-weight: 700; color: #fafafa; font-family: 'SF Mono', monospace; }
    .receipt-total-val { color: #f59e0b; }

    .anatomy-bar { display: flex; height: 5px; border-radius: 3px; overflow: hidden; margin: 0 0 8px; }
    .anatomy-legend { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 14px; }
    .anatomy-item { display: flex; align-items: center; gap: 5px;
        font-size: 0.72rem; color: #71717a; font-family: system-ui, sans-serif; }
    .anatomy-dot { width: 7px; height: 7px; border-radius: 2px; flex-shrink: 0; }

    div[data-testid="stButton"] { display: flex; justify-content: center; }
    div[data-testid="stButton"] button {
        background: #f59e0b; color: #0a0a0b; border: none; border-radius: 7px;
        font-weight: 700; font-size: 0.95rem; padding: 0.7rem 3rem;
        font-family: system-ui, sans-serif; transition: background .12s; min-width: 200px;
    }
    div[data-testid="stButton"] button:hover { background: #fbbf24; }
</style>
""", unsafe_allow_html=True)

# Translations

TRANSLATIONS = {
    "en": {
        "subtitle": "Paste text: token counts per provider, cost comparison, context window usage, caching ROI, and multi-turn projections.",
        "project_placeholder": "Project name (optional)",
        "textarea_placeholder": "Paste any text, prompt, code, document…",
        "calculate": "Calculate",
        "warning_empty": "Paste some text first.",
        "characters": "characters",
        "words": "words",
        "pages_est": "pages est.",
        "eff_chars_lbl": "chars / token · baseline 4.0",
        "eff_tokens_lbl": "tokens / word",
        "eff_label": "token efficiency",
        "eff_script_lbl": "script detected",
        "efficient": "efficient",
        "average": "average",
        "below_avg": "below avg",
        "latin_ascii": "Latin / ASCII",
        "section_cost_input": "Cost to send this text as input (USD)",
        "section_breakdown": "Full breakdown",
        "df_model": "Model", "df_provider": "Provider", "df_tokens": "Tokens",
        "df_input": "Input $", "df_inout": "In+Out $", "df_fits": "Fits",
        "cost_formula_lbl": "Cost formula: how the bill is calculated",
        "devin_title": "How we calculate Devin's cost",
        "devin_body": "Devin (Cognition AI) does not charge per token; it uses <b style=\"color:#fafafa\">ACUs (Agent Compute Units)</b>, where <b style=\"color:#fafafa\">1 ACU = $2.25</b>. To compare with other providers, we derived an estimated price per token:",
        "devin_formula": "effective rate = <span style=\"color:#00BFA5\">$2.25 per ACU</span> ÷ <span style=\"color:#a1a1aa\">100,000 estimated tokens per session</span> = <span style=\"color:#fafafa\">$22.50 / 1M tokens</span>",
        "devin_note": "The estimate of 100k tokens/ACU is based on typical agent sessions: file reading, multiple LLM calls, and code generation. More complex sessions consume more ACUs. This value is a reference for comparison, not the official price per token.",
        "receipt_total": "total",
        "receipt_input_tkns": "input tkns",
        "receipt_out_tkns": "out tkns (est.)",
        "receipt_acu_note": "Rate derived from ACU model. Not a direct token API.",
        "models_excluded": "model(s) excluded",
        "ctx_too_small": "context window too small for",
        "ctx_input_plus": "input + ~",
        "ctx_estimated_out": "estimated output tokens",
        "section_ctx": "Context window usage per provider",
        "ctx_exceeds": "exceeds limit",
        "section_cache": "Prompt caching ROI",
        "cache_not_supported": "not supported",
        "cache_need_tokens": "need >{n} tokens",
        "cache_breakeven_lbl": "calls to break even",
        "cache_calls": "calls",
        "section_token_breaks": "Token breaks by provider",
        "anatomy_whole": "whole words", "anatomy_subword": "subwords",
        "anatomy_numeric": "numbers", "anatomy_punct": "punctuation",
        "anatomy_space": "whitespace", "anatomy_other": "other",
        "section_multiturn": "Multi-turn conversation cost projector",
        "mt_caption": "In multi-turn chats, the entire history is resent every call. Cost grows quadratically, not linearly.",
        "mt_turns": "Conversation turns",
        "mt_output_pct": "Output size (% of prompt)",
        "mt_model": "Model",
        "mt_no_cache": "No caching",
        "mt_with_cache": "With caching",
        "mt_axis_turn": "Turn",
        "mt_axis_cost": "Cumulative cost (USD)",
        "mt_total_no_cache": "{n}-turn total · no caching",
        "mt_total_cache": "{n}-turn total · with caching",
        "mt_not_eligible": "caching not eligible",
        "mt_saved": "saved with caching ({pct:.0f}%)",
        "mt_savings": "savings",
        "section_arch": "Architecture recommendation",
        "section_tiers": "Model tiers for this input",
        "section_best_practices": "Best practices",
        "badge_saves": "saves ~{n}% vs GPT-4o",
        "pipeline_total": "Total pipeline cost:",
        "price_live": "Live prices",
        "price_cached": "Cached prices",
        "price_fallback": "Fallback prices",
        "price_updated": "{n} model(s) updated",
        "viz_exact": "exact tokenizer",
        "viz_approx": "BPE approximation",
        "viz_tokens": "tokens",
        "viz_rank_best": "#{rank} most efficient",
        "viz_rank_best_among": "among {total} providers",
        "viz_rank_best_fewer": "{pct:.0f}% fewer tokens than {prov} ({tok:,})",
        "viz_rank_worst": "#{rank} of {total} in efficiency",
        "viz_rank_worst_more": "{pct:.0f}% more tokens than {prov} ({tok:,})",
        "viz_rank_mid": "#{rank} of {total}",
        "viz_rank_mid_more": "{pct:.0f}% more than {min_prov} ({min_tok:,})",
        "viz_rank_mid_fewer": "{pct:.0f}% fewer than {max_prov} ({max_tok:,})",
        "viz_cost_cheapest": "Cost: <b style=\"color:#fafafa\">${cost:.6f}</b> / call (cheapest for this text)",
        "viz_cost_expensive": "Cost: <b style=\"color:#fafafa\">${cost:.6f}</b> / call, <span style=\"color:#ef4444\">+${diff:.6f}</span> vs {prov}",
        "viz_cost_plain": "Cost: <b style=\"color:#fafafa\">${cost:.6f}</b> / call",
        "viz_ctx_note": "Context: window of <b style=\"color:#fafafa\">{ctx}</b> tokens ≈ <b style=\"color:#fafafa\">{chars:,}</b> chars of this text type",
        "viz_ctx_extra": "({prov} fits +{extra:,} more chars)",
        "viz_why_fewer": "▸ Why do fewer tokens matter?",
        "viz_edu": [
            "<b>Direct cost</b>: pricing is per token. Fewer tokens for the same message = a smaller bill immediately, with no product changes needed.",
            "<b>More content in the same context</b>: two models with a 128k token window process very different amounts of real text if they tokenize with different efficiencies.",
            "<b>Non-English languages are penalized</b>: Portuguese, Arabic and CJK fragment into 2-4x more tokens than equivalent English; BPE vocabularies were optimized for English and treat other languages as rare character sequences.",
            "<b>Long identifiers tokenize well</b>: <code style='background:#1c1c1f;padding:1px 5px;border-radius:3px'>calculate_cost_per_provider</code> can be 1 token in modern vocabularies; in smaller vocabularies it becomes 4-6 fragments, each consuming context space.",
            "<b>Less fragmentation = better semantic cohesion</b>: the model receives text as a sequence of tokens. Highly fragmented text can dilute relationships between nearby words, hurting comprehension and translation tasks.",
        ],
        "section_compress": "Prompt Compressor",
        "section_hotspot": "Token Hotspot",
        "section_budget": "Budget Calculator",
        "section_breakeven": "Cost Scaling",
        "section_template": "Template Analyzer",
        "budget_slider": "Monthly budget (USD)",
        "budget_calls_month": "calls / month",
        "budget_calls_day": "calls / day",
        "hotspot_light": "light",
        "hotspot_medium": "medium",
        "hotspot_dense": "high density",
        "compress_total": "saveable tokens",
        "compress_comments": "comment tokens",
        "compress_stopwords": "stopword overhead",
        "compress_repeated": "repeated phrases",
        "compress_none": "No obvious compression opportunities detected.",
        "compress_insight": "Removing comments, reducing stopwords and deduplicating repeated phrases could save ~{n} tokens ({pct:.0f}%), equivalent to ${cost:.6f} per call on gpt-5.",
        "template_fixed": "fixed tokens",
        "template_var": "variable tokens (est.)",
        "template_vars": "detected variables",
        "template_cache_tip": "Fixed portion is large enough to cache. Break-even at {n}x calls ({model})",
        "template_none": "No template variables ({{var}} or {var}) detected.",
        "scaling_output_ratio": "Assumed output ratio",
        "scaling_current": "current text",
    },
    "pt": {
        "subtitle": "Cole texto: contagem de tokens por provider, comparação de custo, uso de janela de contexto, ROI de cache e projeções multi-turn.",
        "project_placeholder": "Nome do projeto (opcional)",
        "textarea_placeholder": "Cole qualquer texto, prompt, código, documento…",
        "calculate": "Calcular",
        "warning_empty": "Cole algum texto primeiro.",
        "characters": "caracteres",
        "words": "palavras",
        "pages_est": "páginas est.",
        "eff_chars_lbl": "chars / token · base 4,0",
        "eff_tokens_lbl": "tokens / palavra",
        "eff_label": "eficiência de tokens",
        "eff_script_lbl": "script detectado",
        "efficient": "eficiente",
        "average": "médio",
        "below_avg": "abaixo da média",
        "latin_ascii": "Latino / ASCII",
        "section_cost_input": "Custo para enviar este texto como input (USD)",
        "section_breakdown": "Detalhamento completo",
        "df_model": "Modelo", "df_provider": "Provider", "df_tokens": "Tokens",
        "df_input": "Input $", "df_inout": "Ent+Saí $", "df_fits": "Cabe",
        "cost_formula_lbl": "Fórmula de custo: como a conta é calculada",
        "devin_title": "Como calculamos o custo do Devin",
        "devin_body": "Devin (Cognition AI) não cobra por token; usa <b style=\"color:#fafafa\">ACUs (Agent Compute Units)</b>, onde <b style=\"color:#fafafa\">1 ACU = $2,25</b>. Para comparar com outros providers, derivamos um preço/token estimado:",
        "devin_formula": "taxa efetiva = <span style=\"color:#00BFA5\">$2,25 por ACU</span> ÷ <span style=\"color:#a1a1aa\">100.000 tokens estimados por sessão</span> = <span style=\"color:#fafafa\">$22,50 / 1M tokens</span>",
        "devin_note": "A estimativa de 100k tokens/ACU é baseada em sessões típicas de agente: leitura de arquivos, múltiplas chamadas LLM e geração de código. Sessões mais complexas consomem mais ACUs. Este valor é uma referência para comparação, não é o preço oficial por token.",
        "receipt_total": "total",
        "receipt_input_tkns": "tokens de entrada",
        "receipt_out_tkns": "tokens de saída (est.)",
        "receipt_acu_note": "Taxa derivada do modelo ACU. Não é uma API de token direta.",
        "models_excluded": "modelo(s) excluído(s)",
        "ctx_too_small": "janela de contexto pequena demais para",
        "ctx_input_plus": "input + ~",
        "ctx_estimated_out": "tokens de output estimados",
        "section_ctx": "Uso da janela de contexto por provider",
        "ctx_exceeds": "excede o limite",
        "section_cache": "ROI de prompt caching",
        "cache_not_supported": "não suportado",
        "cache_need_tokens": "precisa >{n} tokens",
        "cache_breakeven_lbl": "chamadas para breakeven",
        "cache_calls": "chamadas",
        "section_token_breaks": "Quebras de token por provider",
        "anatomy_whole": "palavras inteiras", "anatomy_subword": "subpalavras",
        "anatomy_numeric": "números", "anatomy_punct": "pontuação",
        "anatomy_space": "espaços", "anatomy_other": "outros",
        "section_multiturn": "Projetor de custo multi-turn",
        "mt_caption": "Em chats multi-turn, todo o histórico é reenviado a cada chamada. O custo cresce quadraticamente, não linearmente.",
        "mt_turns": "Turnos da conversa",
        "mt_output_pct": "Tamanho do output (% do prompt)",
        "mt_model": "Modelo",
        "mt_no_cache": "Sem cache",
        "mt_with_cache": "Com cache",
        "mt_axis_turn": "Turno",
        "mt_axis_cost": "Custo acumulado (USD)",
        "mt_total_no_cache": "{n} turnos · sem cache",
        "mt_total_cache": "{n} turnos · com cache",
        "mt_not_eligible": "cache não elegível",
        "mt_saved": "economizado com cache ({pct:.0f}%)",
        "mt_savings": "economia",
        "section_arch": "Recomendação de arquitetura",
        "section_tiers": "Tiers de modelo para este input",
        "section_best_practices": "Boas práticas",
        "badge_saves": "economiza ~{n}% vs GPT-4o",
        "pipeline_total": "Custo total do pipeline:",
        "price_live": "Preços ao vivo",
        "price_cached": "Preços em cache",
        "price_fallback": "Preços fallback",
        "price_updated": "{n} modelo(s) atualizado(s)",
        "viz_exact": "tokenizador exato",
        "viz_approx": "aproximação BPE",
        "viz_tokens": "tokens",
        "viz_rank_best": "#{rank} mais eficiente",
        "viz_rank_best_among": "entre os {total} providers",
        "viz_rank_best_fewer": "{pct:.0f}% menos tokens que {prov} ({tok:,})",
        "viz_rank_worst": "#{rank}º de {total} em eficiência",
        "viz_rank_worst_more": "{pct:.0f}% mais tokens que {prov} ({tok:,})",
        "viz_rank_mid": "#{rank}º de {total}",
        "viz_rank_mid_more": "{pct:.0f}% mais que {min_prov} ({min_tok:,})",
        "viz_rank_mid_fewer": "{pct:.0f}% menos que {max_prov} ({max_tok:,})",
        "viz_cost_cheapest": "Custo: <b style=\"color:#fafafa\">${cost:.6f}</b> / chamada (o mais barato para este texto)",
        "viz_cost_expensive": "Custo: <b style=\"color:#fafafa\">${cost:.6f}</b> / chamada, <span style=\"color:#ef4444\">+${diff:.6f}</span> vs {prov}",
        "viz_cost_plain": "Custo: <b style=\"color:#fafafa\">${cost:.6f}</b> / chamada",
        "viz_ctx_note": "Contexto: janela de <b style=\"color:#fafafa\">{ctx}</b> tokens ≈ <b style=\"color:#fafafa\">{chars:,}</b> chars deste tipo de texto",
        "viz_ctx_extra": "({prov} cabe +{extra:,} chars a mais)",
        "viz_why_fewer": "▸ Por que menos tokens é melhor?",
        "viz_edu": [
            "<b>Custo direto</b>: o preço é cobrado por token. Menos tokens na mesma mensagem = fatura menor imediatamente, sem mudar nada no produto.",
            "<b>Mais conteúdo no mesmo contexto</b>: dois modelos com janela de 128k tokens processam quantidades muito diferentes de texto real se tokenizarem com eficiências distintas.",
            "<b>Idiomas não-ingleses são penalizados</b>: português, árabe e CJK fragmentam em 2-4x mais tokens que o equivalente em inglês; os vocabulários BPE foram otimizados para inglês e tratam outros idiomas como sequências de caracteres raros.",
            "<b>Identificadores longos tokenizam bem</b>: <code style='background:#1c1c1f;padding:1px 5px;border-radius:3px'>calculate_cost_per_provider</code> pode ser 1 token em vocabulários modernos; em vocabulários menores vira 4-6 fragmentos, cada um consome espaço de contexto.",
            "<b>Menos fragmentação = melhor coesão semântica</b>: o modelo recebe o texto como sequência de tokens. Texto muito fragmentado pode diluir relações entre palavras próximas, prejudicando tarefas de compreensão e tradução.",
        ],
        "section_compress": "Compressor de Prompt",
        "section_hotspot": "Hotspot de Tokens",
        "section_budget": "Calculadora de Orçamento",
        "section_breakeven": "Escala de Custo",
        "section_template": "Analisador de Template",
        "budget_slider": "Orçamento mensal (USD)",
        "budget_calls_month": "chamadas / mês",
        "budget_calls_day": "chamadas / dia",
        "hotspot_light": "leve",
        "hotspot_medium": "médio",
        "hotspot_dense": "alta densidade",
        "compress_total": "tokens economizáveis",
        "compress_comments": "tokens de comentário",
        "compress_stopwords": "overhead de stopwords",
        "compress_repeated": "frases repetidas",
        "compress_none": "Nenhuma oportunidade óbvia de compressão detectada.",
        "compress_insight": "Remover comentários, reduzir stopwords e desduplicar frases repetidas pode economizar ~{n} tokens ({pct:.0f}%), equivalente a ${cost:.6f} por chamada no gpt-5.",
        "template_fixed": "tokens fixos",
        "template_var": "tokens variáveis (est.)",
        "template_vars": "variáveis detectadas",
        "template_cache_tip": "A parte fixa é grande o suficiente para cachear. Breakeven em {n}x chamadas ({model})",
        "template_none": "Nenhuma variável de template ({{{{var}}}} ou {{var}}) detectada.",
        "scaling_output_ratio": "Proporção de output assumida",
        "scaling_current": "texto atual",
    },
    "es": {
        "subtitle": "Pegue texto: conteo de tokens por proveedor, comparación de costos, ventana de contexto, ROI de caché y proyecciones multi-turno.",
        "project_placeholder": "Nombre del proyecto (opcional)",
        "textarea_placeholder": "Pegue cualquier texto, prompt, código, documento…",
        "calculate": "Calcular",
        "warning_empty": "Pegue algún texto primero.",
        "characters": "caracteres",
        "words": "palabras",
        "pages_est": "páginas est.",
        "eff_chars_lbl": "chars / token · base 4,0",
        "eff_tokens_lbl": "tokens / palabra",
        "eff_label": "eficiencia de tokens",
        "eff_script_lbl": "script detectado",
        "efficient": "eficiente",
        "average": "promedio",
        "below_avg": "bajo promedio",
        "latin_ascii": "Latino / ASCII",
        "section_cost_input": "Costo de enviar este texto como input (USD)",
        "section_breakdown": "Desglose completo",
        "df_model": "Modelo", "df_provider": "Proveedor", "df_tokens": "Tokens",
        "df_input": "Input $", "df_inout": "Ent+Sal $", "df_fits": "Cabe",
        "cost_formula_lbl": "Fórmula de costo: cómo se calcula la factura",
        "devin_title": "Cómo calculamos el costo de Devin",
        "devin_body": "Devin (Cognition AI) no cobra por token; usa <b style=\"color:#fafafa\">ACUs (Agent Compute Units)</b>, donde <b style=\"color:#fafafa\">1 ACU = $2,25</b>. Para comparar con otros proveedores, derivamos un precio/token estimado:",
        "devin_formula": "tasa efectiva = <span style=\"color:#00BFA5\">$2,25 por ACU</span> ÷ <span style=\"color:#a1a1aa\">100.000 tokens estimados por sesión</span> = <span style=\"color:#fafafa\">$22,50 / 1M tokens</span>",
        "devin_note": "La estimación de 100k tokens/ACU se basa en sesiones típicas de agente: lectura de archivos, múltiples llamadas LLM y generación de código. Las sesiones más complejas consumen más ACUs. Este valor es una referencia de comparación, no es el precio oficial por token.",
        "receipt_total": "total",
        "receipt_input_tkns": "tkns entrada",
        "receipt_out_tkns": "tkns salida (est.)",
        "receipt_acu_note": "Tasa derivada del modelo ACU. No es una API de token directa.",
        "models_excluded": "modelo(s) excluido(s)",
        "ctx_too_small": "ventana de contexto demasiado pequeña para",
        "ctx_input_plus": "input + ~",
        "ctx_estimated_out": "tokens de output estimados",
        "section_ctx": "Uso de ventana de contexto por proveedor",
        "ctx_exceeds": "excede el límite",
        "section_cache": "ROI de prompt caching",
        "cache_not_supported": "no soportado",
        "cache_need_tokens": "necesita >{n} tokens",
        "cache_breakeven_lbl": "llamadas para breakeven",
        "cache_calls": "llamadas",
        "section_token_breaks": "División de tokens por proveedor",
        "anatomy_whole": "palabras completas", "anatomy_subword": "subpalabras",
        "anatomy_numeric": "números", "anatomy_punct": "puntuación",
        "anatomy_space": "espacios", "anatomy_other": "otros",
        "section_multiturn": "Proyector de costo multi-turno",
        "mt_caption": "En chats multi-turno, todo el historial se reenvía en cada llamada. El costo crece cuadráticamente, no linealmente.",
        "mt_turns": "Turnos de conversación",
        "mt_output_pct": "Tamaño del output (% del prompt)",
        "mt_model": "Modelo",
        "mt_no_cache": "Sin caché",
        "mt_with_cache": "Con caché",
        "mt_axis_turn": "Turno",
        "mt_axis_cost": "Costo acumulado (USD)",
        "mt_total_no_cache": "{n} turnos · sin caché",
        "mt_total_cache": "{n} turnos · con caché",
        "mt_not_eligible": "caché no elegible",
        "mt_saved": "ahorrado con caché ({pct:.0f}%)",
        "mt_savings": "ahorros",
        "section_arch": "Recomendación de arquitectura",
        "section_tiers": "Niveles de modelo para este input",
        "section_best_practices": "Buenas prácticas",
        "badge_saves": "ahorra ~{n}% vs GPT-4o",
        "pipeline_total": "Costo total del pipeline:",
        "price_live": "Precios en vivo",
        "price_cached": "Precios en caché",
        "price_fallback": "Precios fallback",
        "price_updated": "{n} modelo(s) actualizado(s)",
        "viz_exact": "tokenizador exacto",
        "viz_approx": "aproximación BPE",
        "viz_tokens": "tokens",
        "viz_rank_best": "#{rank} más eficiente",
        "viz_rank_best_among": "entre los {total} proveedores",
        "viz_rank_best_fewer": "{pct:.0f}% menos tokens que {prov} ({tok:,})",
        "viz_rank_worst": "#{rank}º de {total} en eficiencia",
        "viz_rank_worst_more": "{pct:.0f}% más tokens que {prov} ({tok:,})",
        "viz_rank_mid": "#{rank}º de {total}",
        "viz_rank_mid_more": "{pct:.0f}% más que {min_prov} ({min_tok:,})",
        "viz_rank_mid_fewer": "{pct:.0f}% menos que {max_prov} ({max_tok:,})",
        "viz_cost_cheapest": "Costo: <b style=\"color:#fafafa\">${cost:.6f}</b> / llamada (el más barato para este texto)",
        "viz_cost_expensive": "Costo: <b style=\"color:#fafafa\">${cost:.6f}</b> / llamada, <span style=\"color:#ef4444\">+${diff:.6f}</span> vs {prov}",
        "viz_cost_plain": "Costo: <b style=\"color:#fafafa\">${cost:.6f}</b> / llamada",
        "viz_ctx_note": "Contexto: ventana de <b style=\"color:#fafafa\">{ctx}</b> tokens ≈ <b style=\"color:#fafafa\">{chars:,}</b> chars de este tipo de texto",
        "viz_ctx_extra": "({prov} cabe +{extra:,} chars más)",
        "viz_why_fewer": "▸ ¿Por qué menos tokens es mejor?",
        "viz_edu": [
            "<b>Costo directo</b>: el precio se cobra por token. Menos tokens en el mismo mensaje = una factura menor de inmediato, sin cambios en el producto.",
            "<b>Más contenido en el mismo contexto</b>: dos modelos con una ventana de 128k tokens procesan cantidades muy diferentes de texto real si tokenizan con distintas eficiencias.",
            "<b>Los idiomas no-ingleses son penalizados</b>: el español, árabe y CJK se fragmentan en 2-4x más tokens que el equivalente en inglés; los vocabularios BPE fueron optimizados para inglés.",
            "<b>Los identificadores largos tokenizan bien</b>: <code style='background:#1c1c1f;padding:1px 5px;border-radius:3px'>calculate_cost_per_provider</code> puede ser 1 token en vocabularios modernos; en vocabularios pequeños se convierte en 4–6 fragmentos.",
            "<b>Menos fragmentación = mejor cohesión semántica</b>: el modelo recibe el texto como secuencia de tokens. El texto muy fragmentado puede diluir relaciones entre palabras cercanas, perjudicando la comprensión.",
        ],
        "section_compress": "Compresor de Prompt",
        "section_hotspot": "Hotspot de Tokens",
        "section_budget": "Calculadora de Presupuesto",
        "section_breakeven": "Escala de Costo",
        "section_template": "Analizador de Plantilla",
        "budget_slider": "Presupuesto mensual (USD)",
        "budget_calls_month": "llamadas / mes",
        "budget_calls_day": "llamadas / día",
        "hotspot_light": "leve",
        "hotspot_medium": "medio",
        "hotspot_dense": "alta densidad",
        "compress_total": "tokens ahorrables",
        "compress_comments": "tokens de comentario",
        "compress_stopwords": "overhead de stopwords",
        "compress_repeated": "frases repetidas",
        "compress_none": "No se detectaron oportunidades obvias de compresión.",
        "compress_insight": "Eliminar comentarios, reducir stopwords y deduplicar frases repetidas podría ahorrar ~{n} tokens ({pct:.0f}%), equivalente a ${cost:.6f} por llamada en gpt-5.",
        "template_fixed": "tokens fijos",
        "template_var": "tokens variables (est.)",
        "template_vars": "variables detectadas",
        "template_cache_tip": "La parte fija es suficientemente grande para cachear. Breakeven en {n}x llamadas ({model})",
        "template_none": "No se detectaron variables de plantilla ({{{{var}}}} o {{var}}).",
        "scaling_output_ratio": "Proporción de output asumida",
        "scaling_current": "texto actual",
    },
    "zh": {
        "subtitle": "粘贴文本：按提供商统计令牌数、成本比较、上下文窗口使用、缓存ROI及多轮对话预测。",
        "project_placeholder": "项目名称（可选）",
        "textarea_placeholder": "粘贴任意文本、提示词、代码、文档…",
        "calculate": "计算",
        "warning_empty": "请先粘贴一些文本。",
        "characters": "字符",
        "words": "词语",
        "pages_est": "预估页数",
        "eff_chars_lbl": "字符/令牌 · 基准 4.0",
        "eff_tokens_lbl": "令牌/词",
        "eff_label": "令牌效率",
        "eff_script_lbl": "检测到的文字系统",
        "efficient": "高效",
        "average": "一般",
        "below_avg": "低于平均",
        "latin_ascii": "拉丁 / ASCII",
        "section_cost_input": "将此文本作为输入发送的费用（美元）",
        "section_breakdown": "完整明细",
        "df_model": "模型", "df_provider": "提供商", "df_tokens": "令牌数",
        "df_input": "输入 $", "df_inout": "输入+输出 $", "df_fits": "适配",
        "cost_formula_lbl": "成本公式：账单计算方式",
        "devin_title": "我们如何计算 Devin 的成本",
        "devin_body": "Devin (Cognition AI) 不按令牌计费，使用 <b style=\"color:#fafafa\">ACU（代理计算单元）</b>，其中 <b style=\"color:#fafafa\">1 ACU = $2.25</b>。为与其他提供商比较，我们推导了估算的每令牌价格：",
        "devin_formula": "有效费率 = <span style=\"color:#00BFA5\">$2.25 / ACU</span> ÷ <span style=\"color:#a1a1aa\">每次会话估计 100,000 个令牌</span> = <span style=\"color:#fafafa\">$22.50 / 1M 令牌</span>",
        "devin_note": "100k令牌/ACU的估算基于典型代理会话：读取文件、多次LLM调用和代码生成。更复杂的会话消耗更多ACU。此值仅供比较参考，不是官方每令牌价格。",
        "receipt_total": "合计",
        "receipt_input_tkns": "输入令牌",
        "receipt_out_tkns": "输出令牌（估）",
        "receipt_acu_note": "费率来自ACU模型推算，非直接令牌API。",
        "models_excluded": "个模型已排除",
        "ctx_too_small": "上下文窗口太小，无法容纳",
        "ctx_input_plus": "输入 + ~",
        "ctx_estimated_out": "个预估输出令牌",
        "section_ctx": "各提供商上下文窗口使用情况",
        "ctx_exceeds": "超出限制",
        "section_cache": "提示词缓存ROI",
        "cache_not_supported": "不支持",
        "cache_need_tokens": "需要 >{n} 令牌",
        "cache_breakeven_lbl": "达到盈亏平衡所需调用次数",
        "cache_calls": "次调用",
        "section_token_breaks": "各提供商令牌分布",
        "anatomy_whole": "完整词", "anatomy_subword": "子词",
        "anatomy_numeric": "数字", "anatomy_punct": "标点",
        "anatomy_space": "空白", "anatomy_other": "其他",
        "section_multiturn": "多轮对话成本预测",
        "mt_caption": "在多轮对话中，每次调用都会重新发送完整历史记录。成本呈二次方增长，而非线性增长。",
        "mt_turns": "对话轮次",
        "mt_output_pct": "输出大小（占提示词%）",
        "mt_model": "模型",
        "mt_no_cache": "无缓存",
        "mt_with_cache": "有缓存",
        "mt_axis_turn": "轮次",
        "mt_axis_cost": "累计费用（美元）",
        "mt_total_no_cache": "{n}轮 · 无缓存",
        "mt_total_cache": "{n}轮 · 有缓存",
        "mt_not_eligible": "不符合缓存条件",
        "mt_saved": "缓存节省 ({pct:.0f}%)",
        "mt_savings": "节省",
        "section_arch": "架构建议",
        "section_tiers": "此输入的模型层级",
        "section_best_practices": "最佳实践",
        "badge_saves": "节省约{n}% vs GPT-4o",
        "pipeline_total": "管道总成本：",
        "price_live": "实时价格",
        "price_cached": "缓存价格",
        "price_fallback": "备用价格",
        "price_updated": "{n} 个模型已更新",
        "viz_exact": "精确分词器",
        "viz_approx": "BPE近似",
        "viz_tokens": "令牌",
        "viz_rank_best": "#{rank} 最高效",
        "viz_rank_best_among": "在 {total} 个提供商中",
        "viz_rank_best_fewer": "比 {prov} 少 {pct:.0f}% 令牌（{tok:,}）",
        "viz_rank_worst": "效率排名第 #{rank}（共{total}）",
        "viz_rank_worst_more": "比 {prov} 多 {pct:.0f}% 令牌（{tok:,}）",
        "viz_rank_mid": "排名第 #{rank}（共{total}）",
        "viz_rank_mid_more": "比 {min_prov} 多 {pct:.0f}%（{min_tok:,}）",
        "viz_rank_mid_fewer": "比 {max_prov} 少 {pct:.0f}%（{max_tok:,}）",
        "viz_cost_cheapest": "成本：<b style=\"color:#fafafa\">${cost:.6f}</b> / 次调用（此文本最便宜）",
        "viz_cost_expensive": "成本：<b style=\"color:#fafafa\">${cost:.6f}</b> / 次调用，<span style=\"color:#ef4444\">+${diff:.6f}</span> vs {prov}",
        "viz_cost_plain": "成本：<b style=\"color:#fafafa\">${cost:.6f}</b> / 次调用",
        "viz_ctx_note": "上下文：窗口 <b style=\"color:#fafafa\">{ctx}</b> 令牌 ≈ 此类文本 <b style=\"color:#fafafa\">{chars:,}</b> 字符",
        "viz_ctx_extra": "（{prov} 可多容纳 +{extra:,} 字符）",
        "viz_why_fewer": "▸ 为什么令牌越少越好？",
        "viz_edu": [
            "<b>直接成本</b>：按令牌计费。相同消息使用更少令牌 = 账单立即减少，无需改变产品。",
            "<b>相同上下文中容纳更多内容</b>：两个拥有128k令牌窗口的模型，若分词效率不同，实际能处理的文本量差异巨大。",
            "<b>非英语语言被惩罚</b>：中文、阿拉伯语等比等效英文多产生2-4倍令牌，BPE词汇表针对英语优化，将其他语言视为罕见字符序列。",
            "<b>长标识符分词效果好</b>：<code style='background:#1c1c1f;padding:1px 5px;border-radius:3px'>calculate_cost_per_provider</code> 在现代词汇表中可能是1个令牌；在小词汇表中变成4–6个片段。",
            "<b>碎片化越少 = 语义连贯性越好</b>：模型将文本作为令牌序列接收。高度碎片化的文本会削弱邻近词之间的关系，影响理解和翻译任务。",
        ],
        "section_compress": "提示词压缩器",
        "section_hotspot": "令牌热点",
        "section_budget": "预算计算器",
        "section_breakeven": "成本规模",
        "section_template": "模板分析器",
        "budget_slider": "月度预算（美元）",
        "budget_calls_month": "次调用 / 月",
        "budget_calls_day": "次调用 / 天",
        "hotspot_light": "轻量",
        "hotspot_medium": "中等",
        "hotspot_dense": "高密度",
        "compress_total": "可节省令牌",
        "compress_comments": "注释令牌",
        "compress_stopwords": "停用词开销",
        "compress_repeated": "重复短语",
        "compress_none": "未检测到明显的压缩机会。",
        "compress_insight": "删除注释、减少停用词并去除重复短语可节省约 {n} 个令牌（{pct:.0f}%），相当于每次调用 gpt-5 节省 ${cost:.6f}。",
        "template_fixed": "固定令牌",
        "template_var": "可变令牌（估）",
        "template_vars": "检测到的变量",
        "template_cache_tip": "固定部分足够大，可以缓存。在 {n}x 次调用时达到盈亏平衡（{model}）",
        "template_none": "未检测到模板变量（{{{{var}}}} 或 {{var}}）。",
        "scaling_output_ratio": "假设的输出比例",
        "scaling_current": "当前文本",
    },
}

# Constants

PROVIDERS = {
    "openai": {"color": "#10A37F", "model": "gpt-5", "display": "OpenAI"},
    "anthropic": {"color": "#D4722E", "model": "claude-opus-4", "display": "Anthropic"},
    "deepseek": {"color": "#5865F2", "model": "deepseek-r1", "display": "DeepSeek"},
    "google": {"color": "#4285F4", "model": "gemini-1.5-pro", "display": "Google-Gemini"},
    "mistral": {"color": "#FF7000", "model": "mistral-large", "display": "Mistral"},
    "devin": {"color": "#00BFA5", "model": "devin-agent", "display": "Devin"},
    "aws_bedrock": {
        "color": "#FF9900",
        "model": "llama-4-maverick",
        "display": "AWS-Bedrock",
        "tagline": "expressão de milhões de fãs ao redor do mundo",
    },
}

_ACU_PROVIDERS = {"devin"}

TOKEN_COLORS = [
    "rgba(251,191,36,.38)",
    "rgba(134,239,172,.45)",
    "rgba(196,181,253,.45)",
]

MAX_VIZ_TOKENS = 600


def _pcolor(provider: str) -> str:
    return PROVIDERS.get(provider, {}).get("color", "#6366f1")

def _hex_rgba(h: str, a: float) -> str:
    h = h.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

def _ctx_color(pct: float) -> str:
    if pct < 40:  return "#22c55e"
    if pct < 70:  return "#f59e0b"
    if pct < 90:  return "#f97316"
    return "#ef4444"

def _fmt_ctx(n: int) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n//1_000}k"
    return str(n)

def _render_token_viz(tokens: list[str], is_exact: bool, model: str, T: dict) -> str:
    accuracy = T["viz_exact"] if is_exact else T["viz_approx"]
    shown = tokens[:MAX_VIZ_TOKENS]
    spans = []
    for i, tok in enumerate(shown):
        color = TOKEN_COLORS[i % len(TOKEN_COLORS)]
        safe = html_lib.escape(tok)
        safe = safe.replace(" ", "&thinsp;·&thinsp;").replace("\n", "↵<br>").replace("\t", "→")
        spans.append(
            f'<span style="background:{color};padding:1px 5px;border-radius:3px;'
            f'margin:0 1px;white-space:pre-wrap">{safe}</span>'
        )
    if len(tokens) > MAX_VIZ_TOKENS:
        spans.append(f'<span style="color:#a8a29e;font-size:11px"> … +{len(tokens)-MAX_VIZ_TOKENS:,} {T["viz_tokens"]}</span>')
    meta = (
        f'<p class="tok-meta"><b>{len(tokens):,} {T["viz_tokens"]}</b>'
        f' &nbsp;·&nbsp; <code>{model}</code>'
        f' &nbsp;·&nbsp; {accuracy}</p>'
    )
    return meta + f'<div class="tok-viz">{"".join(spans)}</div>'

def _detect_scripts(text: str) -> list[str]:
    scripts = []
    if any('一' <= c <= '鿿' or '぀' <= c <= 'ヿ' or '가' <= c <= '힯' for c in text):
        scripts.append("CJK")
    if any('؀' <= c <= 'ۿ' for c in text):
        scripts.append("Arabic")
    if any('Ѐ' <= c <= 'ӿ' for c in text):
        scripts.append("Cyrillic")
    return scripts


def _token_anatomy(tokens: list[str]) -> dict:
    whole = subword = numeric = punct = space_tok = other = 0
    for tok in tokens:
        s = tok.strip()
        if not s:
            space_tok += 1
        elif s.replace('.','').replace(',','').replace('-','').isdigit():
            numeric += 1
        elif all(c in '.,!?;:()[]{}\'"-/\\@#$%^&*+=<>|~`_' for c in s):
            punct += 1
        elif s.replace("'","").replace("-","").isalpha():
            whole += 1 if (tok.startswith(' ') or tok == s) else 0
            subword += 0 if (tok.startswith(' ') or tok == s) else 1
        else:
            other += 1
    return {"whole": whole, "subword": subword, "numeric": numeric,
            "punct": punct, "space": space_tok, "other": other, "total": len(tokens)}


def _efficiency_label(ratio: float) -> tuple[str, str]:
    if ratio >= 0.95:  return "efficient",  "#22c55e"
    if ratio >= 0.78:  return "average",    "#f59e0b"
    return "below_avg", "#ef4444"


def _efficiency_insight(chars_per_tok: float, tok_per_word: float,
                         content_type: str, scripts: list[str], lang: str) -> str:
    parts = []
    if lang == "pt":
        if scripts:
            s = " + ".join(scripts)
            parts.append(
                f"Caracteres {s} usam 2-4x mais tokens que o equivalente em latim. "
                "Os vocabulários BPE são otimizados para o inglês, então scripts não-latinos são codificados com menos eficiência. "
                "Isso aumenta diretamente o custo por frase."
            )
        elif chars_per_tok < 3.2:
            parts.append(
                f"Com {chars_per_tok:.1f} chars/token (abaixo da baseline de ~4,0 para prosa em inglês) "
                "este texto está tokenizando com menos eficiência que a média. "
                "Identificadores curtos, símbolos, nomes camelCase e termos mistos fragmentam em mais tokens relativos à contagem de caracteres."
            )
        elif chars_per_tok > 4.6:
            parts.append(
                f"Com {chars_per_tok:.1f} chars/token, isso é mais eficiente que prosa típica em inglês (~4,0). "
                "Palavras compostas longas e vocabulário denso tendem a compactar mais significado por token, reduzindo o custo por ideia expressa."
            )
        else:
            parts.append(
                f"Com {chars_per_tok:.1f} chars/token, isso está próximo da baseline de prosa em inglês de 4,0. "
                "A eficiência de tokenização é típica para este tipo de conteúdo."
            )
        if content_type == "code":
            parts.append(
                "Operadores de código, colchetes e nomes curtos de variáveis fragmentam em mais tokens que prosa. "
                "Remover comentários e docstrings antes de enviar pode reduzir a contagem de tokens em 15–30% com perda mínima de informação."
            )
        elif content_type == "json":
            parts.append(
                "Tokens de estrutura JSON (chaves, dois pontos, aspas) adicionam 20–40% de overhead sobre os dados brutos. "
                "Minificar e remover chaves não utilizadas antes de enviar reduz o custo significativamente."
            )
        elif content_type == "conversation":
            parts.append(
                f"Com {tok_per_word:.1f} tokens/palavra, o formato de conversa adiciona overhead de marcadores de role e estrutura de turno. "
                "Comprima turnos mais antigos em um resumo contínuo para manter a contagem de tokens por chamada estável."
            )
    elif lang == "es":
        if scripts:
            s = " + ".join(scripts)
            parts.append(
                f"Los caracteres {s} usan 2-4x más tokens que el equivalente latino. "
                "Los vocabularios BPE están optimizados para el inglés, por lo que los scripts no latinos se codifican con menos eficiencia. "
                "Esto aumenta directamente el costo por frase."
            )
        elif chars_per_tok < 3.2:
            parts.append(
                f"Con {chars_per_tok:.1f} chars/token (por debajo de la línea base de ~4,0 para prosa en inglés) "
                "este texto tokeniza con menos eficiencia que el promedio. "
                "Identificadores cortos, símbolos, nombres camelCase y términos mixtos se fragmentan en más tokens."
            )
        elif chars_per_tok > 4.6:
            parts.append(
                f"Con {chars_per_tok:.1f} chars/token esto es más eficiente que la prosa inglesa típica (~4,0). "
                "Las palabras compuestas largas y el vocabulario denso tienden a empaquetar más significado por token, reduciendo el costo por idea expresada."
            )
        else:
            parts.append(
                f"Con {chars_per_tok:.1f} chars/token esto está cerca de la línea base de prosa inglesa de 4,0. "
                "La eficiencia de tokenización es típica para este tipo de contenido."
            )
        if content_type == "code":
            parts.append(
                "Los operadores de código, corchetes y nombres cortos de variables se fragmentan en más tokens que la prosa. "
                "Eliminar comentarios y docstrings antes de enviar puede reducir el conteo de tokens en 15–30%."
            )
        elif content_type == "json":
            parts.append(
                "Los tokens de estructura JSON (llaves, dos puntos, comillas) añaden un 20–40% de overhead sobre los datos brutos. "
                "Minificar y eliminar claves no utilizadas antes de enviar reduce el costo significativamente."
            )
        elif content_type == "conversation":
            parts.append(
                f"Con {tok_per_word:.1f} tokens/palabra el formato de conversación añade overhead de marcadores de rol y estructura de turno. "
                "Comprima los turnos más antiguos en un resumen para mantener plano el conteo de tokens por llamada."
            )
    elif lang == "zh":
        if scripts:
            s = " + ".join(scripts)
            parts.append(
                f"{s}字符使用的令牌数是等效拉丁文本的2-4倍。"
                "BPE词汇表针对英语优化，因此非拉丁脚本的编码效率较低。"
                "这直接增加了每句话的成本。"
            )
        elif chars_per_tok < 3.2:
            parts.append(
                f"以{chars_per_tok:.1f}字符/令牌（低于英语散文~4.0的基准）"
                "此文本的分词效率低于平均水平。"
                "短标识符、符号、驼峰命名和混合大小写术语各自产生更多令牌。"
            )
        elif chars_per_tok > 4.6:
            parts.append(
                f"以{chars_per_tok:.1f}字符/令牌，这比典型英语散文（~4.0）更高效。"
                "长复合词和密集词汇往往每个令牌承载更多含义，降低每个表达想法的成本。"
            )
        else:
            parts.append(
                f"以{chars_per_tok:.1f}字符/令牌，这接近英语散文4.0的基准。"
                "此内容类型的分词效率属于典型水平。"
            )
        if content_type == "code":
            parts.append(
                "代码运算符、括号和短变量名比散文产生更多令牌。"
                "发送前删除注释和文档字符串可将令牌数减少15–30%，信息损失极小。"
            )
        elif content_type == "json":
            parts.append(
                "JSON结构令牌（花括号、冒号、引号）在原始数据基础上增加20–40%的开销。"
                "发送前压缩并删除未使用的键可显著降低成本。"
            )
        elif content_type == "conversation":
            parts.append(
                f"以{tok_per_word:.1f}令牌/词，对话格式因角色标记和轮次结构增加了开销。"
                "将旧轮次压缩为滚动摘要，保持每次调用的令牌数恒定。"
            )
    else:  # en
        if scripts:
            s = " + ".join(scripts)
            parts.append(
                f"{s} characters use 2-4x more tokens than equivalent Latin text. "
                "BPE vocabularies are optimised for English, so non-Latin scripts are encoded less efficiently. "
                "This directly increases your cost per sentence."
            )
        elif chars_per_tok < 3.2:
            parts.append(
                f"At {chars_per_tok:.1f} chars/token (below the ~4.0 English prose baseline) "
                "this text is tokenising less efficiently than average. "
                "Short identifiers, symbols, camelCase names, and mixed-case terms each break into more tokens relative to their character count."
            )
        elif chars_per_tok > 4.6:
            parts.append(
                f"At {chars_per_tok:.1f} chars/token this is more efficient than typical English prose (~4.0). "
                "Long compound words and dense vocabulary tend to pack more meaning per token, lowering cost per idea expressed."
            )
        else:
            parts.append(
                f"At {chars_per_tok:.1f} chars/token this is close to the English prose baseline of 4.0. "
                "Tokenisation efficiency is typical for this content type."
            )
        if content_type == "code":
            parts.append(
                "Code operators, brackets, and short variable names fragment into more tokens than prose. "
                "Stripping comments and docstrings before sending can reduce token count by 15–30% with minimal information loss."
            )
        elif content_type == "json":
            parts.append(
                "JSON structure tokens (braces, colons, quotes) add 20–40% overhead over the raw data. "
                "Minifying and removing unused keys before sending reduces cost significantly."
            )
        elif content_type == "conversation":
            parts.append(
                f"At {tok_per_word:.1f} tokens/word the conversation format adds overhead from role markers and turn structure. "
                "Compress older turns into a running summary to keep the per-call token count flat."
            )
    return " ".join(parts)


def _viz_insight(provider: str, tok: int, all_counts: dict,
                 model: str, is_exact: bool, char_count: int, T: dict) -> str:
    ordered    = sorted(all_counts.items(), key=lambda x: x[1])
    min_prov, min_tok = ordered[0]
    max_prov, max_tok = ordered[-1]
    rank       = next(i + 1 for i, (p, _) in enumerate(ordered) if p == provider)
    total      = len(ordered)
    is_best    = provider == min_prov
    is_worst   = provider == max_prov
    accuracy   = T["viz_exact"] if is_exact else T["viz_approx"]

    pct_vs_best  = (tok - min_tok) / min_tok * 100 if min_tok > 0 else 0
    pct_vs_worst = (max_tok - tok) / tok  * 100 if tok > 0 else 0

    if is_best:
        rank_color = "#22c55e"
        rank_html  = (
            f'<span style="color:#22c55e;font-weight:700">'
            + T["viz_rank_best"].format(rank=rank)
            + f'</span> '
            + T["viz_rank_best_among"].format(total=total)
            + f' <span style="color:#22c55e">'
            + T["viz_rank_best_fewer"].format(pct=pct_vs_worst, prov=PROVIDERS.get(max_prov, {}).get("display", max_prov.title()), tok=max_tok)
            + f'</span>'
        )
    elif is_worst:
        rank_color = "#ef4444"
        rank_html  = (
            f'<span style="color:#ef4444;font-weight:700">'
            + T["viz_rank_worst"].format(rank=rank, total=total)
            + f'</span> <span style="color:#ef4444">'
            + T["viz_rank_worst_more"].format(pct=pct_vs_best, prov=PROVIDERS.get(min_prov, {}).get("display", min_prov.title()), tok=min_tok)
            + f'</span>'
        )
    else:
        rank_color = "#f59e0b"
        rank_html  = (
            f'<span style="color:#f59e0b;font-weight:700">'
            + T["viz_rank_mid"].format(rank=rank, total=total)
            + f'</span> '
            + T["viz_rank_mid_more"].format(pct=pct_vs_best, min_prov=PROVIDERS.get(min_prov, {}).get("display", min_prov.title()), min_tok=min_tok)
            + f' · '
            + T["viz_rank_mid_fewer"].format(pct=pct_vs_worst, max_prov=PROVIDERS.get(max_prov, {}).get("display", max_prov.title()), max_tok=max_tok)
        )

    best_model  = PROVIDERS.get(min_prov, {}).get("model", "gpt-5")
    this_meta   = MODEL_PRICING.get(model, {})
    best_meta   = MODEL_PRICING.get(best_model, {})
    this_cost   = tok    * (this_meta.get("input", 0) + this_meta.get("output", 0))
    best_cost   = min_tok * (best_meta.get("input",  0) + best_meta.get("output",  0))
    diff        = this_cost - best_cost

    if is_best:
        cost_note = T["viz_cost_cheapest"].format(cost=this_cost)
    elif diff > 0.0000005:
        cost_note = T["viz_cost_expensive"].format(cost=this_cost, diff=diff, prov=PROVIDERS.get(min_prov, {}).get("display", min_prov.title()))
    else:
        cost_note = T["viz_cost_plain"].format(cost=this_cost)

    ctx         = CONTEXT_WINDOWS.get(model, 128_000)
    cpt         = char_count / tok if tok > 0 else 4.0
    chars_in_ctx = int(ctx * cpt)
    ctx_note    = T["viz_ctx_note"].format(ctx=_fmt_ctx(ctx), chars=chars_in_ctx)
    if not is_best and min_tok > 0:
        best_cpt    = char_count / min_tok
        best_chars  = int(CONTEXT_WINDOWS.get(best_model, 128_000) * best_cpt)
        extra       = best_chars - chars_in_ctx
        if extra > 0:
            ctx_note += f' <span style="color:#3f3f46">' + T["viz_ctx_extra"].format(prov=PROVIDERS.get(min_prov, {}).get("display", min_prov.title()), extra=extra) + '</span>'

    edu_rows = "".join(
        f'<div style="display:flex;gap:10px;padding:7px 0;border-bottom:1px solid #1a1a1d">'
        f'<span style="color:#f59e0b;flex-shrink:0;margin-top:1px">›</span>'
        f'<span style="font-size:11.5px;color:#71717a;line-height:1.65">{item}</span>'
        f'</div>'
        for item in T["viz_edu"]
    )

    return (
        f'<div style="background:#111114;border:1px solid #27272a;border-radius:8px;'
        f'padding:16px 20px;margin-bottom:12px">'

        f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px">'
        f'<div style="font-size:1.6rem;font-weight:800;color:{rank_color};'
        f'font-family:system-ui,sans-serif;letter-spacing:-1px;line-height:1">'
        f'{tok:,}'
        f'<span style="font-size:0.9rem;font-weight:400;color:#52525b;margin-left:6px">{T["viz_tokens"]}</span>'
        f'</div>'
        f'<div style="font-size:10px;color:#3f3f46;font-family:\'SF Mono\',monospace">'
        f'{model} &nbsp;·&nbsp; {accuracy}'
        f'</div>'
        f'</div>'

        f'<div style="font-size:12.5px;color:#71717a;font-family:system-ui,sans-serif;'
        f'line-height:1.6;margin-bottom:10px">'
        f'{rank_html}'
        f'</div>'

        f'<div style="font-size:12px;color:#52525b;font-family:system-ui,sans-serif;'
        f'line-height:1.8;border-top:1px solid #1f1f23;padding-top:10px">'
        f'{cost_note}<br>{ctx_note}'
        f'</div>'

        f'<details style="margin-top:12px">'
        f'<summary style="cursor:pointer;font-size:11px;color:#3f3f46;list-style:none;'
        f'font-family:system-ui,sans-serif;outline:none;user-select:none;'
        f'transition:color .15s" '
        f'onmouseover="this.style.color=\'#f59e0b\'" '
        f'onmouseout="this.style.color=\'#3f3f46\'">'
        f'{T["viz_why_fewer"]}'
        f'</summary>'
        f'<div style="margin-top:10px">{edu_rows}</div>'
        f'</details>'

        f'</div>'
    )


def _multiturn_series(model: str, system_tokens: int, turns: int, output_pct: float):
    provider = MODEL_PRICING.get(model, {}).get("provider", "openai")
    cache_info = CACHING.get(provider, {"supported": False})

    user_per_turn = max(20, int(system_tokens * 0.05))
    out_per_turn  = max(50, int(system_tokens * output_pct / 100))

    no_cache = []
    with_cache = []
    cum_no = 0.0
    cum_cache = 0.0

    for k in range(1, turns + 1):
        history = (k - 1) * (user_per_turn + out_per_turn)
        input_k = system_tokens + history + user_per_turn

        turn_cost = calculate_cost(model, input_k, out_per_turn)
        cum_no += turn_cost
        no_cache.append((k, cum_no))

        if cache_info.get("supported") and system_tokens >= cache_info.get("min_tokens", 1024):
            if k == 1:
                sys_cost = calculate_cost(model, system_tokens, 0) * cache_info["cache_write_multiplier"]
            else:
                sys_cost = calculate_cost(model, system_tokens, 0) * cache_info["cache_read_multiplier"]
            rest_cost = calculate_cost(model, history + user_per_turn, out_per_turn)
            cum_cache += sys_cost + rest_cost
        else:
            cum_cache += turn_cost

        with_cache.append((k, cum_cache))

    return no_cache, with_cache


_STOPWORDS_EN = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","being","have","has","had","do",
    "does","did","will","would","could","should","may","might","shall",
    "can","that","this","these","those","it","its","as","by","from","into",
    "through","during","before","after","above","below","up","down","out",
    "off","over","under","again","further","then","once","so","if","not",
    "no","nor","very","just","also","than","too","i","you","he","she","we",
    "they","me","him","her","us","them","my","your","his","our","their",
}


def _analyze_compression(text: str, token_count: int) -> dict:
    import re
    lines = text.splitlines()
    comment_lines = [l for l in lines if l.strip().startswith(("#", "//", "/*", "*", "<!--"))]
    comment_tokens = max(1, int(token_count * len(comment_lines) / max(len(lines), 1)))

    words = text.lower().split()
    stopword_tokens = int(sum(1 for w in words if w.strip(".,!?;:") in _STOPWORDS_EN) * 1.0)

    toks = text.split()
    ngrams: dict[str, int] = {}
    for n in (3, 4):
        for i in range(len(toks) - n + 1):
            g = " ".join(toks[i:i+n])
            ngrams[g] = ngrams.get(g, 0) + 1
    repeated_phrases = sum(c - 1 for c in ngrams.values() if c > 1)
    repeated_tokens = min(repeated_phrases * 3, token_count // 4)

    saveable = comment_tokens + max(0, stopword_tokens - len(words) // 10) + repeated_tokens
    saveable = min(saveable, int(token_count * 0.6))
    return {
        "total_saveable": saveable,
        "comment_tokens": comment_tokens,
        "stopword_tokens": stopword_tokens,
        "repeated_tokens": repeated_tokens,
    }


def _token_hotspot_html(text: str) -> str:
    import re
    paragraphs = [p.strip() for p in re.split(r"\n{2,}|\n", text) if p.strip()]
    if not paragraphs:
        return ""
    counts = [len(p.split()) for p in paragraphs]
    mx = max(counts) or 1
    parts = []
    for para, cnt in zip(paragraphs, counts):
        ratio = cnt / mx
        if ratio < 0.33:
            color, label = "#22c55e", "light"
        elif ratio < 0.66:
            color, label = "#f59e0b", "medium"
        else:
            color, label = "#ef4444", "dense"
        safe = html_lib.escape(para)
        parts.append(
            f'<div style="margin-bottom:6px;padding:8px 12px;border-left:3px solid {color};'
            f'background:{color}18;border-radius:0 6px 6px 0;font-size:0.8rem;color:#a1a1aa">'
            f'<span style="color:{color};font-size:0.7rem;font-weight:600;margin-right:8px">'
            f'[{cnt} w]</span>{safe}</div>'
        )
    return "".join(parts)


def _analyze_template(text: str, token_count: int) -> dict:
    import re
    vars_double = re.findall(r"\{\{(\w+)\}\}", text)
    vars_single = re.findall(r"\{(\w+)\}", text)
    all_vars = list(dict.fromkeys(vars_double + vars_single))
    cleaned = re.sub(r"\{\{?\w+\}?\}", "", text)
    fixed_tokens = max(0, int(token_count * len(cleaned) / max(len(text), 1)))
    var_tokens = token_count - fixed_tokens
    return {"vars": all_vars, "fixed_tokens": fixed_tokens, "var_tokens": var_tokens}


@st.cache_data(ttl=86_400, show_spinner=False)
def _get_model_pricing() -> tuple[dict, dict]:
    try:
        from tokenmesh.pricing.updater import load_model_pricing
        return load_model_pricing()
    except Exception as _e:
        import traceback
        traceback.print_exc()
        print(f"[TokenMesh] pricing update failed ({type(_e).__name__}: {_e}), using fallback")
        return _FALLBACK_PRICING, {"source": "fallback", "updated_at": None, "changed": []}


# Language selector

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"
_qp = st.query_params.get("lang", None)
if _qp in TRANSLATIONS:
    st.session_state["lang"] = _qp
_cur = st.session_state["lang"]

# Hero + language selector

_LANG_LIST = [("en", "EN"), ("pt", "PT"), ("es", "ES"), ("zh", "ZH")]
_btns = ""
for _i, (_code, _label) in enumerate(_LANG_LIST):
    _a = _code == _cur
    _r = "border-radius:5px 0 0 5px;" if _i == 0 else ("border-radius:0 5px 5px 0;" if _i == 3 else "")
    _bl = "border-left:none;" if _i > 0 else ""
    _btns += (
        f'<a href="?lang={_code}" target="_self" style="display:inline-block;padding:5px 15px;'
        f'border:1px solid {"rgba(245,158,11,.4)" if _a else "#27272a"};{_bl}{_r}'
        f'background:{"rgba(245,158,11,.08)" if _a else "#0a0a0b"};'
        f'color:{"#f59e0b" if _a else "#52525b"};font-size:0.8rem;'
        f'font-weight:{"700" if _a else "500"};'
        f'font-family:system-ui,sans-serif;text-decoration:none;letter-spacing:.04em">'
        f'{_label}</a>'
    )

_c_wordmark, _c_lang = st.columns([5, 2])
with _c_wordmark:
    st.markdown('<p class="tm-wordmark">Token<span>Mesh</span></p>', unsafe_allow_html=True)
with _c_lang:
    st.markdown(
        f'<div style="display:flex;justify-content:flex-end;padding-top:6px">{_btns}</div>',
        unsafe_allow_html=True,
    )

T = TRANSLATIONS[st.session_state["lang"]]
st.markdown(f'<p class="tm-sub">{T["subtitle"]}</p>', unsafe_allow_html=True)

# Input

project_name = st.text_input(
    "project", placeholder=T["project_placeholder"], label_visibility="collapsed"
)

raw_text = st.text_area(
    "input", height=200,
    placeholder=T["textarea_placeholder"],
    label_visibility="collapsed",
)

st.markdown("<br>", unsafe_allow_html=True)
calculate = st.button(T["calculate"])

if calculate:
    if not raw_text.strip():
        st.warning(T["warning_empty"])
        st.stop()
    st.session_state["calc_text"] = raw_text.strip()

# Results

MODEL_PRICING, _price_meta = _get_model_pricing()

_src = _price_meta["source"]
_ts  = _price_meta.get("updated_at")
if _src == "live":
    _age_str = "just now"
    _dot_color = "#22c55e"
elif _src == "cache" and _ts:
    _age_h = int((time.time() - _ts) // 3600)
    _age_str = f"{_age_h}h ago" if _age_h > 0 else "< 1h ago"
    _dot_color = "#f59e0b"
else:
    _age_str = ""
    _dot_color = "#52525b"

_changed_note = ""
if _price_meta.get("changed"):
    _changed_note = (
        f' &nbsp;·&nbsp; <span style="color:#f59e0b">'
        f'{T["price_updated"].format(n=len(_price_meta["changed"]))}</span>'
    )

_price_label = T["price_live"] if _src == "live" else (T["price_cached"] if _src == "cache" else T["price_fallback"])

st.markdown(
    f'<p style="font-size:11px;color:{_dot_color};font-family:system-ui,sans-serif;'
    f'margin-bottom:1.5rem">'
    f'{"●" if _src != "fallback" else "○"} '
    f'{_price_label}'
    f'{(" · " + _age_str) if _age_str else ""}'
    f'{_changed_note}'
    f' &nbsp;·&nbsp; <span style="color:#3f3f46">source: LiteLLM</span>'
    f'</p>',
    unsafe_allow_html=True,
)

if "calc_text" in st.session_state:
    text = st.session_state["calc_text"]

    token_count = count_tokens(text, model="gpt-5", provider="openai")
    char_count  = len(text)
    word_count  = len(text.split())
    pages_est   = round(token_count / 500, 1)
    arch        = suggest_architecture(token_count, text)
    excluded_set = {m["model"] for m in arch.get("excluded_models", [])}

    if project_name:
        st.markdown(f'<p class="tm-result-title">{project_name}</p>', unsafe_allow_html=True)

    st.divider()

    # stats

    col_hero, col_sec = st.columns([2, 3])
    with col_hero:
        st.markdown(
            f'<div class="stat-hero">'
            f'<div class="stat-hero-val">{token_count:,}</div>'
            f'<div class="stat-hero-lbl">{T["viz_tokens"]} &nbsp;·&nbsp; gpt-5</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_sec:
        for col, val, lbl in zip(
            st.columns(3),
            [f"{char_count:,}", f"{word_count:,}", str(pages_est)],
            [T["characters"], T["words"], T["pages_est"]],
        ):
            with col:
                st.markdown(
                    f'<div class="stat-sec">'
                    f'<div class="stat-sec-val">{val}</div>'
                    f'<div class="stat-sec-lbl">{lbl}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # token efficiency

    chars_per_tok = char_count / token_count if token_count > 0 else 0
    tok_per_word  = token_count / word_count  if word_count  > 0 else 0
    _eff_key, eff_color = _efficiency_label(chars_per_tok / 4.0)
    scripts      = _detect_scripts(text)
    script_val   = " + ".join(scripts) if scripts else T["latin_ascii"]
    script_color = "#ef4444" if scripts else "#71717a"

    ec1, ec2, ec3, ec4 = st.columns(4)
    with ec1:
        st.markdown(
            f'<div class="eff-metric">'
            f'<div class="eff-metric-val" style="color:#fafafa">{chars_per_tok:.2f}</div>'
            f'<div class="eff-metric-lbl">{T["eff_chars_lbl"]}</div>'
            f'</div>', unsafe_allow_html=True)
    with ec2:
        st.markdown(
            f'<div class="eff-metric">'
            f'<div class="eff-metric-val" style="color:#fafafa">{tok_per_word:.2f}</div>'
            f'<div class="eff-metric-lbl">{T["eff_tokens_lbl"]}</div>'
            f'</div>', unsafe_allow_html=True)
    with ec3:
        st.markdown(
            f'<div class="eff-metric">'
            f'<div class="eff-metric-val" style="color:{eff_color}">{T[_eff_key]}</div>'
            f'<div class="eff-metric-lbl">{T["eff_label"]}</div>'
            f'</div>', unsafe_allow_html=True)
    with ec4:
        st.markdown(
            f'<div class="eff-metric">'
            f'<div class="eff-metric-val" style="color:{script_color};font-size:1rem">{script_val}</div>'
            f'<div class="eff-metric-lbl">{T["eff_script_lbl"]}</div>'
            f'</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    insight = _efficiency_insight(chars_per_tok, tok_per_word, arch["content_type"], scripts, st.session_state["lang"])
    st.markdown(f'<div class="insight-card">{insight}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # per-provider tokenization

    _active_providers = set(m["provider"] for m in MODEL_PRICING.values())
    providers_ordered: list[str] = [p for p in PROVIDERS if p in _active_providers]

    provider_tokens = {}
    provider_exact = {}
    provider_count = {}

    for provider in providers_ordered:
        model = PROVIDERS.get(provider, {}).get("model", "gpt-5")
        toks, is_exact = tm_tokenize(text, model=model, provider=provider)
        provider_tokens[provider] = toks
        provider_exact[provider]  = is_exact
        provider_count[provider]  = len(toks)

    # cost comparison

    rows = []
    for model, meta in MODEL_PRICING.items():
        provider = meta["provider"]
        tok      = provider_count.get(provider, token_count)
        cost_in  = calculate_cost(model, tok, 0)
        cost_out = calculate_cost(model, 0, tok)
        rows.append({
            "model": model, "provider": provider, "tokens": tok,
            "input_cost": cost_in, "output_cost": cost_out,
            "total_cost": cost_in + cost_out,
        })

    df = pd.DataFrame(rows).sort_values("input_cost").reset_index(drop=True)
    eligible_df = df[~df["model"].isin(excluded_set)]

    col_chart, col_table = st.columns([3, 2])

    with col_chart:
        st.markdown(f'<p class="tm-section-label">{T["section_cost_input"]}</p>', unsafe_allow_html=True)

        bar_colors = []
        for _, row in df.iterrows():
            if row["model"] in excluded_set:
                bar_colors.append("rgba(39,39,42,0.30)")
            else:
                bar_colors.append(_hex_rgba(_pcolor(row["provider"]), 0.18))

        if not eligible_df.empty:
            cheapest_idx = eligible_df["input_cost"].idxmin()
            bar_colors[cheapest_idx] = _pcolor(df.loc[cheapest_idx, "provider"])

        y_labels = [
            f"{m}  ✗" if m in excluded_set else m
            for m in df["model"]
        ]

        fig = go.Figure(go.Bar(
            x=df["input_cost"], y=y_labels, orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"${v:.6f}" for v in df["input_cost"]],
            textposition="outside",
            textfont=dict(
                color=["#3f3f46" if m in excluded_set else "#52525b" for m in df["model"]],
                size=10,
            ),
            hovertemplate="<b>%{y}</b><br>$%{x:.7f}<extra></extra>",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#71717a", size=11, family="system-ui, sans-serif"),
            margin=dict(l=0, r=90, t=4, b=0),
            height=max(300, len(df) * 30),
            xaxis=dict(showgrid=True, gridcolor="#1f1f23", zeroline=False,
                       tickformat=".6f", tickprefix="$"),
            yaxis=dict(showgrid=False, zeroline=False, autorange="reversed"),
            showlegend=False,
            hoverlabel=dict(bgcolor="#111114", font_color="#fafafa", bordercolor="#27272a"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        if excluded_set:
            exc_count = len(arch["excluded_models"])
            est_out   = arch.get("estimated_output_tokens", 0)
            exc_list  = ", ".join(
                f'{m["model"]} (−{m["shortfall"]:,} tokens)'
                for m in sorted(arch["excluded_models"], key=lambda x: x["shortfall"])
            )
            st.markdown(
                f'<div style="background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.15);'
                f'border-radius:8px;padding:10px 14px;margin-top:4px;'
                f'font-size:11.5px;color:#fca5a5;font-family:system-ui,sans-serif;line-height:1.65">'
                f'<b style="color:#ef4444">{exc_count} {T["models_excluded"]}</b>: {T["ctx_too_small"]} '
                f'{token_count:,} {T["ctx_input_plus"]}{est_out:,} {T["ctx_estimated_out"]}.<br>'
                f'<span style="color:#52525b">{exc_list}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_table:
        st.markdown(f'<p class="tm-section-label">{T["section_breakdown"]}</p>', unsafe_allow_html=True)
        display_df = df[["model", "provider", "tokens", "input_cost", "total_cost"]].copy()
        display_df["fits"] = df["model"].apply(lambda m: "✓" if m not in excluded_set else "✗")
        display_df.columns = [T["df_model"], T["df_provider"], T["df_tokens"], T["df_input"], T["df_inout"], T["df_fits"]]
        display_df[T["df_tokens"]]  = display_df[T["df_tokens"]].map(lambda v: f"{v:,}")
        display_df[T["df_input"]]   = display_df[T["df_input"]].map(lambda v: f"${v:.6f}")
        display_df[T["df_inout"]]   = display_df[T["df_inout"]].map(lambda v: f"${v:.6f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True,
                     height=min(520, len(df) * 38 + 40))

    # cost receipt

    st.markdown(f'<p class="tm-section-label">{T["cost_formula_lbl"]}</p>', unsafe_allow_html=True)
    st.markdown(
        '<div style="background:#0d0d0f;border:1px solid #1f1f23;border-radius:8px;'
        'padding:12px 18px;margin-bottom:14px;font-family:\'SF Mono\',monospace;font-size:11px;'
        'color:#52525b;line-height:2">'
        'cost = <span style="color:#a1a1aa">(input_tokens ÷ 1,000,000) × input_$/M</span>'
        ' <span style="color:#3f3f46">+</span> '
        '<span style="color:#a1a1aa">(output_tokens ÷ 1,000,000) × output_$/M</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="background:rgba(0,191,165,.06);border:1px solid rgba(0,191,165,.2);'
        f'border-radius:8px;padding:14px 18px;margin-bottom:14px">'

        f'<div style="font-size:10px;font-weight:600;color:#00BFA5;letter-spacing:.05em;'
        f'text-transform:uppercase;font-family:system-ui,sans-serif;margin-bottom:8px">'
        f'{T["devin_title"]}'
        f'</div>'

        f'<div style="font-size:12px;color:#a1a1aa;font-family:system-ui,sans-serif;line-height:1.75">'
        f'{T["devin_body"]}'
        f'</div>'

        f'<div style="margin:10px 0 6px;font-family:\'SF Mono\',monospace;font-size:11px;'
        f'color:#52525b;background:#0d0d0f;border-radius:6px;padding:10px 14px;line-height:2">'
        f'{T["devin_formula"]}'
        f'</div>'

        f'<div style="font-size:11px;color:#52525b;font-family:system-ui,sans-serif;line-height:1.65">'
        f'{T["devin_note"]}'
        f'</div>'

        f'</div>',
        unsafe_allow_html=True,
    )

    _cheapest_eligible = (
        eligible_df.iloc[0]["model"] if not eligible_df.empty else df.iloc[0]["model"]
    )
    _RECEIPT_MODELS = [_cheapest_eligible, "gpt-4o", "claude-opus-4"]
    seen_r: set = set()
    receipt_models = [m for m in _RECEIPT_MODELS
                      if m in MODEL_PRICING and not (m in seen_r or seen_r.add(m))]  # type: ignore[func-returns-value]

    rcols = st.columns(len(receipt_models))
    for col, rmodel in zip(rcols, receipt_models):
        meta      = MODEL_PRICING[rmodel]
        provider  = meta["provider"]
        in_price  = meta["input"]
        out_price = meta["output"]
        in_cost   = token_count * in_price
        out_cost  = token_count * out_price
        total_r   = in_cost + out_cost
        in_per_m  = in_price  * 1_000_000
        out_per_m = out_price * 1_000_000
        is_acu    = provider in _ACU_PROVIDERS

        if is_acu:
            acu_cost   = total_r
            acu_count  = acu_cost / 2.25
            body_html  = (
                f'<div class="receipt-line">'
                f'  <span>{token_count:,} tokens (est.)</span>'
                f'  <span class="receipt-line-val">× ${in_per_m:.4f}/M</span>'
                f'</div>'
                f'<div class="receipt-line">'
                f'  <span class="receipt-line-result">= ${total_r:.6f}</span>'
                f'</div>'
                f'<div class="receipt-line" style="margin-top:6px;color:#3f3f46">'
                f'  <span>≈ {acu_count:.4f} ACUs × $2.25</span>'
                f'</div>'
                f'<div class="receipt-line" style="font-size:10px;color:#3f3f46;margin-top:4px">'
                f'  <span>{T["receipt_acu_note"]}</span>'
                f'</div>'
            )
        else:
            body_html = (
                f'<div class="receipt-line">'
                f'  <span>{token_count:,} {T["receipt_input_tkns"]}</span>'
                f'  <span class="receipt-line-val">× ${in_per_m:.4f}/M</span>'
                f'</div>'
                f'<div class="receipt-line">'
                f'  <span class="receipt-line-result">= ${in_cost:.6f}</span>'
                f'</div>'
                f'<div class="receipt-line" style="margin-top:6px">'
                f'  <span>{token_count:,} {T["receipt_out_tkns"]}</span>'
                f'  <span class="receipt-line-val">× ${out_per_m:.4f}/M</span>'
                f'</div>'
                f'<div class="receipt-line">'
                f'  <span class="receipt-line-result">= ${out_cost:.6f}</span>'
                f'</div>'
            )

        with col:
            st.markdown(
                f'<div class="receipt">'
                f'<div class="receipt-label">{PROVIDERS.get(provider, {}).get("display", provider.title())}</div>'
                f'<div class="receipt-model">{rmodel}</div>'
                f'{body_html}'
                f'<hr class="receipt-sep">'
                f'<div class="receipt-total">'
                f'  <span>{T["receipt_total"]}</span>'
                f'  <span class="receipt-total-val">${total_r:.6f}</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # Context Window Meter

    st.markdown(f'<p class="tm-section-label">{T["section_ctx"]}</p>', unsafe_allow_html=True)

    ctx_cols = st.columns(len(providers_ordered))

    for col, provider in zip(ctx_cols, providers_ordered):
        model      = PROVIDERS[provider]["model"]
        ctx_size   = CONTEXT_WINDOWS.get(model, 128_000)
        tok        = provider_count[provider]
        pct        = min(100.0, tok / ctx_size * 100)
        color      = _ctx_color(pct)
        exceeds    = tok > ctx_size
        pct_label  = f"{pct:.1f}%" if pct >= 0.1 else "<0.1%"
        tokens_str = f"{tok:,} / {_fmt_ctx(ctx_size)}"

        with col:
            warning_html = f'<div class="ctx-warning">{T["ctx_exceeds"]}</div>' if exceeds else ""
            tagline = PROVIDERS.get(provider, {}).get("tagline", "")
            tagline_html = (
                f'<div style="font-size:0.7rem;color:#FF9900;margin-bottom:10px;'
                f'font-style:italic;font-family:system-ui,sans-serif;line-height:1.4">'
                f'{tagline}</div>'
            ) if tagline else ""
            st.markdown(
                f'<div class="ctx-card">'
                f'<div class="ctx-provider">{PROVIDERS.get(provider, {}).get("display", provider.upper())}</div>'
                f'<div class="ctx-model-name">{model}</div>'
                f'{tagline_html}'
                f'<div class="ctx-numbers">'
                f'  <div class="ctx-pct-big" style="color:{color}">{pct_label}</div>'
                f'  <div class="ctx-window-size">{_fmt_ctx(ctx_size)} {T["ctx_exceeds"][:3] if False else "ctx"}</div>'
                f'</div>'
                f'<div class="ctx-track"><div class="ctx-fill" style="width:{min(pct,100):.2f}%;background:{color}"></div></div>'
                f'<div class="ctx-tokens-label">{tokens_str} {T["viz_tokens"]}</div>'
                f'{warning_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Prompt Caching ROI

    st.markdown(f'<p class="tm-section-label">{T["section_cache"]}</p>', unsafe_allow_html=True)

    cache_cols = st.columns(len(providers_ordered))
    SAMPLE_VOLUMES = [10, 100, 1_000]

    for col, provider in zip(cache_cols, providers_ordered):
        model      = PROVIDERS[provider]["model"]
        cache_info = CACHING.get(provider, {"supported": False})
        tok        = provider_count[provider]
        base_cost  = calculate_cost(model, tok, 0)
        supported  = cache_info.get("supported", False)
        min_tok    = cache_info.get("min_tokens", 1024)
        eligible   = supported and tok >= min_tok

        with col:
            if not eligible:
                reason = T["cache_not_supported"] if not supported else T["cache_need_tokens"].format(n=_fmt_ctx(min_tok))
                st.markdown(
                    f'<div class="cache-card">'
                    f'<div class="cache-provider">{PROVIDERS.get(provider, {}).get("display", provider.upper())}</div>'
                    f'<div class="cache-disabled">{reason}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                continue

            breakeven = caching_breakeven(base_cost, cache_info)
            rows_html = ""
            for n in SAMPLE_VOLUMES:
                no_c   = base_cost * n
                with_c = caching_cost(base_cost, cache_info, n)
                saving = no_c - with_c
                saving_pct = saving / no_c * 100 if no_c > 0 else 0
                rows_html += (
                    f'<div class="cache-row">'
                    f'<span class="cache-row-lbl">{n:,} {T["cache_calls"]}</span>'
                    f'<span class="cache-row-val">${with_c:.4f}</span>'
                    f'<span class="cache-row-saving">-{saving_pct:.0f}%</span>'
                    f'</div>'
                )

            st.markdown(
                f'<div class="cache-card">'
                f'<div class="cache-provider">{PROVIDERS.get(provider, {}).get("display", provider.upper())}</div>'
                f'<div class="cache-breakeven">{breakeven}×</div>'
                f'<div class="cache-breakeven-lbl">{T["cache_breakeven_lbl"]}</div>'
                f'{rows_html}'
                f'<div class="cache-note">{cache_info.get("note","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # token visualizer

    st.markdown(f'<p class="tm-section-label">{T["section_token_breaks"]}</p>', unsafe_allow_html=True)

    _ANATOMY_COLORS = {
        "whole": "#22c55e",
        "subword": "#f59e0b",
        "numeric": "#6366f1",
        "punct": "#71717a",
        "space": "#27272a",
        "other": "#3f3f46",
    }
    _ANATOMY_LABELS = {
        "whole": T["anatomy_whole"], "subword": T["anatomy_subword"],
        "numeric": T["anatomy_numeric"], "punct": T["anatomy_punct"],
        "space": T["anatomy_space"], "other": T["anatomy_other"],
    }

    viz_tabs = st.tabs([PROVIDERS.get(p, {}).get("display", p.title()) for p in providers_ordered])
    for provider, tab in zip(providers_ordered, viz_tabs):
        with tab:
            p_model  = PROVIDERS.get(provider, {}).get("model", "gpt-5")
            p_tok    = provider_count[provider]
            p_exact  = provider_exact[provider]

            tagline = PROVIDERS.get(provider, {}).get("tagline", "")
            if tagline:
                pcolor = _pcolor(provider)
                st.markdown(
                    f'<div style="margin-bottom:10px;padding:8px 14px;'
                    f'border-left:3px solid {pcolor};background:{pcolor}12;'
                    f'border-radius:0 6px 6px 0;font-size:0.82rem;'
                    f'color:{pcolor};font-style:italic;font-family:system-ui,sans-serif">'
                    f'{tagline}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                _viz_insight(provider, p_tok, provider_count, p_model, p_exact, char_count, T),
                unsafe_allow_html=True,
            )

            anatomy = _token_anatomy(provider_tokens[provider])
            total_a = anatomy["total"] or 1
            bar_segs = "".join(
                f'<div style="flex:{anatomy[k]/total_a*100:.2f};background:{_ANATOMY_COLORS[k]}"></div>'
                for k in ["whole", "subword", "numeric", "punct", "space", "other"]
                if anatomy[k] > 0
            )
            legend_items = "".join(
                f'<div class="anatomy-item">'
                f'<div class="anatomy-dot" style="background:{_ANATOMY_COLORS[k]}"></div>'
                f'{anatomy[k]:,} {_ANATOMY_LABELS[k]} ({anatomy[k]/total_a*100:.0f}%)'
                f'</div>'
                for k in ["whole", "subword", "numeric", "punct", "space", "other"]
                if anatomy[k] > 0
            )
            st.markdown(
                f'<div class="anatomy-bar">{bar_segs}</div>'
                f'<div class="anatomy-legend">{legend_items}</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                _render_token_viz(provider_tokens[provider], p_exact, p_model, T),
                unsafe_allow_html=True,
            )

    st.divider()

    # Multi-turn Conversation Cost Projector

    st.markdown(f'<p class="tm-section-label">{T["section_multiturn"]}</p>', unsafe_allow_html=True)
    st.caption(T["mt_caption"])

    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 3])
    with ctrl1:
        n_turns = st.slider(T["mt_turns"], min_value=2, max_value=60, value=20, step=1)
    with ctrl2:
        output_pct = st.slider(T["mt_output_pct"], min_value=10, max_value=150, value=40, step=5)
    with ctrl3:
        mt_model = st.selectbox(
            T["mt_model"],
            options=list(MODEL_PRICING.keys()),
            index=list(MODEL_PRICING.keys()).index("gpt-5") if "gpt-5" in MODEL_PRICING else 0,
        )

    mt_provider  = MODEL_PRICING[mt_model]["provider"]
    cache_info   = CACHING.get(mt_provider, {"supported": False})
    tok_for_mt   = provider_count.get(mt_provider, token_count)
    eligible_mt  = cache_info.get("supported") and tok_for_mt >= cache_info.get("min_tokens", 1024)

    no_cache_series, cache_series = _multiturn_series(mt_model, tok_for_mt, n_turns, output_pct)

    turns_x  = [t for t, _ in no_cache_series]
    costs_nc = [c for _, c in no_cache_series]
    costs_c  = [c for _, c in cache_series]

    fig_mt = go.Figure()

    fig_mt.add_trace(go.Scatter(
        x=turns_x, y=costs_nc,
        mode="lines",
        name=T["mt_no_cache"],
        line=dict(color="#3f3f46", width=2),
        hovertemplate=f'{T["mt_axis_turn"]} %{{x}}<br>$%{{y:.5f}} total<extra>{T["mt_no_cache"]}</extra>',
    ))

    if eligible_mt:
        fig_mt.add_trace(go.Scatter(
            x=turns_x, y=costs_c,
            mode="lines",
            name=T["mt_with_cache"],
            line=dict(color="#f59e0b", width=2.5),
            hovertemplate=f'{T["mt_axis_turn"]} %{{x}}<br>$%{{y:.5f}} total<extra>{T["mt_with_cache"]}</extra>',
        ))
        fig_mt.add_trace(go.Scatter(
            x=turns_x + turns_x[::-1],
            y=costs_nc + costs_c[::-1],
            fill="toself",
            fillcolor="rgba(245,158,11,0.05)",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))

    final_nc = costs_nc[-1] if costs_nc else 0
    final_c  = costs_c[-1]  if costs_c  else 0
    saving   = final_nc - final_c

    fig_mt.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#71717a", size=11, family="system-ui, sans-serif"),
        margin=dict(l=0, r=20, t=16, b=0),
        height=280,
        xaxis=dict(showgrid=True, gridcolor="#1f1f23", zeroline=False,
                   title=T["mt_axis_turn"], title_font=dict(color="#52525b", size=11)),
        yaxis=dict(showgrid=True, gridcolor="#1f1f23", zeroline=False,
                   title=T["mt_axis_cost"], title_font=dict(color="#52525b", size=11),
                   tickprefix="$"),
        legend=dict(
            bgcolor="rgba(17,17,20,.9)", bordercolor="#27272a", borderwidth=1,
            font=dict(color="#a1a1aa", size=11),
        ),
        hoverlabel=dict(bgcolor="#111114", font_color="#fafafa", bordercolor="#27272a"),
    )
    st.plotly_chart(fig_mt, use_container_width=True, config={"displayModeBar": False})

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f'<div class="stat-sec">'
            f'<div class="stat-sec-val">${final_nc:.4f}</div>'
            f'<div class="stat-sec-lbl">{T["mt_total_no_cache"].format(n=n_turns)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m2:
        if eligible_mt:
            st.markdown(
                f'<div class="stat-sec">'
                f'<div class="stat-sec-val" style="color:#f59e0b">${final_c:.4f}</div>'
                f'<div class="stat-sec-lbl">{T["mt_total_cache"].format(n=n_turns)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="stat-sec">'
                f'<div class="stat-sec-val" style="color:#3f3f46">-</div>'
                f'<div class="stat-sec-lbl">{T["mt_not_eligible"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with m3:
        if eligible_mt and saving > 0:
            pct_saved = saving / final_nc * 100
            st.markdown(
                f'<div class="stat-sec">'
                f'<div class="stat-sec-val" style="color:#f59e0b">${saving:.4f}</div>'
                f'<div class="stat-sec-lbl">{T["mt_saved"].format(pct=pct_saved)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="stat-sec">'
                f'<div class="stat-sec-val" style="color:#3f3f46">-</div>'
                f'<div class="stat-sec-lbl">{T["mt_savings"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # architecture recommendation

    st.markdown(f'<p class="tm-section-label">{T["section_arch"]}</p>', unsafe_allow_html=True)

    savings = arch["savings_vs_gpt4o_pct"]

    warnings_html = "".join(
        f'<div class="arch-warning">{w}</div>'
        for w in arch.get("warnings", [])
    )

    badges_html = (
        f'<span class="badge">{arch["content_type"]}</span>'
        f'<span class="badge">{arch["size"]} &nbsp;·&nbsp; {token_count:,} tokens</span>'
        f'<span class="badge">{arch["approach"]}</span>'
        + (f'<span class="badge badge-savings">{T["badge_saves"].format(n=savings)}</span>' if savings > 0 else "")
    )

    steps_html = "".join(
        f'<div class="step-card">'
        f'<div class="step-role">{s["role"]}</div>'
        f'<div class="step-model">{s["model"]}</div>'
        f'<div class="step-desc">{s["desc"]}</div>'
        f'<div class="step-why">{s.get("why", "")}</div>'
        f'<div class="step-footer">'
        f'<span class="step-cost">${s["cost"]:.6f}</span>'
        f'<span class="step-tokens">{s.get("input_tokens", 0):,} in / {s.get("output_tokens", 0):,} out</span>'
        f'</div>'
        f'</div>'
        for s in arch["steps"]
    )

    total_line = (
        f'<p style="color:#52525b;font-size:12px;margin-top:14px;font-family:system-ui,sans-serif">'
        f'{T["pipeline_total"]} '
        f'<span style="color:#fafafa;font-family:\'SF Mono\',monospace">${arch["total_cost"]:.6f}</span>'
        f'</p>'
    )

    cache_tip_html = (
        f'<div class="arch-cache-tip">'
        f'<div class="arch-cache-tip-label">Caching</div>'
        f'{arch["caching_tip"]}'
        f'</div>'
    ) if arch.get("caching_tip") else ""

    best_model = arch["steps"][-1]["model"]
    tiers_html = "".join(
        f'<div class="tier-card{"  active" if t["model"] == best_model else ""}">'
        f'<div class="tier-label">{t["label"]}</div>'
        f'<div class="tier-model">{t["model"]}</div>'
        f'<div class="tier-provider">{t["provider"]}</div>'
        f'<div class="tier-cost">${t["cost"]:.6f}</div>'
        f'<div class="tier-note">{t["note"]}</div>'
        f'</div>'
        for t in arch.get("tiers", [])
    )

    tips_items_html = "".join(
        f'<div class="arch-tip"><span>{t}</span></div>'
        for t in arch.get("content_tips", [])
    )
    tips_section_html = (
        f'<div style="margin-top:20px">'
        f'<p class="tm-section-label">{T["section_best_practices"]}: {arch["content_type"]}</p>'
        f'<div class="content-card" style="padding:16px 24px">{tips_items_html}</div>'
        f'</div>'
    ) if tips_items_html else ""

    st.markdown(
        f'{warnings_html}'
        f'<div class="content-card">'
        f'<div style="margin-bottom:14px">{badges_html}</div>'
        f'<p style="font-size:1rem;font-weight:600;color:#fafafa;margin-bottom:6px;font-family:system-ui,sans-serif">{arch["headline"]}</p>'
        f'<p style="font-size:0.87rem;color:#52525b;line-height:1.65;margin-bottom:18px;font-family:system-ui,sans-serif">{arch["rationale"]}</p>'
        f'{steps_html}{total_line}{cache_tip_html}'
        f'</div>'
        f'<div style="margin-top:16px">'
        f'<p class="tm-section-label">{T["section_tiers"]}</p>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">'
        f'{tiers_html}'
        f'</div>'
        f'</div>'
        f'{tips_section_html}',
        unsafe_allow_html=True,
    )

    # prompt compressor

    st.markdown(f'<p class="tm-section-label" style="margin-top:2rem">{T["section_compress"]}</p>', unsafe_allow_html=True)

    comp = _analyze_compression(text, token_count)
    saveable = comp["total_saveable"]
    pct_save = (saveable / token_count * 100) if token_count else 0
    if saveable == 0:
        st.markdown(
            f'<div class="content-card"><p style="color:#52525b;font-size:0.87rem">{T["compress_none"]}</p></div>',
            unsafe_allow_html=True,
        )
    else:
        _gpt5_meta = MODEL_PRICING.get("gpt-5", {})
        cost_per_token_gpt5 = _gpt5_meta.get("input", 0.00000125)
        saved_cost = saveable * cost_per_token_gpt5
        insight = T["compress_insight"].format(n=saveable, pct=pct_save, cost=saved_cost)
        c1, c2, c3, c4 = st.columns(4)
        for col, val, lbl in [
            (c1, saveable, T["compress_total"]),
            (c2, comp["comment_tokens"], T["compress_comments"]),
            (c3, comp["stopword_tokens"], T["compress_stopwords"]),
            (c4, comp["repeated_tokens"], T["compress_repeated"]),
        ]:
            col.markdown(
                f'<div class="stat-sec"><div class="stat-sec-val">{val:,}</div>'
                f'<div class="stat-sec-lbl">{lbl}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="content-card" style="margin-top:8px">'
            f'<p style="color:#a1a1aa;font-size:0.87rem;line-height:1.65">{insight}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # token hotspot

    st.markdown(f'<p class="tm-section-label" style="margin-top:2rem">{T["section_hotspot"]}</p>', unsafe_allow_html=True)

    hotspot_html = _token_hotspot_html(text)
    legend = (
        f'<span style="color:#22c55e;margin-right:12px">■ {T["hotspot_light"]}</span>'
        f'<span style="color:#f59e0b;margin-right:12px">■ {T["hotspot_medium"]}</span>'
        f'<span style="color:#ef4444">■ {T["hotspot_dense"]}</span>'
    )
    st.markdown(
        f'<div class="content-card">'
        f'<div style="font-size:0.75rem;margin-bottom:12px;color:#52525b">{legend}</div>'
        f'{hotspot_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # budget calculator

    st.markdown(f'<p class="tm-section-label" style="margin-top:2rem">{T["section_budget"]}</p>', unsafe_allow_html=True)

    budget = st.slider(T["budget_slider"], min_value=10, max_value=5000, value=100, step=10)
    _budget_candidates = [
        ("GPT-4o", "openai", "gpt-4o"),
        ("GPT-5", "openai", "gpt-5"),
        ("Claude Opus 4", "anthropic", "claude-opus-4"),
        ("Gemini 1.5 Pro", "google", "gemini-1.5-pro"),
        ("DeepSeek R1", "deepseek", "deepseek-r1"),
        ("Mistral Large", "mistral", "mistral-large"),
    ]
    budget_models = [(lbl, prov, mk) for lbl, prov, mk in _budget_candidates if mk in MODEL_PRICING]
    budget_rows = []
    for label, provider, model_key in budget_models:
        cost_per_call = calculate_cost(model_key, token_count, int(token_count * 0.3)) or 0
        if cost_per_call <= 0:
            continue
        calls_month = int(budget / cost_per_call)
        calls_day = max(1, calls_month // 30)
        budget_rows.append({
            "Model": label,
            "$/call": f"${cost_per_call:.6f}",
            T["budget_calls_month"]: f"{calls_month:,}",
            T["budget_calls_day"]: f"{calls_day:,}",
        })
    if budget_rows:
        st.dataframe(
            pd.DataFrame(budget_rows),
            use_container_width=True,
            hide_index=True,
        )

    # cost scaling

    st.markdown(f'<p class="tm-section-label" style="margin-top:2rem">{T["section_breakeven"]}</p>', unsafe_allow_html=True)

    output_ratio = st.slider(T["scaling_output_ratio"], min_value=0.1, max_value=2.0, value=0.3, step=0.1)
    scaling_models = [
        ("GPT-4o", "openai", "gpt-4o", "#10A37F"),
        ("Claude Opus 4", "anthropic", "claude-opus-4", "#D4722E"),
        ("Gemini 1.5 Pro", "google", "gemini-1.5-pro", "#4285F4"),
        ("DeepSeek R1", "deepseek", "deepseek-r1", "#5865F2"),
    ]
    token_steps = list(range(500, 50001, 500))
    fig_scale = go.Figure()
    for label, provider, model_key, color in scaling_models:
        costs = [calculate_cost(model_key, t, int(t * output_ratio)) or 0 for t in token_steps]
        fig_scale.add_trace(go.Scatter(
            x=token_steps, y=costs, name=label,
            line=dict(color=color, width=2), mode="lines",
        ))
    fig_scale.add_vline(
        x=token_count, line_dash="dash", line_color="#f59e0b",
        annotation_text=T["scaling_current"], annotation_font_color="#f59e0b",
    )
    fig_scale.update_layout(
        paper_bgcolor="#111114", plot_bgcolor="#111114",
        font=dict(color="#71717a", family="system-ui", size=12),
        xaxis=dict(title="tokens", gridcolor="#1f1f23", color="#52525b"),
        yaxis=dict(title="USD / call", gridcolor="#1f1f23", color="#52525b"),
        legend=dict(bgcolor="#111114", font=dict(color="#a1a1aa")),
        margin=dict(l=0, r=0, t=10, b=10), height=300,
    )
    st.plotly_chart(fig_scale, use_container_width=True)

    # template analyzer

    st.markdown(f'<p class="tm-section-label" style="margin-top:2rem">{T["section_template"]}</p>', unsafe_allow_html=True)

    tmpl = _analyze_template(text, token_count)
    if not tmpl["vars"]:
        st.markdown(
            f'<div class="content-card"><p style="color:#52525b;font-size:0.87rem">{T["template_none"]}</p></div>',
            unsafe_allow_html=True,
        )
    else:
        vars_str = ", ".join(f'<code style="background:#1c1c1f;padding:1px 5px;border-radius:3px;color:#f59e0b">{{{v}}}</code>' for v in tmpl["vars"])
        c1, c2, c3 = st.columns(3)
        for col, val, lbl in [
            (c1, tmpl["fixed_tokens"], T["template_fixed"]),
            (c2, tmpl["var_tokens"], T["template_var"]),
            (c3, len(tmpl["vars"]), T["template_vars"]),
        ]:
            col.markdown(
                f'<div class="stat-sec"><div class="stat-sec-val">{val:,}</div>'
                f'<div class="stat-sec-lbl">{lbl}</div></div>',
                unsafe_allow_html=True,
            )
        cache_tip_model = "claude-opus-4"
        from tokenmesh.pricing.caching import caching_breakeven, CACHING as _CACHING
        _cache_tip_base = calculate_cost(cache_tip_model, tmpl["fixed_tokens"], 0)
        _cache_tip_info = _CACHING.get("anthropic", {"supported": False})
        breakeven_n = caching_breakeven(_cache_tip_base, _cache_tip_info)
        cache_tip_html_tmpl = ""
        if breakeven_n and breakeven_n < 100 and tmpl["fixed_tokens"] > 1024:
            cache_tip_html_tmpl = (
                f'<div style="margin-top:10px;padding:8px 12px;border-left:3px solid #f59e0b;'
                f'background:#f59e0b18;border-radius:0 6px 6px 0;font-size:0.8rem;color:#a1a1aa">'
                f'{T["template_cache_tip"].format(n=breakeven_n, model=cache_tip_model)}'
                f'</div>'
            )
        st.markdown(
            f'<div class="content-card">'
            f'<div style="margin-bottom:8px;font-size:0.8rem;color:#52525b">{vars_str}</div>'
            f'{cache_tip_html_tmpl}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Truncation simulator

    st.markdown('<p class="tm-section-label" style="margin-top:2rem">Truncation simulator</p>', unsafe_allow_html=True)

    trunc_model = st.selectbox(
        "Model",
        options=list(CONTEXT_WINDOWS.keys()),
        index=list(CONTEXT_WINDOWS.keys()).index("gpt-5") if "gpt-5" in CONTEXT_WINDOWS else 0,
        key="trunc_model",
        label_visibility="collapsed",
    )

    ctx_limit   = CONTEXT_WINDOWS[trunc_model]
    trunc_provider = MODEL_PRICING.get(trunc_model, {}).get("provider", "openai")
    trunc_toks, _  = tm_tokenize(text, model=trunc_model, provider=trunc_provider)
    trunc_count    = len(trunc_toks)
    fits           = trunc_count <= ctx_limit
    remaining      = ctx_limit - trunc_count

    # estimate character split point
    cpt = len(text) / trunc_count if trunc_count > 0 else 4.0
    safe_chars  = min(len(text), int(ctx_limit * cpt))
    safe_text   = text[:safe_chars]
    cut_text    = text[safe_chars:]

    # status bar
    used_pct = min(100.0, trunc_count / ctx_limit * 100)
    bar_color = _ctx_color(used_pct)
    st.markdown(
        f'<div style="background:#111114;border:1px solid #27272a;border-radius:10px;padding:20px 24px;margin-bottom:12px">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:10px">'
        f'<span style="font-size:0.8rem;color:#52525b;font-family:system-ui,sans-serif">{trunc_model}</span>'
        f'<span style="font-size:0.8rem;font-family:\'SF Mono\',monospace;color:{bar_color}">'
        f'{trunc_count:,} / {_fmt_ctx(ctx_limit)} tokens &nbsp;·&nbsp; {used_pct:.1f}%</span>'
        f'</div>'
        f'<div style="height:6px;background:#1f1f23;border-radius:3px;overflow:hidden;margin-bottom:12px">'
        f'<div style="height:100%;width:{used_pct:.2f}%;background:{bar_color};border-radius:3px;transition:width .3s"></div>'
        f'</div>'
        + (
            f'<div style="display:flex;gap:24px">'
            f'<div><div style="font-size:1.4rem;font-weight:800;color:#22c55e;font-family:system-ui,sans-serif;letter-spacing:-1px">'
            f'{remaining:,}</div><div style="font-size:0.72rem;color:#52525b;font-family:system-ui,sans-serif">tokens remaining</div></div>'
            f'<div><div style="font-size:1.4rem;font-weight:800;color:#22c55e;font-family:system-ui,sans-serif;letter-spacing:-1px">'
            f'{len(text):,}</div><div style="font-size:0.72rem;color:#52525b;font-family:system-ui,sans-serif">chars, all fit</div></div>'
            f'</div>'
            if fits else
            f'<div style="display:flex;gap:24px;margin-bottom:12px">'
            f'<div><div style="font-size:1.4rem;font-weight:800;color:#ef4444;font-family:system-ui,sans-serif;letter-spacing:-1px">'
            f'{trunc_count - ctx_limit:,}</div><div style="font-size:0.72rem;color:#52525b;font-family:system-ui,sans-serif">tokens over limit</div></div>'
            f'<div><div style="font-size:1.4rem;font-weight:800;color:#ef4444;font-family:system-ui,sans-serif;letter-spacing:-1px">'
            f'{len(cut_text):,}</div><div style="font-size:0.72rem;color:#52525b;font-family:system-ui,sans-serif">chars truncated</div></div>'
            f'<div><div style="font-size:1.4rem;font-weight:800;color:#f59e0b;font-family:system-ui,sans-serif;letter-spacing:-1px">'
            f'{len(safe_text):,}</div><div style="font-size:0.72rem;color:#52525b;font-family:system-ui,sans-serif">chars kept</div></div>'
            f'</div>'
        )
        + f'</div>',
        unsafe_allow_html=True,
    )

    if not fits:
        safe_preview  = safe_text[-300:] if len(safe_text) > 300 else safe_text
        cut_preview   = cut_text[:300]
        ellipsis_left = "…" if len(safe_text) > 300 else ""
        ellipsis_right = "…" if len(cut_text) > 300 else ""
        st.markdown(
            f'<div style="background:#0d0d0f;border:1px solid #27272a;border-radius:8px;'
            f'padding:16px 20px;font-family:\'SF Mono\',\'Fira Code\',monospace;font-size:0.8rem;'
            f'line-height:1.9;overflow-wrap:break-word;word-break:break-all">'

            f'<div style="font-size:0.7rem;color:#52525b;margin-bottom:10px;font-family:system-ui,sans-serif">'
            f'<span style="color:#22c55e">■</span> kept &nbsp;·&nbsp; '
            f'<span style="color:#ef4444">■</span> truncated &nbsp;·&nbsp; '
            f'<span style="color:#f59e0b">◀</span> cutoff point'
            f'</div>'

            f'<span style="color:#52525b">{ellipsis_left}</span>'
            f'<span style="color:#a1a1aa">{html_lib.escape(safe_preview)}</span>'
            f'<span style="background:#f59e0b;color:#0a0a0b;padding:0 4px;border-radius:2px;'
            f'font-size:0.7rem;margin:0 3px;vertical-align:middle">CUTOFF</span>'
            f'<span style="color:#ef4444;background:rgba(239,68,68,.1);border-radius:3px;padding:1px 3px">'
            f'{html_lib.escape(cut_preview)}</span>'
            f'<span style="color:#ef4444">{ellipsis_right}</span>'

            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.2);'
            f'border-radius:8px;padding:12px 16px;font-size:0.85rem;color:#86efac;'
            f'font-family:system-ui,sans-serif">'
            f'✓ This text fits entirely within the <b>{trunc_model}</b> context window '
            f'({_fmt_ctx(ctx_limit)} tokens). You have room for ~{int(remaining * cpt):,} more characters.'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # Semantic density

    st.markdown('<p class="tm-section-label" style="margin-top:0.5rem">Semantic density</p>', unsafe_allow_html=True)

    import re as _re

    _BOILERPLATE = [
        r"\bit is important to note\b", r"\bplease note that\b",
        r"\bin this (document|text|article|section)\b",
        r"\bas (mentioned|stated|discussed) (above|below|earlier|previously)\b",
        r"\bthis (document|text|section) (provides|discusses|explains|covers)\b",
        r"\bwith that (said|in mind)\b", r"\bneedless to say\b",
        r"\bfor the purposes of\b", r"\bin order to\b",
        r"\bit should be noted\b", r"\bfurthermore\b",
        r"\bmoreover\b", r"\bnevertheless\b",
    ]

    words_all   = text.lower().split()
    words_clean = [_re.sub(r"[^a-záéíóúàâêôãõüçñ]", "", w) for w in words_all]
    words_clean = [w for w in words_clean if len(w) > 1]
    unique_words = len(set(words_clean))
    total_words  = len(words_clean) or 1

    type_token_ratio = unique_words / total_words

    stopword_count = sum(1 for w in words_clean if w in _STOPWORDS_EN)
    stopword_pct   = stopword_count / total_words * 100

    repeated_pct = 0.0
    ngrams_sd: dict[str, int] = {}
    for n in (4, 5, 6):
        for i in range(len(words_all) - n + 1):
            g = " ".join(words_all[i:i+n])
            ngrams_sd[g] = ngrams_sd.get(g, 0) + 1
    repeated_phrases_sd = [(g, c) for g, c in ngrams_sd.items() if c > 1]
    repeated_tokens_sd  = sum((c - 1) * len(g.split()) for g, c in repeated_phrases_sd)
    repeated_pct = repeated_tokens_sd / token_count * 100 if token_count > 0 else 0

    boilerplate_matches = []
    for pat in _BOILERPLATE:
        found = _re.findall(pat, text.lower())
        boilerplate_matches.extend(found)
    boilerplate_tokens = len(boilerplate_matches) * 4
    boilerplate_pct    = boilerplate_tokens / token_count * 100 if token_count > 0 else 0

    # semantic density score: 0–100
    waste_pct = min(95, stopword_pct * 0.25 + repeated_pct * 0.5 + boilerplate_pct * 1.5)
    sem_density = max(5, round(100 - waste_pct))
    if sem_density >= 75:
        density_color, density_label = "#22c55e", "high"
    elif sem_density >= 50:
        density_color, density_label = "#f59e0b", "medium"
    else:
        density_color, density_label = "#ef4444", "low"

    sd1, sd2, sd3, sd4 = st.columns(4)
    for col, val, lbl, color in [
        (sd1, f"{sem_density}", "semantic density score", density_color),
        (sd2, f"{type_token_ratio:.2f}", "unique words / total", "#fafafa"),
        (sd3, f"{stopword_pct:.0f}%", "stopword overhead", "#71717a" if stopword_pct < 30 else "#f59e0b"),
        (sd4, f"{repeated_pct:.1f}%", "repeated token waste", "#71717a" if repeated_pct < 5 else "#ef4444"),
    ]:
        col.markdown(
            f'<div class="eff-metric">'
            f'<div class="eff-metric-val" style="color:{color}">{val}</div>'
            f'<div class="eff-metric-lbl">{lbl}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # density bar breakdown
    useful_pct_bar   = max(0, 100 - stopword_pct * 0.25 - repeated_pct * 0.5 - boilerplate_pct * 1.5)
    stop_bar         = min(stopword_pct * 0.25, 100 - useful_pct_bar)
    repeat_bar       = min(repeated_pct * 0.5, 100 - useful_pct_bar - stop_bar)
    boiler_bar       = min(boilerplate_pct * 1.5, 100 - useful_pct_bar - stop_bar - repeat_bar)

    st.markdown(
        f'<div style="background:#111114;border:1px solid #27272a;border-radius:10px;padding:20px 24px">'

        f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;margin-bottom:10px">'
        f'<div style="flex:{useful_pct_bar:.1f};background:#22c55e"></div>'
        f'<div style="flex:{stop_bar:.1f};background:#52525b"></div>'
        f'<div style="flex:{repeat_bar:.1f};background:#f59e0b"></div>'
        f'<div style="flex:{boiler_bar:.1f};background:#ef4444"></div>'
        f'</div>'

        f'<div style="display:flex;gap:18px;flex-wrap:wrap;margin-bottom:16px">'
        f'<div style="display:flex;align-items:center;gap:5px;font-size:0.72rem;color:#71717a;font-family:system-ui,sans-serif">'
        f'<div style="width:8px;height:8px;border-radius:2px;background:#22c55e"></div>unique content</div>'
        f'<div style="display:flex;align-items:center;gap:5px;font-size:0.72rem;color:#71717a;font-family:system-ui,sans-serif">'
        f'<div style="width:8px;height:8px;border-radius:2px;background:#52525b"></div>stopwords</div>'
        f'<div style="display:flex;align-items:center;gap:5px;font-size:0.72rem;color:#71717a;font-family:system-ui,sans-serif">'
        f'<div style="width:8px;height:8px;border-radius:2px;background:#f59e0b"></div>repetitions</div>'
        f'<div style="display:flex;align-items:center;gap:5px;font-size:0.72rem;color:#71717a;font-family:system-ui,sans-serif">'
        f'<div style="width:8px;height:8px;border-radius:2px;background:#ef4444"></div>boilerplate</div>'
        f'</div>'

        + (
            "".join(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:7px 0;border-top:1px solid #1f1f23;font-size:0.8rem;font-family:system-ui,sans-serif">'
                f'<span style="color:#52525b">repeated: <code style="background:#1c1c1f;padding:1px 5px;'
                f'border-radius:3px;color:#f59e0b;font-size:0.75rem">{html_lib.escape(g)}</code></span>'
                f'<span style="color:#f59e0b;font-family:\'SF Mono\',monospace">{c}×</span>'
                f'</div>'
                for g, c in sorted(repeated_phrases_sd, key=lambda x: -x[1])[:5]
            ) if repeated_phrases_sd else
            '<div style="font-size:0.8rem;color:#3f3f46;padding:8px 0;border-top:1px solid #1f1f23;'
            'font-family:system-ui,sans-serif">No repeated phrases detected.</div>'
        )

        + (
            "".join(
                f'<div style="padding:6px 0;border-top:1px solid #1f1f23;font-size:0.8rem;'
                f'font-family:system-ui,sans-serif;color:#52525b">'
                f'boilerplate: <span style="color:#ef4444">&ldquo;{html_lib.escape(m)}&rdquo;</span></div>'
                for m in boilerplate_matches[:3]
            ) if boilerplate_matches else ""
        )

        + f'<div style="margin-top:14px;padding:10px 14px;background:#0d0d0f;border-radius:6px;'
        f'font-size:0.82rem;color:#a1a1aa;font-family:system-ui,sans-serif;line-height:1.65">'
        f'<b style="color:{density_color}">Semantic density: {sem_density}/100 ({density_label}).</b> '
        + (
            f'Removing stopwords, deduplicating repeated phrases'
            + (f' and {len(boilerplate_matches)} boilerplate expression(s)' if boilerplate_matches else "")
            + f' could free ~{int(waste_pct / 100 * token_count):,} tokens '
            f'({waste_pct:.0f}%), equivalent to '
            f'<b style="color:#fafafa">${calculate_cost("gpt-5", int(waste_pct / 100 * token_count), 0):.6f}</b> per call on gpt-5.'
            if waste_pct > 5 else
            "This text has high semantic density. Most tokens carry unique information. No significant waste detected."
        )
        + f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.divider()

# Footer

import base64 as _b64
_foto_path = os.path.join(os.path.dirname(__file__), "foto_perfil.png")
try:
    with open(_foto_path, "rb") as _f:
        _foto_b64 = _b64.b64encode(_f.read()).decode()
    _foto_src = f"data:image/png;base64,{_foto_b64}"
except FileNotFoundError:
    _foto_src = ""

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    f'<div style="border-top:1px solid #1f1f23;padding:32px 0 24px;'
    f'display:flex;align-items:center;gap:20px;flex-wrap:wrap">'

    + (f'<img src="{_foto_src}" style="width:56px;height:56px;border-radius:50%;'
       f'object-fit:cover;flex-shrink:0;border:2px solid #27272a" />' if _foto_src else "")

    + (
        '<div>'
        '<div style="font-size:0.95rem;font-weight:700;color:#fafafa;'
        'font-family:system-ui,sans-serif;margin-bottom:4px">Cristiano Pires</div>'
        '<a href="https://www.linkedin.com/in/cristiano-p-a9039698/" target="_blank" '
        'style="display:inline-flex;align-items:center;gap:6px;color:#0A66C2;'
        'text-decoration:none;font-size:0.82rem;font-family:system-ui,sans-serif;font-weight:500">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="#0A66C2" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136'
        ' 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267'
        ' 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0'
        ' 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452z'
        'M22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227'
        ' 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>'
        'LinkedIn</a>'
        '</div>'
        '<div style="margin-left:auto">'
        '<span style="font-size:0.72rem;color:#27272a;font-family:system-ui,sans-serif">'
        'TokenMesh · open source · MIT</span>'
        '</div>'
        '</div>'
    ),
    unsafe_allow_html=True,
)
