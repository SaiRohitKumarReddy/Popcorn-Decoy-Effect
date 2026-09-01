import csv
import html
import hmac
import io
from datetime import datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


# ============================================================
# APP VERSION
# ============================================================

APP_VERSION = "3.1.0"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Movie Snack Choice",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# THEME
# ============================================================

NAVY = "#243B5A"
RED = "#B54A4A"

LIGHT_ORANGE = "#F1B56B"
LIGHT_ORANGE_HOVER = "#E6A24D"

BACKGROUND = "#F3F4F6"
SURFACE = "#FFFFFF"
TEXT = "#252A32"
MUTED = "#747A83"
BORDER = "#DDE1E5"

RED_SOFT = "#F8EEEE"
ORANGE_SOFT = "#FFF8EF"

# Popcorn visuals are self-contained SVG illustrations.
# Small, Medium, and Large use genuinely different bucket dimensions
# while keeping the same red-and-white cinema-popcorn visual family.


# ============================================================
# SAFE HTML HELPER
# ============================================================

def render_html(markup: str) -> None:
    compact_html = " ".join(
        line.strip()
        for line in markup.splitlines()
        if line.strip()
    )

    st.markdown(
        compact_html,
        unsafe_allow_html=True,
    )


def popcorn_bucket_svg(size_name: str) -> str:
    """Return one illustrated popcorn bucket with a true size-specific shape."""

    configs = {
        "Small": {
            "top_y": 58,
            "bottom_y": 101,
            "left_top": 41,
            "right_top": 79,
            "left_bottom": 45,
            "right_bottom": 75,
            "badge_y": 80,
            "badge_r": 9,
            "puffs": [
                (45, 56, 7),
                (52, 51, 8),
                (60, 53, 8),
                (68, 50, 8),
                (75, 56, 7),
                (59, 45, 7),
            ],
        },
        "Medium": {
            "top_y": 50,
            "bottom_y": 103,
            "left_top": 33,
            "right_top": 87,
            "left_bottom": 39,
            "right_bottom": 81,
            "badge_y": 77,
            "badge_r": 11,
            "puffs": [
                (35, 49, 8),
                (43, 44, 9),
                (52, 47, 9),
                (61, 42, 10),
                (70, 46, 9),
                (79, 43, 9),
                (86, 49, 8),
                (50, 38, 8),
                (68, 35, 8),
            ],
        },
        "Large": {
            "top_y": 42,
            "bottom_y": 106,
            "left_top": 23,
            "right_top": 97,
            "left_bottom": 31,
            "right_bottom": 89,
            "badge_y": 74,
            "badge_r": 13,
            "puffs": [
                (24, 42, 9),
                (32, 36, 10),
                (42, 40, 10),
                (51, 32, 11),
                (61, 37, 10),
                (71, 31, 11),
                (81, 37, 10),
                (91, 34, 10),
                (98, 42, 9),
                (39, 29, 9),
                (58, 24, 10),
                (79, 24, 9),
            ],
        },
    }

    config = configs.get(size_name)
    if config is None:
        return ""

    top_y = config["top_y"]
    bottom_y = config["bottom_y"]
    left_top = config["left_top"]
    right_top = config["right_top"]
    left_bottom = config["left_bottom"]
    right_bottom = config["right_bottom"]

    def interpolate(left: float, right: float, fraction: float) -> float:
        return left + ((right - left) * fraction)

    stripe_ranges = [
        (0.00, 0.13),
        (0.27, 0.40),
        (0.54, 0.67),
        (0.81, 0.94),
    ]

    stripe_svg = ""
    for start, end in stripe_ranges:
        top_x1 = interpolate(left_top, right_top, start)
        top_x2 = interpolate(left_top, right_top, end)
        bottom_x1 = interpolate(left_bottom, right_bottom, start)
        bottom_x2 = interpolate(left_bottom, right_bottom, end)

        stripe_svg += (
            f'<polygon points="{top_x1:.1f},{top_y + 3} '
            f'{top_x2:.1f},{top_y + 3} '
            f'{bottom_x2:.1f},{bottom_y - 2} '
            f'{bottom_x1:.1f},{bottom_y - 2}" '
            'fill="#F04A3E" />'
        )

    puff_svg = ""
    for index, (cx, cy, radius) in enumerate(config["puffs"]):
        kernel_x = cx + (2 if index % 2 == 0 else -2)
        kernel_y = cy + 1
        puff_svg += (
            '<g>'
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
            'fill="#FFFDF7" stroke="#E7C36B" stroke-width="1.2" />'
            f'<circle cx="{cx - radius * 0.45:.1f}" cy="{cy + 1:.1f}" '
            f'r="{radius * 0.55:.1f}" fill="#FFF8DE" />'
            f'<circle cx="{cx + radius * 0.40:.1f}" cy="{cy - 1:.1f}" '
            f'r="{radius * 0.52:.1f}" fill="#FFFFFF" />'
            f'<circle cx="{kernel_x}" cy="{kernel_y}" r="1.5" fill="#E9A628" />'
            '</g>'
        )

    rim_left = left_top - 2
    rim_width = (right_top - left_top) + 4

    return f"""
        <div class="popcorn-visual-wrap">
            <svg
                class="popcorn-visual"
                viewBox="0 0 120 112"
                role="img"
                aria-label="{html.escape(size_name)} popcorn box"
                xmlns="http://www.w3.org/2000/svg"
            >
                <ellipse
                    cx="60"
                    cy="106"
                    rx="31"
                    ry="3.4"
                    fill="rgba(36,59,90,0.10)"
                />

                {puff_svg}

                <polygon
                    points="{left_top},{top_y} {right_top},{top_y}
                            {right_bottom},{bottom_y} {left_bottom},{bottom_y}"
                    fill="#FFFDF8"
                    stroke="#D9DDE3"
                    stroke-width="1.3"
                />

                {stripe_svg}

                <rect
                    x="{rim_left}"
                    y="{top_y - 1}"
                    width="{rim_width}"
                    height="6"
                    rx="2.2"
                    fill="#F04A3E"
                />

                <rect
                    x="{rim_left + 2}"
                    y="{top_y}"
                    width="{rim_width - 4}"
                    height="2"
                    rx="1"
                    fill="#FFFFFF"
                    opacity="0.9"
                />

                <circle
                    cx="60"
                    cy="{config['badge_y']}"
                    r="{config['badge_r']}"
                    fill="#FFFDF8"
                    stroke="#E58D3A"
                    stroke-width="2"
                />

                <circle
                    cx="60"
                    cy="{config['badge_y']}"
                    r="{config['badge_r'] - 3}"
                    fill="#FFFFFF"
                    opacity="0.96"
                />
            </svg>
        </div>
    """


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        html, body, [class*="css"], .stApp {{
            font-family:
                "Inter",
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }}

        body, .stApp {{
            font-size: 17px;
        }}

        button, input, textarea, select {{
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        }}

        .stApp {{
            background: {BACKGROUND};
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        #MainMenu,
        footer {{
            visibility: hidden;
        }}

        .block-container {{
            max-width: 960px;
            padding-top: 2.65rem;
            padding-bottom: 3rem;
        }}

        /* ==================================================
           TITLE
        ================================================== */

        .main-title {{
            margin: 0;
            text-align: left;
            color: {NAVY};
            font-size: 2.35rem;
            line-height: 1.10;
            font-weight: 800;
            letter-spacing: -0.035em;
        }}

        .title-spacer {{
            height: 1.15rem;
        }}

        /* ==================================================
           GENERIC BUTTONS
        ================================================== */

        button {{
            transition: all 0.12s ease !important;
        }}

        .stButton > button[kind="primary"],
        .stButton > button[data-testid="stBaseButton-primary"] {{
            background: {NAVY} !important;
            border-color: {NAVY} !important;
            color: #FFFFFF !important;
            box-shadow: none !important;
        }}

        /* Reliable orange hover for every clickable Streamlit button. */
        div.stButton > button:hover:not(:disabled),
        [data-testid="stButton"] > button:hover:not(:disabled),
        button[data-testid^="stBaseButton"]:hover:not(:disabled) {{
            background-color: {LIGHT_ORANGE_HOVER} !important;
            background: {LIGHT_ORANGE_HOVER} !important;
            border-color: {LIGHT_ORANGE_HOVER} !important;
            color: {NAVY} !important;
            transform: translateY(-1px) !important;
            box-shadow: none !important;
        }}

        div.stButton > button:hover:not(:disabled) p,
        div.stButton > button:hover:not(:disabled) span,
        [data-testid="stButton"] > button:hover:not(:disabled) p,
        [data-testid="stButton"] > button:hover:not(:disabled) span,
        button[data-testid^="stBaseButton"]:hover:not(:disabled) p,
        button[data-testid^="stBaseButton"]:hover:not(:disabled) span {{
            color: {NAVY} !important;
        }}

        .stButton > button[kind="secondary"],
        .stButton > button[data-testid="stBaseButton-secondary"] {{
            background: {SURFACE} !important;
            border-color: {BORDER} !important;
            color: {NAVY} !important;
            box-shadow: none !important;
        }}

        /* ==================================================
           CAPSULE BUTTONS
           Buttons placed inside Streamlit columns use this
           capsule treatment.
        ================================================== */

        div[data-testid="stHorizontalBlock"] .stButton > button {{
            width: 100% !important;
            height: 40px !important;
            min-height: 40px !important;
            padding: 0 0.78rem !important;
            border-radius: 999px !important;
            border: 1.5px solid {LIGHT_ORANGE} !important;
            font-size: 0.94rem !important;
            font-weight: 730 !important;
            line-height: 1 !important;
            letter-spacing: 0.01em !important;
            white-space: nowrap !important;
            box-shadow: none !important;
        }}

        div[data-testid="stHorizontalBlock"] .stButton > button p {{
            margin: 0 !important;
            font-size: 0.94rem !important;
            line-height: 1 !important;
            white-space: nowrap !important;
        }}

        div[data-testid="stHorizontalBlock"] .stButton > button:hover {{
            border-color: {LIGHT_ORANGE_HOVER} !important;
        }}

        /* ==================================================
           CONTENT
        ================================================== */

        .content-area {{
            margin-top: 1.2rem;
        }}

        .section-title {{
            color: {TEXT};
            font-size: 1.22rem;
            line-height: 1.2;
            font-weight: 740;
            letter-spacing: -0.018em;
            margin: 0;
        }}

        /* Name-entry heading: medium-sized and clearly readable. */
        .entry-label {{
            color: {TEXT};
            font-size: 1.16rem !important;
            line-height: 1.2;
            font-weight: 740;
            letter-spacing: -0.012em;
            margin: 0;
        }}

        .section-copy {{
            color: {MUTED};
            font-size: 0.98rem;
            line-height: 1.5;
            margin: 0.25rem 0 0 0;
        }}

        /* ==================================================
           NAME INPUT
           No surrounding form/card.
        ================================================== */

        .name-input-gap {{
            height: 0.5rem;
        }}

        [data-testid="stTextInput"] {{
            margin-bottom: 0.2rem;
        }}

        /* Keep the COMPLETE name field white and slightly taller. */
        [data-testid="stTextInput"] > div,
        [data-testid="stTextInput"] div[data-baseweb="input"],
        [data-testid="stTextInput"] div[data-baseweb="base-input"] {{
            background-color: {SURFACE} !important;
            background: {SURFACE} !important;
        }}

        [data-testid="stTextInput"] div[data-baseweb="input"] {{
            height: 50px !important;
            min-height: 50px !important;
            border-radius: 8px !important;
            border: 1px solid {BORDER} !important;
            background-color: {SURFACE} !important;
            background: {SURFACE} !important;
            box-shadow: none !important;
            box-sizing: border-box !important;
        }}

        [data-testid="stTextInput"] div[data-baseweb="base-input"] {{
            height: 48px !important;
            min-height: 48px !important;
            border-radius: 8px !important;
            background-color: {SURFACE} !important;
            background: {SURFACE} !important;
        }}

        [data-testid="stTextInput"] input {{
            height: 48px !important;
            min-height: 48px !important;
            border: 0 !important;
            border-radius: 8px !important;
            background-color: {SURFACE} !important;
            background: {SURFACE} !important;
            color: {TEXT} !important;
            font-size: 0.94rem !important;
            padding: 0 0.86rem !important;
            box-shadow: none !important;
            box-sizing: border-box !important;
        }}

        [data-testid="stTextInput"] input:-webkit-autofill,
        [data-testid="stTextInput"] input:-webkit-autofill:hover,
        [data-testid="stTextInput"] input:-webkit-autofill:focus {{
            -webkit-box-shadow: 0 0 0 1000px {SURFACE} inset !important;
            -webkit-text-fill-color: {TEXT} !important;
        }}

        [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {{
            border-color: {LIGHT_ORANGE} !important;
            box-shadow: 0 0 0 2px rgba(241,181,107,0.12) !important;
            background-color: {SURFACE} !important;
        }}

        /* ==================================================
           STUDENT SCENARIO HEADER
        ================================================== */

        .student-scenario-area {{
            margin-top: 3.35rem;
        }}

        .student-hello {{
            display: block;
            color: {TEXT};
            font-size: 1.82rem;
            line-height: 1.12;
            font-weight: 800;
            letter-spacing: -0.022em;
            margin: 0;
        }}

        .student-hello strong {{
            color: {NAVY};
            font-size: 1.82rem;
            font-weight: 850;
        }}

        .student-question-gap {{
            height: 1.35rem;
        }}

        /* ==================================================
           SCENARIO 1 -> SCENARIO 2 TRANSITION
        ================================================== */

        .scenario-transition-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-left: 4px solid {LIGHT_ORANGE};
            border-radius: 14px;
            min-height: 210px;
            padding: 1.55rem 1.45rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            box-sizing: border-box;
            box-shadow: 0 2px 7px rgba(36, 59, 90, 0.025);
        }}

        .scenario-transition-badge {{
            display: inline-flex;
            align-items: center;
            min-height: 34px;
            padding: 0.38rem 0.86rem;
            border-radius: 999px;
            border: 1.5px solid {LIGHT_ORANGE};
            background: {ORANGE_SOFT};
            color: {NAVY};
            font-size: 0.94rem;
            line-height: 1;
            font-weight: 790;
            letter-spacing: 0.025em;
            margin-bottom: 0.88rem;
            box-sizing: border-box;
        }}

        .scenario-transition-title {{
            color: {TEXT};
            font-size: 1.42rem;
            line-height: 1.25;
            font-weight: 790;
            letter-spacing: -0.018em;
            margin: 0;
        }}

        .scenario-transition-copy {{
            color: {MUTED};
            font-size: 1.04rem;
            line-height: 1.58;
            margin-top: 0.58rem;
        }}

        .scenario-transition-copy strong {{
            color: {NAVY};
            font-weight: 800;
        }}

        .scenario-transition-button-gap {{
            height: 1.05rem;
        }}

        .st-key-continue_scenario_2 button {{
            min-height: 46px !important;
            height: 46px !important;
            font-size: 1.00rem !important;
            padding-left: 1.05rem !important;
            padding-right: 1.05rem !important;
        }}

        .st-key-continue_scenario_2 button p {{
            font-size: 1.00rem !important;
        }}


        /* ==================================================
           QUESTION SCREEN
        ================================================== */

        .scenario-capsule {{
            display: inline-flex;
            align-items: center;
            min-height: 36px;
            padding: 0.42rem 0.92rem;
            border-radius: 999px;
            border: 1.5px solid {LIGHT_ORANGE};
            background: {SURFACE};
            color: {NAVY};
            font-size: 0.98rem;
            line-height: 1;
            font-weight: 790;
            letter-spacing: 0.02em;
            box-sizing: border-box;
        }}

        .scenario-to-question-gap {{
            height: 0.72rem;
        }}

        .question-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 14px;
            min-height: 84px;
            padding: 1.18rem 1.22rem;
            margin-top: 0;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 7px rgba(36, 59, 90, 0.025);
            box-sizing: border-box;
        }}

        .question {{
            color: {TEXT};
            font-size: 1.26rem;
            line-height: 1.28;
            font-weight: 750;
            letter-spacing: -0.012em;
            margin: 0;
        }}

        .question-hint {{
            color: {MUTED};
            font-size: 1.04rem;
            line-height: 1.4;
            margin: 0.68rem 0 0 0;
        }}

        /* ==================================================
           POPCORN OPTION CAPSULES
           These are Streamlit buttons, never radio controls.
           Their width is controlled by a short left column.
        ================================================== */

        .question-to-options-gap {{
            height: 0.92rem;
        }}

        .option-stack-gap {{
            height: 0.72rem;
        }}

        .options-to-submit-gap {{
            height: 0.92rem;
        }}

        .selected-note {{
            background: {ORANGE_SOFT};
            border-left: 3px solid {LIGHT_ORANGE};
            border-radius: 7px;
            color: {TEXT};
            padding: 0.58rem 0.72rem;
            margin: 0.72rem 0 0.78rem 0;
            font-size: 0.94rem;
            font-weight: 590;
        }}

        /* ==================================================
           SUBMIT RESPONSE BUTTON
           Remains a clear rectangular final action.
        ================================================== */

        .stButton > button {{
            min-height: 37px;
            border-radius: 7px;
            font-size: 0.92rem;
            font-weight: 730;
        }}

        /* Illustrated cinema-popcorn buckets with true Small/Medium/Large shapes. */
        .popcorn-visual-wrap {{
            height: 82px;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            margin-bottom: 0.30rem;
            line-height: 1;
        }}

        .popcorn-visual {{
            display: block;
            width: 108px;
            height: 82px;
            max-width: 100%;
            overflow: visible;
            filter: drop-shadow(0 2px 3px rgba(36, 59, 90, 0.08));
        }}

        .popcorn-visual-placeholder {{
            width: 1px;
            height: 1px;
        }}

        /* Keep the option capsules comfortably readable, but slightly more compact. */
        .stApp div[data-testid="stHorizontalBlock"] .st-key-popcorn_choice_small button,
        .stApp div[data-testid="stHorizontalBlock"] .st-key-popcorn_choice_medium button,
        .stApp div[data-testid="stHorizontalBlock"] .st-key-popcorn_choice_large button,
        .stApp div[data-testid="stHorizontalBlock"] .st-key-popcorn_choice_dont_know button {{
            min-height: 96px !important;
            height: 96px !important;
            font-size: 1.00rem !important;
            line-height: 1.30 !important;
            padding: 0.68rem 0.58rem !important;
        }}

        .stApp div[data-testid="stHorizontalBlock"] .st-key-popcorn_choice_small button p,
        .stApp div[data-testid="stHorizontalBlock"] .st-key-popcorn_choice_medium button p,
        .stApp div[data-testid="stHorizontalBlock"] .st-key-popcorn_choice_large button p,
        .stApp div[data-testid="stHorizontalBlock"] .st-key-popcorn_choice_dont_know button p {{
            margin: 0 !important;
            font-size: 1.00rem !important;
            line-height: 1.36 !important;
            white-space: normal !important;
            text-align: center !important;
        }}

        /* Make only the final submit action larger on the question area. */
        .st-key-submit_response button {{
            min-height: 50px !important;
            height: 50px !important;
            font-size: 1.00rem !important;
        }}

        .st-key-submit_response button p {{
            font-size: 1.00rem !important;
        }}

        /* Continue and Join are enlarged through their column widths;
           capsule height is controlled by the reliable column-button rule. */

        /* ==================================================
           SUCCESS
        ================================================== */

        .success-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 14px;
            min-height: 220px;
            padding: 1.75rem 1.50rem;
            margin-top: 0.85rem;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
            box-shadow: 0 2px 7px rgba(36, 59, 90, 0.025);
        }}

        .success-check {{
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 0.78rem auto;
            border-radius: 50%;
            border: 1.5px solid {LIGHT_ORANGE};
            background: {NAVY};
            color: white;
            font-size: 1.02rem;
            font-weight: 850;
        }}

        .success-title {{
            color: {TEXT};
            font-size: 1.38rem;
            line-height: 1.25;
            font-weight: 780;
            margin-bottom: 0.42rem;
        }}

        .success-copy {{
            color: {MUTED};
            font-size: 1.04rem;
            line-height: 1.65;
        }}

        .success-copy strong {{
            color: {NAVY};
        }}

        /* ==================================================
           PROFESSOR MODE
        ================================================== */

        .professor-login-wrap {{
            margin-top: 3.2rem;
        }}

        .professor-login-title {{
            color: {TEXT};
            font-size: 1.65rem;
            line-height: 1.2;
            font-weight: 790;
            letter-spacing: -0.02em;
            margin: 0;
        }}

        .professor-login-copy {{
            color: {MUTED};
            font-size: 1.00rem;
            line-height: 1.5;
            margin: 0.42rem 0 1rem 0;
        }}

        .professor-dashboard-head {{
            margin-top: 3rem;
            margin-bottom: 1.2rem;
        }}

        .professor-dashboard-title {{
            color: {TEXT};
            font-size: 1.72rem;
            line-height: 1.2;
            font-weight: 790;
            letter-spacing: -0.022em;
            margin: 0;
        }}

        .professor-dashboard-copy {{
            color: {MUTED};
            font-size: 0.98rem;
            line-height: 1.5;
            margin: 0.36rem 0 0 0;
        }}

        .prof-auto-refresh-capsule {{
            display: inline-flex;
            align-items: center;
            min-height: 34px;
            padding: 0.38rem 0.86rem;
            margin-top: 0.78rem;
            border-radius: 999px;
            border: 1.5px solid {LIGHT_ORANGE};
            background: {SURFACE};
            color: {NAVY};
            font-size: 0.70rem;
            line-height: 1;
            font-weight: 760;
            letter-spacing: 0.015em;
            box-sizing: border-box;
        }}

        .prof-auto-refresh-dot {{
            width: 7px;
            height: 7px;
            margin-right: 0.48rem;
            border-radius: 50%;
            background: {LIGHT_ORANGE_HOVER};
            flex: 0 0 auto;
        }}

        .prof-metric-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            min-height: 104px;
            padding: 1rem 0.82rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            box-sizing: border-box;
            box-shadow: 0 2px 7px rgba(36, 59, 90, 0.025);
        }}

        .prof-metric-value {{
            color: {NAVY};
            font-size: 1.72rem;
            line-height: 1;
            font-weight: 830;
            letter-spacing: -0.025em;
        }}

        .prof-metric-label {{
            color: {MUTED};
            font-size: 0.78rem;
            line-height: 1.25;
            font-weight: 740;
            letter-spacing: 0.035em;
            text-transform: uppercase;
            margin-top: 0.52rem;
        }}

        .prof-section-gap {{
            height: 1.7rem;
        }}

        .prof-section-title {{
            color: {TEXT};
            font-size: 1.16rem;
            line-height: 1.25;
            font-weight: 780;
            letter-spacing: -0.012em;
            margin: 0 0 0.68rem 0;
        }}

        .prof-result-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-top: 3px solid {LIGHT_ORANGE};
            border-radius: 12px;
            min-height: 278px;
            padding: 1.18rem 1.12rem;
            box-sizing: border-box;
            box-shadow: 0 2px 7px rgba(36, 59, 90, 0.025);
        }}

        .prof-result-title {{
            color: {NAVY};
            font-size: 1.16rem;
            line-height: 1.2;
            font-weight: 820;
            margin: 0;
        }}

        .prof-result-subtitle {{
            color: {MUTED};
            font-size: 0.87rem;
            line-height: 1.4;
            margin: 0.25rem 0 1rem 0;
        }}

        .prof-result-item {{
            margin-top: 0.82rem;
        }}

        .prof-result-meta {{
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            align-items: center;
            color: {TEXT};
            font-size: 0.98rem;
            line-height: 1.25;
            font-weight: 650;
            margin-bottom: 0.34rem;
        }}

        .prof-result-meta strong {{
            color: {NAVY};
            font-weight: 820;
        }}

        .prof-bar-track {{
            width: 100%;
            height: 12px;
            border-radius: 999px;
            background: #EEF0F3;
            overflow: hidden;
        }}

        .prof-bar-fill {{
            height: 100%;
            border-radius: 999px;
            background: {LIGHT_ORANGE};
        }}

        .decoy-result-card {{
            background: {ORANGE_SOFT};
            border: 1px solid rgba(241, 181, 107, 0.72);
            border-radius: 14px;
            padding: 1.35rem 1.25rem;
            text-align: center;
            box-sizing: border-box;
        }}

        .decoy-result-label {{
            color: {NAVY};
            font-size: 0.94rem;
            line-height: 1.2;
            font-weight: 790;
            letter-spacing: 0.045em;
            text-transform: uppercase;
        }}

        .decoy-rate-row {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            margin-top: 0.72rem;
        }}

        .decoy-rate {{
            color: {TEXT};
            font-size: 1rem;
            line-height: 1.2;
            font-weight: 690;
        }}

        .decoy-rate strong {{
            color: {NAVY};
            font-size: 1.42rem;
            font-weight: 840;
        }}

        .decoy-arrow {{
            color: {LIGHT_ORANGE_HOVER};
            font-size: 1.42rem;
            font-weight: 850;
        }}

        .decoy-difference {{
            color: {NAVY};
            font-size: 1.72rem;
            line-height: 1.1;
            font-weight: 850;
            margin-top: 0.72rem;
        }}

        .decoy-copy {{
            color: {MUTED};
            font-size: 0.92rem;
            line-height: 1.5;
            margin-top: 0.42rem;
        }}

        .prof-controls-copy {{
            color: {MUTED};
            font-size: 0.98rem;
            line-height: 1.45;
            margin: -0.20rem 0 0.70rem 0;
        }}

        .prof-reveal-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-left: 4px solid {LIGHT_ORANGE};
            border-radius: 10px;
            padding: 1.05rem 1.05rem;
            margin-top: 0.85rem;
            box-sizing: border-box;
        }}

        .prof-reveal-title {{
            color: {TEXT};
            font-size: 1rem;
            line-height: 1.25;
            font-weight: 790;
            margin: 0 0 0.48rem 0;
        }}

        .prof-reveal-copy {{
            color: {MUTED};
            font-size: 0.92rem;
            line-height: 1.58;
            margin: 0;
        }}

        .prof-reveal-copy strong {{
            color: {NAVY};
        }}

        .prof-reset-warning {{
            background: {RED_SOFT};
            border: 1px solid rgba(181, 74, 74, 0.25);
            border-radius: 10px;
            color: {TEXT};
            padding: 0.86rem 0.92rem;
            margin-top: 0.85rem;
            font-size: 0.92rem;
            line-height: 1.5;
        }}

        .stDownloadButton > button {{
            width: 100% !important;
            height: 40px !important;
            min-height: 40px !important;
            padding: 0 0.78rem !important;
            border-radius: 999px !important;
            border: 1.5px solid {LIGHT_ORANGE} !important;
            background: {SURFACE} !important;
            color: {NAVY} !important;
            font-size: 0.94rem !important;
            font-weight: 730 !important;
            box-shadow: none !important;
        }}

        .stDownloadButton > button p,
        .stDownloadButton > button span {{
            margin: 0 !important;
            font-family: inherit !important;
            font-size: 0.94rem !important;
            line-height: 1 !important;
            font-weight: 730 !important;
            letter-spacing: 0.01em !important;
            white-space: nowrap !important;
        }}

        .stDownloadButton > button:hover:not(:disabled) {{
            background: {LIGHT_ORANGE_HOVER} !important;
            border-color: {LIGHT_ORANGE_HOVER} !important;
            color: {NAVY} !important;
        }}

        .stDownloadButton > button:hover:not(:disabled) p,
        .stDownloadButton > button:hover:not(:disabled) span {{
            color: {NAVY} !important;
        }}

        /* ==================================================
           VERSION
        ================================================== */

        .version-label {{
            text-align: center;
            color: #A3A7AD;
            font-size: 0.68rem;
            margin-top: 2rem;
        }}

        /* ==================================================
           MOBILE
        ================================================== */

        @media (max-width: 700px) {{
            .block-container {{
                padding-left: 0.9rem;
                padding-right: 0.9rem;
                padding-top: 1.8rem;
            }}

            .main-title {{
                font-size: 1.65rem;
            }}

            div[data-testid="stHorizontalBlock"] .stButton > button {{
                height: 36px !important;
                min-height: 36px !important;
                font-size: 0.74rem !important;
                padding: 0 0.55rem !important;
            }}

            div[data-testid="stHorizontalBlock"] .stButton > button p {{
                font-size: 0.74rem !important;
            }}

            div[role="radiogroup"] {{
                flex-direction: column;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GOOGLE SHEETS STORAGE - NEW ROWS ARE ANONYMOUS
# ============================================================

RESPONSE_FIELDS = [
    "name_key",
    "name",
    "scenario_1_choice",
    "scenario_2_choice",
    "status",
    "created_at",
    "scenario_1_submitted_at",
    "scenario_2_submitted_at",
]

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(show_spinner=False)
def get_google_worksheet():
    """Connect to the response worksheet using Streamlit secrets."""

    service_account_info = dict(
        st.secrets["gcp_service_account"]
    )

    # Accept either real line breaks or escaped \n sequences in TOML.
    private_key = str(
        service_account_info.get(
            "private_key",
            "",
        )
    )
    service_account_info["private_key"] = private_key.replace(
        "\\n",
        "\n",
    )

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=GOOGLE_SCOPES,
    )

    client = gspread.authorize(
        credentials
    )

    spreadsheet_id = str(
        st.secrets["google_sheet"]["spreadsheet_id"]
    ).strip()

    worksheet_name = str(
        st.secrets["google_sheet"]["worksheet_name"]
    ).strip()

    spreadsheet = client.open_by_key(
        spreadsheet_id
    )

    return spreadsheet.worksheet(
        worksheet_name
    )


def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def clean_name(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_name(value: str) -> str:
    return clean_name(value).casefold()


def read_sheet_rows_with_numbers() -> tuple[object, list[tuple[int, dict]]]:
    """Read response rows while preserving their Google Sheet row numbers."""

    worksheet = get_google_worksheet()
    values = worksheet.get_all_values()

    if not values:
        worksheet.append_row(
            RESPONSE_FIELDS,
            value_input_option="RAW",
        )
        return worksheet, []

    header = values[0]

    if header[:len(RESPONSE_FIELDS)] != RESPONSE_FIELDS:
        raise RuntimeError(
            "The Responses worksheet header does not match the expected "
            "8 response columns. Please keep row 1 as: "
            + ", ".join(RESPONSE_FIELDS)
        )

    numbered_rows: list[tuple[int, dict]] = []

    for row_number, raw_values in enumerate(
        values[1:],
        start=2,
    ):
        padded_values = list(raw_values) + [
            ""
        ] * max(
            0,
            len(RESPONSE_FIELDS) - len(raw_values),
        )

        record = {
            field: padded_values[index]
            for index, field in enumerate(RESPONSE_FIELDS)
        }

        if not any(
            str(value).strip()
            for value in record.values()
        ):
            continue

        numbered_rows.append(
            (
                row_number,
                record,
            )
        )

    return worksheet, numbered_rows


def read_rows() -> list[dict]:
    _, numbered_rows = read_sheet_rows_with_numbers()

    return [
        row.copy()
        for _, row in numbered_rows
    ]


def append_response_row(
    row: dict,
) -> int:
    """Append one anonymous response row and return its Sheet row number."""

    worksheet = get_google_worksheet()

    result = worksheet.append_row(
        [
            row.get(field, "")
            for field in RESPONSE_FIELDS
        ],
        value_input_option="RAW",
    )

    updated_range = str(
        result.get("updates", {}).get("updatedRange", "")
    )

    if "!" in updated_range:
        row_reference = updated_range.split("!", 1)[1].split(":", 1)[0]
        row_digits = "".join(
            character
            for character in row_reference
            if character.isdigit()
        )

        if row_digits:
            return int(row_digits)

    # Fallback for older gspread/API responses that do not return updatedRange.
    return len(worksheet.get_all_values())


def update_response_row(
    worksheet,
    row_number: int,
    row: dict,
) -> None:
    """Update one student's complete record without rewriting other rows."""

    worksheet.update(
        range_name=f"A{row_number}:H{row_number}",
        values=[
            [
                row.get(field, "")
                for field in RESPONSE_FIELDS
            ]
        ],
        value_input_option="RAW",
    )


def clear_response_rows() -> None:
    """Clear student data while preserving the row-1 headers."""

    worksheet = get_google_worksheet()
    worksheet.batch_clear(
        ["A2:H"]
    )


def rows_to_csv_bytes(
    rows: list[dict],
) -> bytes:
    """Build the Professor Mode CSV download from Google Sheet data."""

    output = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        output,
        fieldnames=RESPONSE_FIELDS,
    )
    writer.writeheader()

    for row in rows:
        writer.writerow(
            {
                field: row.get(field, "")
                for field in RESPONSE_FIELDS
            }
        )

    return output.getvalue().encode(
        "utf-8-sig"
    )


def find_student_by_row_number(
    numbered_rows: list[tuple[int, dict]],
    row_number: int,
) -> dict | None:
    """Find the anonymous response row used by the current Streamlit session."""

    for current_row_number, row in numbered_rows:
        if current_row_number == row_number:
            return row.copy()

    return None


def student_display_name(student: dict) -> str:
    """Return the name kept only in this Streamlit session."""

    return str(student.get("_display_name", "")).strip()


# ============================================================
# STUDENT RECORDS AND SCENARIO RESPONSES
# ============================================================

def get_or_create_student(
    entered_name: str,
) -> dict:
    """Create a response row without storing the student's name in Google Sheets."""

    display_name = clean_name(
        entered_name
    )

    # Preserve the existing 8-column Sheet structure so historical data is not
    # changed. For every NEW response, name_key and name are blank cells.
    # The display name exists only in this student's current Streamlit session.
    new_student = {
        "name_key": "",
        "name": "",
        "scenario_1_choice": "",
        "scenario_2_choice": "",
        "status": "started",
        "created_at": now_text(),
        "scenario_1_submitted_at": "",
        "scenario_2_submitted_at": "",
    }

    sheet_row_number = append_response_row(
        new_student
    )

    session_student = new_student.copy()
    session_student["_sheet_row_number"] = sheet_row_number
    session_student["_display_name"] = display_name

    return session_student


def save_scenario_response(
    sheet_row_number: int,
    scenario: int,
    selected_choice: str,
) -> dict | None:

    worksheet, numbered_rows = read_sheet_rows_with_numbers()

    for row_number, row in numbered_rows:

        if row_number != sheet_row_number:
            continue

        if scenario == 1:
            if row.get("scenario_1_choice"):
                return row.copy()

            row["scenario_1_choice"] = selected_choice
            row["scenario_1_submitted_at"] = now_text()

            if row.get("scenario_2_choice"):
                row["status"] = "completed"
            else:
                row["status"] = "scenario_1_submitted"

        elif scenario == 2:
            if not row.get("scenario_1_choice"):
                return None

            if row.get("scenario_2_choice"):
                return row.copy()

            row["scenario_2_choice"] = selected_choice
            row["scenario_2_submitted_at"] = now_text()
            row["status"] = "completed"

        else:
            return None

        # Never write the student's name or name-derived key for new responses.
        row["name_key"] = ""
        row["name"] = ""

        update_response_row(
            worksheet,
            row_number,
            row,
        )

        return row.copy()

    return None


# ============================================================
# SESSION STATE
# ============================================================

def initialize_state() -> None:
    defaults = {
        "mode": "student",
        "student": None,
        "student_stage": "name",
        "selected_choice": None,
        "just_submitted": False,
        "name_input": "",
        "professor_authenticated": False,
        "professor_reveal_experiment": False,
        "professor_reset_pending": False,
        "professor_login_error": "",
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


def rerun_app() -> None:

    if hasattr(st, "rerun"):
        st.rerun()

    else:
        st.experimental_rerun()


def lock_professor_access() -> None:
    """Lock Professor Mode whenever the user leaves or re-enters it."""

    st.session_state.professor_authenticated = False
    st.session_state.professor_reveal_experiment = False
    st.session_state.professor_reset_pending = False
    st.session_state.professor_login_error = ""

    if "professor_access_code" in st.session_state:
        st.session_state.professor_access_code = ""


initialize_state()


# ============================================================
# HEADER
# ============================================================

def render_header() -> None:

    render_html(
        """
        <h1 class="main-title">
            Movie Snack Choice
        </h1>

        <div class="title-spacer"></div>
        """
    )

    # v2.5:
    # Student and Professor capsules are left-aligned
    # and brought closer together.
    (
        student_col,
        small_gap,
        professor_col,
        right_space,
    ) = st.columns(
        [1.18, 0.08, 1.18, 5.26],
        gap=None,
    )

    with student_col:

        student_clicked = st.button(
            "STUDENT MODE",
            key="mode_student",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.mode == "student"
                else "secondary"
            ),
        )

    with professor_col:

        professor_clicked = st.button(
            "PROFESSOR MODE",
            key="mode_professor",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.mode == "professor"
                else "secondary"
            ),
        )

    if student_clicked:
        st.session_state.mode = "student"
        lock_professor_access()
        rerun_app()

    if professor_clicked:
        if st.session_state.mode != "professor":
            lock_professor_access()

        st.session_state.mode = "professor"
        rerun_app()


# ============================================================
# STUDENT MODE - NAME ENTRY
# ============================================================

def render_name_screen() -> None:

    render_html(
        """
        <div class="content-area">
            <div class="entry-label">
                Enter your name
            </div>

            <div class="name-input-gap"></div>
        </div>
        """
    )

    entered_name = st.text_input(
        "Full name",
        value=st.session_state.get(
            "name_input",
            "",
        ),
        placeholder="Type your full name",
        label_visibility="collapsed",
        key="student_name_field",
    )

    continue_left, continue_col, continue_right = st.columns(
        [2.35, 1.50, 2.35],
        gap=None,
    )

    with continue_col:

        continue_clicked = st.button(
            "CONTINUE",
            key="continue_student",
            use_container_width=True,
            type="primary",
        )

    if not continue_clicked:
        return

    display_name = clean_name(
        entered_name
    )

    if len(display_name) < 2:

        st.error(
            "Please enter your name before continuing."
        )

        return

    student = get_or_create_student(
        display_name
    )

    st.session_state.name_input = display_name
    st.session_state.student = student
    st.session_state.selected_choice = None
    st.session_state.just_submitted = False

    if student.get("scenario_2_choice"):
        st.session_state.student_stage = "submitted"

    elif student.get("scenario_1_choice"):
        # Scenario 1 is already safely stored. Show the transition
        # before the student enters Scenario 2.
        st.session_state.student_stage = "scenario_1_complete"

    else:
        st.session_state.student_stage = "scenario_1"

    rerun_app()


# ============================================================
# STUDENT MODE - SCENARIO HEADER
# ============================================================

def render_student_scenario_header(
    student: dict,
) -> None:

    safe_name = html.escape(
        student_display_name(student)
    )

    render_html(
        f"""
        <div class="student-scenario-area">

            <div class="student-hello">
                Hello&nbsp;<strong>{safe_name}</strong>
            </div>

            <div class="student-question-gap"></div>

        </div>
        """
    )


# ============================================================
# STUDENT MODE - SCENARIO TRANSITION
# ============================================================

def render_scenario_transition(
    student: dict,
) -> None:

    render_html(
        """
        <div class="content-area">

            <div class="scenario-transition-card">

                <div class="scenario-transition-badge">
                    SCENARIO 1 COMPLETE
                </div>

                <div class="scenario-transition-title">
                    Thank you for your response!
                </div>

                <div class="scenario-transition-copy">
                    Your response for <strong>Scenario 1</strong> has been saved.<br>
                    Let's move to <strong>Scenario 2</strong>.
                </div>

            </div>

            <div class="scenario-transition-button-gap"></div>

        </div>
        """
    )

    continue_left, continue_col, continue_right = st.columns(
        [2.75, 2.70, 2.75],
        gap=None,
    )

    with continue_col:
        continue_clicked = st.button(
            "CONTINUE TO SCENARIO 2",
            key="continue_scenario_2",
            use_container_width=True,
            type="primary",
        )

    if continue_clicked:
        st.session_state.student_stage = "scenario_2"
        st.session_state.selected_choice = None
        st.session_state.just_submitted = False
        rerun_app()


# ============================================================
# STUDENT MODE - SCENARIOS
# ============================================================

def scenario_options(
    scenario: int,
) -> list[tuple[str, int | None]]:

    if scenario == 1:
        return [
            ("Small", 150),
            ("Large", 300),
            ("Don't Know", None),
        ]

    return [
        ("Small", 150),
        ("Medium", 290),
        ("Large", 300),
        ("Don't Know", None),
    ]


def render_question_screen(
    student: dict,
    scenario: int,
) -> None:

    render_html(
        f"""
        <div class="content-area">

            <div class="scenario-capsule">
                Scenario {scenario} of 2
            </div>

            <div class="scenario-to-question-gap"></div>

            <div class="question-card">
                <div class="question">
                   {"If you were buying popcorn at a movie theatre, which option would you choose?"
                    if scenario == 1
                    else "If you are buying popcorn, which option would you choose?"}
                </div>
            </div>

            <div class="question-hint">
                Select one option below.
            </div>

            <div class="question-to-options-gap"></div>

        </div>
        """
    )

    options = scenario_options(
        scenario
    )

    option_names = [
        option_name
        for option_name, _ in options
    ]

    prices = {
        option_name: price
        for option_name, price in options
    }

    size_descriptions = {
        "Small": "Size - 6 to 11 cups of popcorn",
        "Medium": "Size - 12 to 15 cups of popcorn",
        "Large": "Size - 16 to 20+ cups of popcorn",
    }

    current_choice = st.session_state.get(
        "selected_choice"
    )

    selected_choice = (
        current_choice
        if current_choice in option_names
        else None
    )

    # Scenario 1 has Small, Large, and Don't Know.
    # Scenario 2 additionally includes the Medium decoy.
    # Clicking a choice only updates temporary session state.
    # The response is saved only after SUBMIT RESPONSE is pressed.
    # Keep the complete option group horizontally centered.
    # Equal spacer columns are used on the left and right so the capsules
    # sit in the middle of the question area rather than against the left.
    if len(options) == 3:
        option_row = st.columns(
            [0.86, 1.34, 1.34, 1.34, 0.86],
            gap="small",
        )
        option_columns = option_row[1:4]
    else:
        option_row = st.columns(
            [0.34, 1.26, 1.26, 1.26, 1.26, 0.34],
            gap="small",
        )
        option_columns = option_row[1:5]

    for option_col, (option_name, price) in zip(
        option_columns,
        options,
    ):

        with option_col:

            size_description = size_descriptions.get(
                option_name
            )

            if option_name in {"Small", "Medium", "Large"}:
                # Each option uses a genuinely different bucket shape inside the
                # same visual frame: Small is short/narrow, Medium is mid-sized,
                # and Large is tall/wide, matching the supplied reference idea.
                render_html(
                    popcorn_bucket_svg(option_name)
                )
            else:
                # Keep Don't Know aligned with the other option capsules.
                render_html(
                    """
                    <div class="popcorn-visual-wrap">
                        <span class="popcorn-visual-placeholder"></span>
                    </div>
                    """
                )

            if price is None:
                button_label = option_name.upper()
            elif size_description:
                # Keep the size information inside the same clickable capsule.
                # A non-breaking-space middle line creates a clear one-line gap
                # between the option name/price and the size description.
                button_label = (
                    f"{option_name.upper()} · ₹{price}  \n"
                    "\u00A0  \n"
                    f"{size_description}"
                )
            else:
                button_label = f"{option_name.upper()} · ₹{price}"

            option_key = (
                option_name.lower()
                .replace("'", "")
                .replace(" ", "_")
            )

            option_clicked = st.button(
                button_label,
                key=f"popcorn_choice_{option_key}",
                use_container_width=True,
                type=(
                    "primary"
                    if selected_choice == option_name
                    else "secondary"
                ),
            )

        if option_clicked:

            st.session_state.selected_choice = (
                option_name
            )

            rerun_app()

    if selected_choice is not None:

        selected_price = prices[selected_choice]
        selected_price_html = (
            f"&nbsp;·&nbsp; ₹{selected_price}"
            if selected_price is not None
            else ""
        )

        render_html(
            f"""
            <div class="selected-note">

                Selected:
                <strong>{selected_choice}</strong>
                {selected_price_html}

            </div>
            """
        )

    render_html(
        '<div class="options-to-submit-gap"></div>'
    )

    submit_clicked = st.button(
        "SUBMIT RESPONSE",
        use_container_width=True,
        type="primary",
        disabled=selected_choice is None,
        key="submit_response",
    )

    if not submit_clicked:
        return

    saved_student = save_scenario_response(
        int(student["_sheet_row_number"]),
        scenario,
        selected_choice,
    )

    if saved_student is None:

        st.error(
            "Your participant record could not be updated. "
            "Please enter your name again."
        )

        st.session_state.student = None
        st.session_state.student_stage = "name"
        st.session_state.selected_choice = None
        st.session_state.just_submitted = False

        return

    saved_student["_sheet_row_number"] = student["_sheet_row_number"]
    saved_student["_display_name"] = student_display_name(student)

    st.session_state.student = (
        saved_student
    )

    st.session_state.selected_choice = None

    if scenario == 1:
        # Create a deliberate break between the two scenarios.
        # Scenario 1 is already saved before this transition appears.
        st.session_state.student_stage = (
            "scenario_1_complete"
        )
        st.session_state.just_submitted = False

    else:
        st.session_state.student_stage = (
            "submitted"
        )
        st.session_state.just_submitted = True

    rerun_app()


# ============================================================
# STUDENT MODE - SUCCESS
# ============================================================

def render_success_screen(
    student: dict,
) -> None:

    safe_name = html.escape(
        student_display_name(student)
    )

    just_submitted = st.session_state.get(
        "just_submitted",
        False,
    )

    if just_submitted:

        message = (
            "Both of your responses have been saved successfully."
        )

    else:

        message = (
            "You have already completed both scenarios."
        )

    render_html(
        f"""
        <div class="content-area">

            <div class="success-card">

                <div class="success-check">
                    ✓
                </div>

                <div class="success-title">
                    Thank you, {safe_name}!
                </div>

                <div class="success-copy">
                    You completed <strong>Scenario 1</strong> and
                    <strong>Scenario 2</strong>.
                    <br>
                    {message}
                </div>

            </div>

        </div>
        """
    )


# ============================================================
# STUDENT MODE ROUTER
# ============================================================

def render_student_mode() -> None:

    student = st.session_state.get(
        "student"
    )

    if student is None:

        st.session_state.student_stage = "name"

        render_name_screen()

        return

    _, numbered_rows = read_sheet_rows_with_numbers()

    sheet_row_number = student.get(
        "_sheet_row_number"
    )

    if sheet_row_number is None:
        latest_student = None
    else:
        latest_student = find_student_by_row_number(
            numbered_rows,
            int(sheet_row_number),
        )

        if latest_student is not None:
            latest_student["_sheet_row_number"] = int(sheet_row_number)
            latest_student["_display_name"] = student_display_name(student)

    if latest_student is None:

        st.session_state.student = None
        st.session_state.student_stage = "name"
        st.session_state.selected_choice = None
        st.session_state.just_submitted = False

        render_name_screen()

        return

    st.session_state.student = (
        latest_student
    )

    # Stored responses are authoritative. After Scenario 1 is saved,
    # the student first sees a clear transition screen. Once CONTINUE is
    # pressed in the current session, Scenario 2 opens. A fresh session
    # returns to the transition rather than repeating Scenario 1.
    if latest_student.get("scenario_2_choice"):
        stage = "submitted"

    elif latest_student.get("scenario_1_choice"):
        current_stage = st.session_state.get(
            "student_stage",
            "scenario_1_complete",
        )

        stage = (
            "scenario_2"
            if current_stage == "scenario_2"
            else "scenario_1_complete"
        )

    else:
        stage = "scenario_1"

    st.session_state.student_stage = stage

    if stage == "scenario_1":

        render_student_scenario_header(
            latest_student
        )

        render_question_screen(
            latest_student,
            scenario=1,
        )

        return

    if stage == "scenario_1_complete":

        render_student_scenario_header(
            latest_student
        )

        render_scenario_transition(
            latest_student
        )

        return

    if stage == "scenario_2":

        render_student_scenario_header(
            latest_student
        )

        render_question_screen(
            latest_student,
            scenario=2,
        )

        return

    render_success_screen(
        latest_student
    )


# ============================================================
# PROFESSOR MODE
# ============================================================

def get_professor_password() -> str | None:
    """Read the professor password only from .streamlit/secrets.toml."""

    try:
        password = st.secrets["professor"]["password"]
    except Exception:
        return None

    password = str(password)

    if not password:
        return None

    return password


def calculate_professor_stats(rows: list[dict]) -> dict:
    scenario_1_rows = [
        row
        for row in rows
        if row.get("scenario_1_choice")
    ]

    scenario_2_rows = [
        row
        for row in rows
        if row.get("scenario_2_choice")
    ]

    completed_rows = [
        row
        for row in rows
        if (
            row.get("scenario_1_choice")
            and row.get("scenario_2_choice")
        )
    ]

    def choice_counts(
        response_rows: list[dict],
        field_name: str,
    ) -> dict[str, int]:
        return {
            "Small": sum(
                1
                for row in response_rows
                if row.get(field_name) == "Small"
            ),
            "Medium": sum(
                1
                for row in response_rows
                if row.get(field_name) == "Medium"
            ),
            "Large": sum(
                1
                for row in response_rows
                if row.get(field_name) == "Large"
            ),
            "Don't Know": sum(
                1
                for row in response_rows
                if row.get(field_name) == "Don't Know"
            ),
        }

    return {
        "total": len(rows),
        "scenario_1_submitted": len(scenario_1_rows),
        "scenario_2_submitted": len(scenario_2_rows),
        "completed": len(completed_rows),
        "in_progress": len(rows) - len(completed_rows),
        "scenario_1_choices": choice_counts(
            scenario_1_rows,
            "scenario_1_choice",
        ),
        "scenario_2_choices": choice_counts(
            scenario_2_rows,
            "scenario_2_choice",
        ),
        "paired_scenario_1_choices": choice_counts(
            completed_rows,
            "scenario_1_choice",
        ),
        "paired_scenario_2_choices": choice_counts(
            completed_rows,
            "scenario_2_choice",
        ),
    }


def percentage(count: int, total: int) -> float:
    if total <= 0:
        return 0.0

    return (count / total) * 100.0


def format_percent(value: float) -> str:
    if abs(value - round(value)) < 0.05:
        return f"{round(value):.0f}%"

    return f"{value:.1f}%"


def render_professor_metric(
    value: int,
    label: str,
) -> None:
    render_html(
        f"""
        <div class="prof-metric-card">
            <div class="prof-metric-value">{value}</div>
            <div class="prof-metric-label">{label}</div>
        </div>
        """
    )


def render_scenario_result_card(
    scenario: int,
    submitted_count: int,
    choices: dict[str, int],
) -> None:
    if scenario == 1:
        options = ["Small", "Large", "Don't Know"]
    else:
        options = ["Small", "Medium", "Large", "Don't Know"]

    rows_html = ""

    for option in options:
        count = choices.get(option, 0)
        rate = percentage(
            count,
            submitted_count,
        )

        rows_html += (
            '<div class="prof-result-item">'
            '<div class="prof-result-meta">'
            f'<span>{option}</span>'
            f'<strong>{count} &nbsp;·&nbsp; {format_percent(rate)}</strong>'
            '</div>'
            '<div class="prof-bar-track">'
            f'<div class="prof-bar-fill" style="width:{rate:.2f}%;"></div>'
            '</div>'
            '</div>'
        )

    render_html(
        f"""
        <div class="prof-result-card">
            <div class="prof-result-title">
                Scenario {scenario}
            </div>
            <div class="prof-result-subtitle">
                {submitted_count} submitted response(s)
            </div>
            {rows_html}
        </div>
        """
    )


def render_decoy_result(stats: dict) -> None:
    completed_total = stats["completed"]

    scenario_1_large = (
        stats["paired_scenario_1_choices"]["Large"]
    )
    scenario_2_large = (
        stats["paired_scenario_2_choices"]["Large"]
    )

    scenario_1_rate = percentage(
        scenario_1_large,
        completed_total,
    )

    scenario_2_rate = percentage(
        scenario_2_large,
        completed_total,
    )

    if completed_total == 0:
        render_html(
            """
            <div class="decoy-result-card">
                <div class="decoy-result-label">
                    Decoy Effect Result
                </div>
                <div class="decoy-difference">
                    Waiting for completed responses
                </div>
                <div class="decoy-copy">
                    At least one student must complete both scenarios before
                    the Large-choice rates can be compared.
                </div>
            </div>
            """
        )
        return

    difference = scenario_2_rate - scenario_1_rate

    if difference > 0:
        comparison_text = (
            f"The Large-choice rate is {format_percent(abs(difference))} "
            "higher in Scenario 2."
        )
    elif difference < 0:
        comparison_text = (
            f"The Large-choice rate is {format_percent(abs(difference))} "
            "lower in Scenario 2."
        )
    else:
        comparison_text = (
            "The Large-choice rate is currently the same in both scenarios."
        )

    signed_difference = f"{difference:+.1f} percentage points"

    render_html(
        f"""
        <div class="decoy-result-card">
            <div class="decoy-result-label">
                Decoy Effect Result
            </div>

            <div class="decoy-rate-row">
                <div class="decoy-rate">
                    Scenario 1<br>
                    <strong>{format_percent(scenario_1_rate)}</strong>
                </div>

                <div class="decoy-arrow">→</div>

                <div class="decoy-rate">
                    Scenario 2<br>
                    <strong>{format_percent(scenario_2_rate)}</strong>
                </div>
            </div>

            <div class="decoy-difference">
                {signed_difference}
            </div>

            <div class="decoy-copy">
                {comparison_text}<br>
                Comparison uses the {completed_total} student(s) who completed
                both scenarios.
            </div>
        </div>
        """
    )


def reset_experiment() -> None:
    clear_response_rows()

    st.session_state.student = None
    st.session_state.student_stage = "name"
    st.session_state.selected_choice = None
    st.session_state.just_submitted = False
    st.session_state.name_input = ""
    st.session_state.professor_reset_pending = False
    st.session_state.professor_reveal_experiment = False


def authenticate_professor() -> None:
    """Validate the professor password from Streamlit secrets."""

    access_code = str(
        st.session_state.get(
            "professor_access_code",
            "",
        )
    )

    configured_password = get_professor_password()

    if configured_password is None:
        st.session_state.professor_authenticated = False
        st.session_state.professor_login_error = (
            "Professor password is not configured. Add "
            "[professor] password = \"...\" to .streamlit/secrets.toml."
        )
        return

    if not hmac.compare_digest(
        access_code,
        configured_password,
    ):
        st.session_state.professor_authenticated = False
        st.session_state.professor_login_error = (
            "Incorrect professor password."
        )
        return

    st.session_state.professor_authenticated = True
    st.session_state.professor_login_error = ""


def render_professor_login() -> None:
    render_html(
        """
        <div class="professor-login-wrap">
            <div class="professor-login-title">
                Professor access
            </div>
            <div class="professor-login-copy">
                Enter the professor password to open the live experiment dashboard.
            </div>
        </div>
        """
    )

    login_left, login_col, login_right = st.columns(
        [1.0, 2.25, 2.0],
        gap="small",
    )

    with login_col:
        st.text_input(
            "Professor password",
            type="password",
            placeholder="Enter professor password",
            label_visibility="collapsed",
            key="professor_access_code",
            on_change=authenticate_professor,
        )

        login_clicked = st.button(
            "ENTER DASHBOARD",
            key="professor_continue",
            use_container_width=True,
            type="primary",
        )

    if login_clicked:
        authenticate_professor()

        if st.session_state.professor_authenticated:
            rerun_app()

    login_error = st.session_state.get(
        "professor_login_error",
        "",
    )

    if login_error:
        st.error(
            login_error
        )


def render_professor_dashboard() -> None:
    rows = read_rows()
    stats = calculate_professor_stats(
        rows
    )

    render_html(
        """
        <div class="professor-dashboard-head">
            <div class="professor-dashboard-title">
                Professor Dashboard
            </div>
            <div class="professor-dashboard-copy">
                Live classroom summary and Scenario 1 / Scenario 2 results.
            </div>
            <div class="prof-auto-refresh-capsule">
                <span class="prof-auto-refresh-dot"></span>
                AUTO-REFRESH EVERY 3 SEC
            </div>
        </div>
        """
    )

    metric_columns = st.columns(
        4,
        gap="small",
    )

    metric_values = [
        (stats["total"], "Total Students"),
        (stats["scenario_1_submitted"], "Scenario 1 Submitted"),
        (stats["scenario_2_submitted"], "Scenario 2 Submitted"),
        (stats["in_progress"], "In Progress"),
    ]

    for column, (value, label) in zip(
        metric_columns,
        metric_values,
    ):
        with column:
            render_professor_metric(
                value,
                label,
            )

    render_html(
        """
        <div class="prof-section-gap"></div>
        <div class="prof-section-title">
            Scenario comparison
        </div>
        """
    )

    scenario_1_col, scenario_2_col = st.columns(
        2,
        gap="medium",
    )

    with scenario_1_col:
        render_scenario_result_card(
            1,
            stats["scenario_1_submitted"],
            stats["scenario_1_choices"],
        )

    with scenario_2_col:
        render_scenario_result_card(
            2,
            stats["scenario_2_submitted"],
            stats["scenario_2_choices"],
        )

    render_html(
        """
        <div class="prof-section-gap"></div>
        <div class="prof-section-title">
            Decoy effect comparison
        </div>
        """
    )

    render_decoy_result(
        stats
    )

    render_html(
        """
        <div class="prof-section-gap"></div>
        <div class="prof-section-title">
            Experiment controls
        </div>
        <div class="prof-controls-copy">
            Refresh the live totals, download the response file, reveal the
            experiment design, or reset the class experiment.
        </div>
        """
    )

    csv_bytes = rows_to_csv_bytes(
        rows
    )

    control_columns = st.columns(
        4,
        gap="small",
    )

    with control_columns[0]:
        refresh_clicked = st.button(
            "REFRESH RESULTS",
            key="professor_refresh",
            use_container_width=True,
            type="primary",
        )

    with control_columns[1]:
        st.download_button(
            "DOWNLOAD CSV",
            data=csv_bytes,
            file_name="popcorn_decoy_responses.csv",
            mime="text/csv",
            key="professor_download_csv",
            use_container_width=True,
        )

    reveal_label = (
        "HIDE EXPERIMENT"
        if st.session_state.professor_reveal_experiment
        else "REVEAL EXPERIMENT"
    )

    with control_columns[2]:
        reveal_clicked = st.button(
            reveal_label,
            key="professor_reveal_button",
            use_container_width=True,
            type="secondary",
        )

    with control_columns[3]:
        reset_clicked = st.button(
            "RESET EXPERIMENT",
            key="professor_reset_button",
            use_container_width=True,
            type="secondary",
        )

    if refresh_clicked:
        rerun_app()

    if reveal_clicked:
        st.session_state.professor_reveal_experiment = (
            not st.session_state.professor_reveal_experiment
        )
        rerun_app()

    if reset_clicked:
        st.session_state.professor_reset_pending = True
        rerun_app()

    if st.session_state.professor_reveal_experiment:
        render_html(
            """
            <div class="prof-reveal-card">
                <div class="prof-reveal-title">
                    Experiment design
                </div>
                <div class="prof-reveal-copy">
                    Every student answers both scenarios in sequence.<br><br>
                    <strong>Scenario 1</strong> has three choices:
                    Small ₹150, Large ₹300, and Don't Know.<br>
                    <strong>Scenario 2</strong> has four choices:
                    Small ₹150, Medium ₹290, Large ₹300, and Don't Know.<br><br>
                    The Medium ₹290 option is the intended decoy. Its price is
                    very close to the Large ₹300 option, which can make the
                    Large option appear more attractive by comparison. The
                    dashboard compares the percentage choosing Large in
                    Scenario 1 and Scenario 2 for students who completed both.
                </div>
            </div>
            """
        )

    if st.session_state.professor_reset_pending:
        render_html(
            """
            <div class="prof-reset-warning">
                <strong>Reset experiment?</strong><br>
                This will permanently remove all current student responses
                from the Google Sheet.
            </div>
            """
        )

        reset_confirm_left, reset_confirm_col, cancel_col, reset_confirm_right = st.columns(
            [2.1, 1.35, 1.05, 2.1],
            gap="small",
        )

        with reset_confirm_col:
            confirm_reset = st.button(
                "CONFIRM RESET",
                key="professor_confirm_reset",
                use_container_width=True,
                type="primary",
            )

        with cancel_col:
            cancel_reset = st.button(
                "CANCEL",
                key="professor_cancel_reset",
                use_container_width=True,
                type="secondary",
            )

        if confirm_reset:
            reset_experiment()
            st.success(
                "Experiment reset successfully."
            )
            rerun_app()

        if cancel_reset:
            st.session_state.professor_reset_pending = False
            rerun_app()


if hasattr(st, "fragment"):
    render_professor_dashboard = st.fragment(
        run_every="3s"
    )(render_professor_dashboard)
elif hasattr(st, "experimental_fragment"):
    render_professor_dashboard = st.experimental_fragment(
        run_every="3s"
    )(render_professor_dashboard)


def render_professor_mode() -> None:
    if not st.session_state.professor_authenticated:
        render_professor_login()
        return

    render_professor_dashboard()


# ============================================================
# VERSION
# ============================================================

#def render_version() -> None:

 #   render_html(
  #      f"""
   #     <div class="version-label">
    #        Version {APP_VERSION}
     #   </div>
      #  """
  #  )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    render_header()

    if st.session_state.mode == "student":

        render_student_mode()

    else:

        render_professor_mode()

    #render_version()


if __name__ == "__main__":
    main()
