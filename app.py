#!/usr/bin/env python3

# SMOLAGENTS 1.19 FIX - Must be imported before anything else
from final_fix import apply_final_fix
from browser_agent_fix import validate_listing_url_for_nyc

# NEW: Import fixed address extraction (prioritizes mapaddress and structured data)
from fixed_address_extraction import apply_fixed_extraction

# Apply all fixes at startup
apply_final_fix()
apply_fixed_extraction()

import gradio as gr
import json
import pandas as pd
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from agent_setup import initialize_caseworker_agent
from tools import final_answer
import ast

# Import our new utilities and constants
from utils import log_tool_action, current_timestamp, parse_observation_data
from constants import StageEvent, RiskLevel, Borough, VoucherType
from browser_agent import BrowserAgent
from violation_checker_agent import ViolationCheckerAgent

# Import V0's enhanced email handling
from email_handler import EmailTemplateHandler, enhanced_classify_message, enhanced_handle_email_request

# Import shortlist utilities
from shortlist_utils import (
    add_to_shortlist, remove_from_shortlist, get_shortlist, 
    is_shortlisted, get_shortlist_summary, get_shortlisted_ids
)

# --- Internationalization Setup ---
i18n_dict = {
    "en": {
        "app_title": "🏠 NYC Voucher Housing Navigator",
        "app_subtitle": "Your personal AI Caseworker for finding voucher-friendly housing with building safety insights.",
        "language_selector": "Language / Idioma / 语言 / ভাষা",
        "conversation_label": "Conversation with VoucherBot",
        "message_label": "Your Message",
        "message_placeholder": "Start by telling me your voucher type, required bedrooms, and max rent...",
        "preferences_title": "🎛️ Search Preferences",
        "strict_mode_label": "Strict Mode (Only show buildings with 0 violations)",
        "borough_label": "Preferred Borough",
        "max_rent_label": "Maximum Rent",
        "listings_label": "Matching Listings",
        "status_label": "Status",
        "status_ready": "Ready to search...",
        "no_listings": "I don't have any listings to show you right now. Please search for apartments first!",
        "no_listings_title": "📋 No Current Listings",
        "invalid_listing": "I only have {count} listings available. Please ask for a listing between 1 and {count}.",
        "invalid_listing_title": "❌ Invalid Listing Number",
        "showing_listings": "Showing {count} listings",
        "strict_applied": "🔒 Strict mode applied: {count} listings with 0 violations",
        "strict_applied_title": "🔒 Filtering Applied",
        "results_found": "✅ Found {count} voucher-friendly listings with safety information!",
        "results_title": "✅ Results Ready",
        "no_safe_listings": "No listings meet your safety criteria. Try disabling strict mode to see all available options.",
        "no_safe_title": "⚠️ No Safe Listings",
        "search_error": "❌ Search error: {error}",
        "search_error_title": "❌ Search Error",
        "error_occurred": "I apologize, but I encountered an error: {error}",
        "error_title": "❌ Error",
        "general_response_title": "💬 General Response",
        "conversation_mode": "Conversation mode",
        "no_criteria": "No listings meet criteria",
        "what_if_analysis": "What-if analysis",
        "what_if_error_title": "❌ What-If Error",
        "error_what_if": "I encountered an error processing your what-if scenario: {error}",
        "error_listings_available": "Error - {count} listings available",
        "error_what_if_processing": "Error in what-if processing",
        "error_conversation": "Error in conversation",
        "col_address": "Address",
        "col_price": "Price",
        "col_risk_level": "Risk Level", 
        "col_violations": "Violations",
        "col_last_inspection": "Last Inspection",
        "col_link": "Link",
        "col_summary": "Summary",
        "col_shortlist": "Shortlist",
        "link_not_available": "No link available",
        "shortlist_save": "➕",
        "shortlist_saved": "✅",
        "shortlist_empty": "Your shortlist is empty. Save some listings to get started!",
        "shortlist_title": "Your Shortlist",
        "shortlist_added": "Added to shortlist",
        "shortlist_removed": "Removed from shortlist",
        "shortlist_cleared": "Shortlist cleared",
        "intro_greeting": """👋 **Hi there! I'm Navi, your personal NYC Housing Navigator!**

I'm here to help you find safe, affordable, and voucher-friendly housing in New York City. I understand that finding the right home can feel overwhelming, but you don't have to do this alone—I'm here to guide you every step of the way, and answer any questions you have about housing vouchers or the process! 😊

**To get started, just tell me:**
• What type of voucher do you have? (Section 8, CityFHEPS, HASA, etc.)
• How many bedrooms do you need? 🛏️
• What's your maximum rent budget? 💰
• Do you have a preferred borough? 🗽"""
    },
    "es": {
        "app_title": "🏠 Navegador de Vivienda con Voucher de NYC",
        "app_subtitle": "Tu trabajador social personal de IA para encontrar vivienda que acepta vouchers con información de seguridad del edificio.",
        "language_selector": "Idioma / Language / 语言 / ভাষা",
        "conversation_label": "Conversación con VoucherBot",
        "message_label": "Tu Mensaje",
        "message_placeholder": "Comienza diciéndome tu tipo de voucher, habitaciones requeridas y renta máxima...",
        "preferences_title": "🎛️ Preferencias de Búsqueda",
        "strict_mode_label": "Modo Estricto (Solo mostrar edificios con 0 violaciones)",
        "borough_label": "Distrito Preferido",
        "max_rent_label": "Renta Máxima",
        "listings_label": "Listados Coincidentes",
        "status_label": "Estado",
        "status_ready": "Listo para buscar...",
        "no_listings": "No tengo listados para mostrarte ahora. ¡Por favor busca apartamentos primero!",
        "no_listings_title": "📋 Sin Listados Actuales",
        "invalid_listing": "Solo tengo {count} listados disponibles. Por favor pide un listado entre 1 y {count}.",
        "invalid_listing_title": "❌ Número de Listado Inválido",
        "showing_listings": "Mostrando {count} listados",
        "strict_applied": "🔒 Modo estricto aplicado: {count} listados con 0 violaciones",
        "strict_applied_title": "🔒 Filtro Aplicado",
        "results_found": "✅ ¡Encontrado {count} listados que aceptan vouchers con información de seguridad!",
        "results_title": "✅ Resultados Listos",
        "no_safe_listings": "Ningún listado cumple tus criterios de seguridad. Intenta desactivar el modo estricto para ver todas las opciones disponibles.",
        "no_safe_title": "⚠️ Sin Listados Seguros",
        "search_error": "❌ Error de búsqueda: {error}",
        "search_error_title": "❌ Error de Búsqueda",
        "error_occurred": "Me disculpo, pero encontré un error: {error}",
        "error_title": "❌ Error",
        "general_response_title": "💬 Respuesta General",
        "conversation_mode": "Modo conversación",
        "no_criteria": "Ningún listado cumple criterios",
        "what_if_analysis": "Análisis de qué pasaría si",
        "what_if_error_title": "❌ Error de Qué Pasaría Si",
        "error_what_if": "Encontré un error procesando tu escenario de qué pasaría si: {error}",
        "error_listings_available": "Error - {count} listados disponibles",
        "error_what_if_processing": "Error en procesamiento de qué pasaría si",
        "error_conversation": "Error en conversación",
        "col_address": "Dirección",
        "col_price": "Precio",
        "col_risk_level": "Nivel de Riesgo",
        "col_violations": "Violaciones",
        "col_last_inspection": "Última Inspección",
        "col_link": "Enlace",
        "col_summary": "Resumen",
        "col_shortlist": "Lista Favorita",
        "link_not_available": "Sin enlace disponible",
        "shortlist_save": "➕",
        "shortlist_saved": "✅",
        "shortlist_empty": "Tu lista favorita está vacía. ¡Guarda algunos listados para comenzar!",
        "shortlist_title": "Tu Lista Favorita",
        "shortlist_added": "Agregado a lista favorita",
        "shortlist_removed": "Removido de lista favorita",
        "shortlist_cleared": "Lista favorita limpiada",
        "intro_greeting": """👋 **¡Hola! Soy Navi, tu Navegadora Personal de Vivienda de NYC!**

Estoy aquí para ayudarte a encontrar vivienda segura, asequible y que acepta vouchers en la Ciudad de Nueva York. Entiendo que encontrar el hogar perfecto puede sentirse abrumador, pero no tienes que hacerlo solo—¡estoy aquí para guiarte en cada paso del camino y responder cualquier pregunta que tengas sobre vouchers de vivienda o el proceso! 😊

**Para comenzar, solo dime:**
• ¿Qué tipo de voucher tienes? (Section 8, CityFHEPS, HASA, etc.)
• ¿Cuántas habitaciones necesitas? 🛏️
• ¿Cuál es tu presupuesto máximo de renta? 💰
• ¿Tienes un distrito preferido? 🗽"""
    },
    "zh": {
        "app_title": "🏠 纽约市住房券导航器",
        "app_subtitle": "您的个人AI社工，帮助您找到接受住房券的房屋，并提供建筑安全信息。",
        "language_selector": "语言 / Language / Idioma / ভাষা",
        "conversation_label": "与VoucherBot对话",
        "message_label": "您的消息",
        "message_placeholder": "请先告诉我您的住房券类型、所需卧室数量和最高租金...",
        "preferences_title": "🎛️ 搜索偏好",
        "strict_mode_label": "严格模式（仅显示0违规的建筑）",
        "borough_label": "首选区域",
        "max_rent_label": "最高租金",
        "listings_label": "匹配房源",
        "status_label": "状态",
        "status_ready": "准备搜索...",
        "no_listings": "我现在没有房源可以显示给您。请先搜索公寓！",
        "no_listings_title": "📋 当前无房源",
        "invalid_listing": "我只有{count}个可用房源。请询问1到{count}之间的房源。",
        "invalid_listing_title": "❌ 无效房源号码",
        "showing_listings": "显示{count}个房源",
        "strict_applied": "🔒 严格模式已应用：{count}个0违规房源",
        "strict_applied_title": "🔒 已应用过滤",
        "results_found": "✅ 找到{count}个接受住房券的房源，包含安全信息！",
        "results_title": "✅ 结果准备就绪",
        "no_safe_listings": "没有房源符合您的安全标准。尝试禁用严格模式以查看所有可用选项。",
        "no_safe_title": "⚠️ 无安全房源",
        "search_error": "❌ 搜索错误：{error}",
        "search_error_title": "❌ 搜索错误",
        "error_occurred": "抱歉，我遇到了一个错误：{error}",
        "error_title": "❌ 错误",
        "general_response_title": "💬 一般回复",
        "conversation_mode": "对话模式",
        "no_criteria": "没有房源符合条件",
        "what_if_analysis": "假设分析",
        "what_if_error_title": "❌ 假设错误",
        "error_what_if": "处理您的假设场景时遇到错误：{error}",
        "error_listings_available": "错误 - {count}个房源可用",
        "error_what_if_processing": "假设处理错误",
        "error_conversation": "对话错误",
        "col_address": "地址",
        "col_price": "价格",
        "col_risk_level": "风险级别",
        "col_violations": "违规",
        "col_last_inspection": "最后检查",
        "col_link": "链接",
        "col_summary": "摘要",
        "col_shortlist": "收藏清单",
        "link_not_available": "无可用链接",
        "shortlist_save": "➕",
        "shortlist_saved": "✅",
        "shortlist_empty": "您的收藏清单为空。保存一些房源开始吧！",
        "shortlist_title": "您的收藏清单",
        "shortlist_added": "已添加到收藏清单",
        "shortlist_removed": "已从收藏清单移除",
        "shortlist_cleared": "收藏清单已清空",
        "intro_greeting": """👋 **您好！我是Navi，您的个人纽约市住房导航员！**

我在这里帮助您在纽约市找到安全、经济实惠且接受住房券的住房。我理解找到合适的家可能让人感到不知所措，但您不必独自面对这一切—我会在每一步中指导您，并回答您关于住房券或申请流程的任何问题！😊

**开始使用时，请告诉我：**
• 您有什么类型的住房券？(Section 8、CityFHEPS、HASA等)
• 您需要多少间卧室？🛏️
• 您的最高租金预算是多少？💰
• 您有首选的行政区吗？🗽"""
    },
    "bn": {
        "app_title": "🏠 NYC ভাউচার হাউজিং নেভিগেটর",
        "app_subtitle": "ভাউচার-বান্ধব আবাসন খোঁজার জন্য আপনার ব্যক্তিগত AI কেসওয়ার্কার, বিল্ডিং নিরাপত্তা তথ্যসহ।",
        "language_selector": "ভাষা / Language / Idioma / 语言",
        "conversation_label": "VoucherBot এর সাথে কথোপকথন",
        "message_label": "আপনার বার্তা",
        "message_placeholder": "আপনার ভাউচারের ধরন, প্রয়োজনীয় বেডরুম এবং সর্বোচ্চ ভাড়া বলে শুরু করুন...",
        "preferences_title": "🎛️ অনুসন্ধান পছন্দ",
        "strict_mode_label": "কঠোর মোড (শুধুমাত্র ০ লঙ্ঘনের বিল্ডিং দেখান)",
        "borough_label": "পছন্দের বরো",
        "max_rent_label": "সর্বোচ্চ ভাড়া",
        "listings_label": "মিলে যাওয়া তালিকা",
        "status_label": "অবস্থা",
        "status_ready": "অনুসন্ধানের জন্য প্রস্তুত...",
        "no_listings": "এই মুহূর্তে আপনাকে দেখানোর মতো কোন তালিকা নেই। প্রথমে অ্যাপার্টমেন্ট অনুসন্ধান করুন!",
        "no_listings_title": "📋 বর্তমান তালিকা নেই",
        "invalid_listing": "আমার কাছে শুধুমাত্র {count}টি তালিকা উপলব্ধ। অনুগ্রহ করে ১ থেকে {count} এর মধ্যে একটি তালিকা চান।",
        "invalid_listing_title": "❌ অবৈধ তালিকা নম্বর",
        "showing_listings": "{count}টি তালিকা দেখাচ্ছে",
        "strict_applied": "🔒 কঠোর মোড প্রয়োগ করা হয়েছে: ০ লঙ্ঘনের {count}টি তালিকা",
        "strict_applied_title": "🔒 ফিল্টার প্রয়োগ করা হয়েছে",
        "results_found": "✅ নিরাপত্তা তথ্যসহ {count}টি ভাউচার-বান্ধব তালিকা পাওয়া গেছে!",
        "results_title": "✅ ফলাফল প্রস্তুত",
        "no_safe_listings": "কোন তালিকা আপনার নিরাপত্তা মানদণ্ড পূরণ করে না। সমস্ত উপলব্ধ বিকল্প দেখতে কঠোর মোড নিষ্ক্রিয় করার চেষ্টা করুন।",
        "no_safe_title": "⚠️ কোন নিরাপদ তালিকা নেই",
        "search_error": "❌ অনুসন্ধান ত্রুটি: {error}",
        "search_error_title": "❌ অনুসন্ধান ত্রুটি",
        "error_occurred": "আমি দুঃখিত, কিন্তু আমি একটি ত্রুটির সম্মুখীন হয়েছি: {error}",
        "error_title": "❌ ত্রুটি",
        "general_response_title": "💬 সাধারণ উত্তর",
        "conversation_mode": "কথোপকথন মোড",
        "no_criteria": "কোন তালিকা মানদণ্ড পূরণ করে না",
        "what_if_analysis": "যদি-তাহলে বিশ্লেষণ",
        "what_if_error_title": "❌ যদি-তাহলে ত্রুটি",
        "error_what_if": "আপনার যদি-তাহলে পরিস্থিতি প্রক্রিয়া করতে আমি ত্রুটির সম্মুখীন হয়েছি: {error}",
        "error_listings_available": "ত্রুটি - {count}টি তালিকা উপলব্ধ",
        "error_what_if_processing": "যদি-তাহলে প্রক্রিয়াকরণে ত্রুটি",
        "error_conversation": "কথোপকথনে ত্রুটি",
        "col_address": "ঠিকানা",
        "col_price": "দাম",
        "col_risk_level": "ঝুঁকির স্তর",
        "col_violations": "লঙ্ঘন",
        "col_last_inspection": "শেষ পরিদর্শন",
        "col_link": "লিংক",
        "col_summary": "সারাংশ",
        "col_shortlist": "পছন্দের তালিকা",
        "link_not_available": "কোন লিংক উপলব্ধ নেই",
        "shortlist_save": "➕",
        "shortlist_saved": "✅",
        "shortlist_empty": "আপনার পছন্দের তালিকা খালি। শুরু করতে কিছু তালিকা সংরক্ষণ করুন!",
        "shortlist_title": "আপনার পছন্দের তালিকা",
        "shortlist_added": "পছন্দের তালিকায় যোগ করা হয়েছে",
        "shortlist_removed": "পছন্দের তালিকা থেকে সরানো হয়েছে",
        "shortlist_cleared": "পছন্দের তালিকা পরিষ্কার করা হয়েছে",
        "intro_greeting": """👋 **নমস্কার! আমি নবি, আপনার ব্যক্তিগত NYC হাউজিং নেভিগেটর!**

আমি এখানে আছি নিউইয়র্ক সিটিতে আপনাকে নিরাপদ, সাশ্রয়ী এবং ভাউচার-বান্ধব আবাসন খুঁজে পেতে সাহায্য করার জন্য। আমি বুঝি যে সঠিক বাড়ি খোঁজা অভিভূতকর মনে হতে পারে, কিন্তু আপনাকে একা এটি করতে হবে না—আমি প্রতিটি পদক্ষেপে আপনাকে গাইড করার জন্য এখানে আছি, এবং হাউজিং ভাউচার বা প্রক্রিয়া সম্পর্কে আপনার যেকোনো প্রশ্নের উত্তর দিতে পারি! 😊

**শুরু করতে, শুধু আমাকে বলুন:**
• আপনার কি ধরনের ভাউচার আছে? (Section 8, CityFHEPS, HASA, ইত্যাদি)
• আপনার কতটি বেডরুম প্রয়োজন? 🛏️
• আপনার সর্বোচ্চ ভাড়ার বাজেট কত? 💰
• আপনার কি কোন পছন্দের বরো আছে? 🗽"""
    }
}

# Create the I18n instance with keyword arguments for each language
i18n = gr.I18n(
    en=i18n_dict["en"],
    es=i18n_dict["es"],
    zh=i18n_dict["zh"],
    bn=i18n_dict["bn"]
)

# --- Initialize Agents and State Management ---
print("Initializing VoucherBot Agents...")
caseworker_agent = initialize_caseworker_agent()
browser_agent = BrowserAgent()
violation_agent = ViolationCheckerAgent()
print("Agents Initialized. Ready for requests.")

# --- State Management Functions ---
def create_initial_state() -> Dict:
    """Create initial app state."""
    return {
        "listings": [],
        "current_listing": None,  # Track the currently discussed listing
        "current_listing_index": None,  # Track the index of the current listing
        "preferences": {
            "borough": "",
            "max_rent": 4000,
            "min_bedrooms": 1,
            "voucher_type": "",
            "strict_mode": False,
            "language": "en"  # Add language to preferences
        },
        "shortlist": []  # Changed from favorites to shortlist
    }

def update_app_state(current_state: Dict, updates: Dict) -> Dict:
    """Update app state with new data."""
    new_state = current_state.copy()
    for key, value in updates.items():
        if key == "preferences" and isinstance(value, dict):
            new_state["preferences"].update(value)
        else:
            new_state[key] = value
    return new_state

def filter_listings_strict_mode(listings: List[Dict], strict: bool = False) -> List[Dict]:
    """Filter listings based on strict mode (no violations)."""
    if not strict:
        return listings
    
    return [
        listing for listing in listings 
        if listing.get("building_violations", 0) == 0
    ]

def create_chat_message_with_metadata(content: str, title: str, 
                                    duration: Optional[float] = None,
                                    parent_id: Optional[str] = None) -> Dict:
    """Create a ChatMessage with metadata for better UX."""
    metadata = {
        "title": title,
        "timestamp": current_timestamp()
    }
    
    if duration is not None:
        metadata["duration"] = duration
    
    if parent_id is not None:
        metadata["parent_id"] = parent_id
    
    return {
        "role": "assistant",
        "content": content,
        "metadata": metadata
    }

def detect_context_dependent_question(message: str) -> bool:
    """Detect if the message is asking about something in the current context (like 'which lines?')"""
    message_lower = message.lower().strip()
    
    # Short questions that likely refer to current context
    context_patterns = [
        r'^which\s+(lines?|train|subway)',  # "which lines", "which line", "which train"
        r'^what\s+(lines?|train|subway)',   # "what lines", "what line", "what train"
        r'^how\s+(far|close|near)',         # "how far", "how close", "how near"
        r'^(lines?|train|subway)$',         # just "lines", "line", "train", "subway"
        r'^what\s+about',                   # "what about..."
        r'^tell\s+me\s+about',             # "tell me about..."
        r'^more\s+(info|details)',         # "more info", "more details"
        r'^(distance|walk|walking)',       # "distance", "walk", "walking"
        r'^any\s+other',                   # "any other..."
        r'^is\s+it\s+(near|close|far)',    # "is it near", "is it close", "is it far"
        # Add patterns for subway and school proximity questions
        r'nearest\s+(subway|train|school|transit)', # "nearest subway", "nearest school", "nearest train", "nearest transit"
        r'closest\s+(subway|train|school|transit)', # "closest subway", "closest school", "closest train", "closest transit"
        r'what\'?s\s+the\s+(nearest|closest)\s+(subway|train|school|transit)', # "what's the nearest/closest subway"
        r'where\s+is\s+the\s+(nearest|closest)\s+(subway|train|school|transit)', # "where is the nearest/closest subway"
        r'how\s+far\s+is\s+the\s+(subway|train|school|transit)', # "how far is the subway"
        r'(subway|train|school|transit)\s+(distance|proximity)', # "subway distance", "school proximity"
        r'^(subway|train|school|transit)\?$',      # just "subway?", "school?", "transit?"
        r'^closest\s+(subway|train|school|transit)\?$', # "closest subway?", "closest school?", "closest transit?"
        # Add broader patterns for context questions with "can i see", "show me" etc.
        r'can\s+i\s+see\s+.*?(nearest|closest|subway|train|school)', # "can i see the nearest subway"
        r'show\s+me\s+.*?(nearest|closest|subway|train|school)', # "show me the nearest subway"
        r'tell\s+me\s+.*?(nearest|closest|subway|train|school)', # "tell me the nearest subway"
        r'what.*?(nearest|closest)\s+(subway|train|school)', # "what's the nearest subway"
        r'where.*?(nearest|closest)\s+(subway|train|school)', # "where is the nearest subway"
    ]
    
    # Check if message matches context-dependent patterns using search instead of match
    import re
    for pattern in context_patterns:
        if re.search(pattern, message_lower):
            return True
    
    # Also check for very short questions (likely context-dependent)
    words = message_lower.split()
    if len(words) <= 3 and any(word in ['which', 'what', 'how', 'where', 'lines', 'train', 'subway'] for word in words):
        return True
    
    return False

def detect_language_from_message(message: str) -> str:
    """Detect language from user message using simple keyword matching."""
    message_lower = message.lower()
    
    # Spanish keywords - removed English terms and borough names
    spanish_keywords = [
        'hola', 'apartamento', 'vivienda', 'casa', 'alquiler', 'renta', 'busco', 
        'necesito', 'ayuda', 'donde', 'como', 'que', 'soy', 'tengo', 'quiero',
        'habitacion', 'habitaciones', 'dormitorio', 'precio', 'costo', 'dinero',
        'gracias', 'por favor', 'dime', 'dame', 'encuentro', 'cuanto',
        'cuantas', 'puedo', 'puedes', 'buscar', 'encontrar'
    ]
    
    # Chinese keywords (simplified)
    chinese_keywords = [
        '你好', '公寓', '住房', '房屋', '租金', '寻找', '需要', '帮助', '在哪里',
        '怎么', '什么', '我', '有', '要', '房间', '卧室', '价格', '钱',
        '住房券', '布朗克斯', '布鲁克林', '曼哈顿', '皇后区', '谢谢', '请',
        '告诉', '给我', '找到'
    ]
    
    # Bengali keywords
    bengali_keywords = [
        'নমস্কার', 'অ্যাপার্টমেন্ট', 'বাড়ি', 'ভাড়া', 'খুঁজছি', 'প্রয়োজন',
        'সাহায্য', 'কোথায়', 'কিভাবে', 'কি', 'আমি', 'আছে', 'চাই',
        'রুম', 'বেডরুম', 'দাম', 'টাকা', 'ভাউচার', 'ব্রঙ্কস', 'ব্রুকলিন',
        'ম্যানহাটান', 'কুইন্স', 'ধন্যবাদ', 'দয়া করে', 'বলুন', 'দিন', 'খুঁজে'
    ]
    
    # Count matches for each language
    spanish_count = sum(1 for keyword in spanish_keywords if keyword in message_lower)
    chinese_count = sum(1 for keyword in chinese_keywords if keyword in message)
    bengali_count = sum(1 for keyword in bengali_keywords if keyword in message)
    
    # Return language with highest count (minimum 2 matches required)
    if spanish_count >= 3:  # Increased threshold for Spanish
        return "es"
    elif chinese_count >= 2:
        return "zh"
    elif bengali_count >= 2:
        return "bn"
    else:
        return "en"  # Default to English

# Define the theme using Origin
theme = gr.themes.Origin(
    primary_hue="indigo",
    secondary_hue="indigo",
    neutral_hue="teal",
)

# --- Gradio UI Definition ---
# Original CSS (for easy revert):
# .app-header { text-align: center; margin-bottom: 2rem; }
# .app-title { font-size: 2.2rem; margin-bottom: 0.5rem; }
# .app-subtitle { font-size: 1.1rem; color: #666; margin-bottom: 1rem; }
# .dark .app-title { color: #f9fafb !important; }
# .dark .app-subtitle { color: #d1d5db !important; }
# .dark .gradio-container { background-color: #1f2937 !important; }
# .dark { background-color: #111827 !important; }

with gr.Blocks(theme=theme, css="""
    /* Material Design-inspired styles - Two-Column Layout */
    body, .gr-root {
        font-family: 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        color: #222;
        background: #f5f5f7;
    }
    
    /* Style the expand/collapse arrow */
    button.svelte-vzs2gq.padded {
        background: transparent !important;
        border: none !important;
        padding: 4px !important;
        cursor: pointer !important;
        width: 24px !important;
        height: 24px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .dropdown-arrow {
        width: 18px !important;
        height: 18px !important;
        display: block !important;
    }
    
    /* Hide only the circle background */
    .dropdown-arrow .circle {
        fill: transparent !important;
        stroke: none !important;
    }
    
    /* Style the arrow path */
    .dropdown-arrow path {
        fill: #666 !important;
        transform-origin: center !important;
    }
    
    /* Header spanning both columns */
    .app-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #00695c 0%, #004d40 100%);
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 16px rgba(0,105,92,0.15);
    }
    .app-title {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
        color: white;
        letter-spacing: 0.5px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .app-subtitle {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.9);
        margin-bottom: 0;
        font-weight: 400;
    }
    
    /* Header controls */
    .header-controls {
        position: absolute;
        top: 1rem;
        right: 1rem;
        display: flex;
        gap: 0.5rem;
    }
    /* NEW: Styles for the new header controls group */
    .header-controls-group {
        padding: 0.5rem 1rem; /* Add some padding around the controls */
        justify-content: flex-end; /* Pushes content to the right */
        align-items: center; /* Vertically centers items in this row */
        margin-top: -1rem; /* Adjust this to pull it up slightly if it's too low */
        margin-bottom: 0.5rem; /* Space below the controls */
    }
     
               
    .header-controls button {
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.3);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.9rem;
    }
    .header-controls button:hover {
        background: rgba(255,255,255,0.3);
    }
    
    /* Two-column layout */
    .main-layout {
        display: flex;
        gap: 2rem;
        min-height: 70vh;
    }
    .chat-column {
        flex: 1;
        max-width: 50%;
        display: flex;
        flex-direction: column;
    }
    .info-column {
        flex: 1;
        max-width: 50%;
        display: flex;
        flex-direction: column;
    }
    
    /* Onboarding/Help Section */
    .onboarding-box {
        background: #fff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 16px rgba(0,105,92,0.08);
        border-left: 4px solid #00695c;
    }
    .onboarding-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #00695c;
        margin-bottom: 0.5rem;
    }
    .onboarding-text {
        color: #666;
        line-height: 1.5;
        margin-bottom: 1rem;
    }
    
    /* Suggested Prompts */
    .suggested-prompts {
        margin-bottom: 1rem;
    }
    .prompt-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .prompt-chip {
        background: #e8eaf6;
        color: #6200ea;
        border: 1px solid #6200ea;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .prompt-chip:hover {
        background: #6200ea;
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(98,0,234,0.2);
    }
    
    .gr-chatbot {
        flex: 1; /* This should already make it grow */
        height: auto !important; /* Allow height to be determined by flex container */
        min-height: 400px; /* Keep a minimum height */
    }
    
    /* Simple fix for green blocks - just target the specific elements causing issues */
    .gr-chatbot .prose::marker,
    .gr-chatbot .prose li::marker {
        color: inherit !important;
    }
    
    /* Remove any custom background colors from markers */
    .gr-chatbot .prose li::before {
        background: none !important;
    }
    
    /* Ensure expandable sections use arrows */
    .gr-chatbot details > summary {
        list-style: revert !important;
        cursor: pointer;
    }
    
    .gr-chatbot details > summary::marker,
    .gr-chatbot details > summary::-webkit-details-marker {
        color: #666 !important;
    }
    
    /* Remove any Material Design overrides for expandable sections */
    .gr-chatbot details,
    .gr-chatbot summary {
        background: transparent !important;
    }
    
    /* Make trash/delete button smaller and positioned correctly */
    .gr-chatbot button[aria-label*="Delete"], 
    .gr-chatbot button[aria-label*="Clear"], 
    .gr-chatbot .gr-button[title*="Delete"], 
    .gr-chatbot .gr-button[title*="Clear"] {
        width: 28px !important;
        height: 28px !important;
        min-width: 28px !important;
        min-height: 28px !important;
        padding: 4px !important;
        font-size: 0.75rem !important;
        position: absolute !important;
        top: 8px !important;
        right: 8px !important;
        z-index: 10 !important;
        border-radius: 50% !important;
        background: rgba(0,105,92,0.8) !important;
    }
    
    .gr-chatbot button[aria-label*="Delete"]:hover, 
    .gr-chatbot button[aria-label*="Clear"]:hover, 
    .gr-chatbot .gr-button[title*="Delete"]:hover, 
    .gr-chatbot .gr-button[title*="Clear"]:hover {
        background: rgba(0,77,64,0.9) !important;
        transform: scale(1.05) !important;
    }
    
    /* Input area */
    .chat-input-area {
        background: #fff;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(0,105,92,0.08);
        margin-bottom: 1rem;
    }
    
    /* Toggles section */
    .toggles-section {
        background: #fff;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(0,105,92,0.08);
    }
    .toggle-title {
        font-weight: 600;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    /* Right column - Info panel */
    .results-header {
        background: #fff;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 16px rgba(0,105,92,0.08);
        text-align: center;
        font-weight: 600;
        color: #00695c;
    }
    .results-dataframe {
        flex: 1;
        background: #fff;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(0,105,92,0.08);
        margin-bottom: 1rem;
    }
    .status-panel {
        background: #fff;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(0,105,92,0.08);
    }

    /* Buttons - Enhanced Material Design */
    button, .gr-button {
        background: #00695c;
        color: #fff;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,105,92,0.15);
        font-weight: 600;
        font-size: 1rem;
        padding: 0.75em 1.5em;
        min-height: 44px;
        position: relative;
        overflow: hidden;
        transition: all 0.2s;
        border: none;
    }
    button:hover, .gr-button:hover {
        background: #004d40;
        box-shadow: 0 6px 20px rgba(0,105,92,0.2);
        transform: translateY(-1px);
    }
    button:active, .gr-button:active {
        transform: translateY(0);
    }

    /* Inputs - Enhanced styling */
    input, textarea, .gr-textbox input, .gr-textbox textarea {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 1rem;
        background: #fff;
        transition: all 0.2s;
        color: #222;
    }
    input:focus, textarea:focus, .gr-textbox input:focus, .gr-textbox textarea:focus {
        border-color: #00695c;
        box-shadow: 0 0 0 3px rgba(0,105,92,0.1);
        outline: none;
    }
    /* Fix input font color in dark mode */
    .dark input, .dark textarea, .dark .gr-textbox input, .dark .gr-textbox textarea {
        color: #f3f4f6 !important;
        background: #222 !important;
        border-color: #444 !important;
    }
    
    /* DataFrame styling */
    .gr-dataframe {
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: auto !important;
        position: relative !important;
    }
    
    /* Prevent layout shift on header click */
    .gr-dataframe table {
        width: 100% !important;
        min-width: 100% !important;
        table-layout: fixed !important;
    }
    
    /* Header button styling */
    .gr-dataframe .header-button {
        width: 100% !important;
        text-align: left !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    /* Ensure container maintains scroll */
    .results-dataframe {
        overflow-x: auto !important;
        max-width: 100% !important;
        position: relative !important;
    }

    /* Make DataFrame cells non-editable */
    .gr-dataframe td {
        pointer-events: auto !important;
        user-select: none !important;
        -webkit-user-select: none !important;
    }

    /* Style link cells specifically */
    .gr-dataframe td:nth-child(7) {  /* 7th column is Link */
        cursor: pointer !important;
    }

    /* Style and prevent editing of input elements in DataFrame */
    .gr-dataframe input.svelte-1y3tas2 {
        pointer-events: none !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        -webkit-user-modify: read-only !important;
        -moz-user-modify: read-only !important;
        user-modify: read-only !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        font-family: inherit !important;
        font-size: inherit !important;
        color: inherit !important;
        cursor: pointer !important;
    }

    /* Style links in DataFrame */
    .gr-dataframe a {
        color: #2196F3 !important;
        text-decoration: underline !important;
        cursor: pointer !important;
        pointer-events: auto !important;
    }

    .gr-dataframe a:hover {
        color: #1976D2 !important;
        text-decoration: underline !important;
    }

    /* Allow interaction only with shortlist column inputs */
    .gr-dataframe td:last-child input.svelte-1y3tas2 {
        pointer-events: none !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        text-align: center !important;
        cursor: pointer !important;
    }

    /* Remove focus styles from inputs */
    .gr-dataframe input.svelte-1y3tas2:focus {
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* Allow interaction only with shortlist column */
    .gr-dataframe td:last-child {
        pointer-events: auto !important;
        cursor: pointer !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        -webkit-user-modify: read-only !important;
        -moz-user-modify: read-only !important;
        user-modify: read-only !important;
        font-family: system-ui, -apple-system, sans-serif !important;
        font-size: 16px !important;
        line-height: 1 !important;
        text-align: center !important;
        color: #666 !important;
        background: transparent !important;
        transition: all 0.2s ease !important;
    }

    /* Style shortlist column hover state */
    .gr-dataframe td:last-child:hover {
        color: #00695c !important;
        background: rgba(0,105,92,0.1) !important;
        border-radius: 4px;
    }

    /* Dark mode adaptations */
    .dark .gr-dataframe td:last-child {
        color: #d1d5db !important;
    }

    .dark .gr-dataframe td:last-child:hover {
        color: #9ca3af !important;
        background: rgba(156,163,175,0.1) !important;
    }

    /* NEW: Ensure checkbox tick is visible in dark mode */
    .dark input[type="checkbox"] {
        accent-color: #f3f4f6 !important; /* A very light gray/nearly white */
        /* You might also want to ensure the checkbox background is discernible */
        background-color: #555 !important; /* A slightly lighter background for the checkbox square itself */
        border-color: #888 !important; /* Make border visible */
    }
    .dark input[type="checkbox"]:checked {
        background-color: #00695c !important; /* Use your primary hue for checked state */
        border-color: #00695c !important;
    }           
               
    /* Prevent cell editing */
    .gr-dataframe td[contenteditable="true"] {
        -webkit-user-modify: read-only !important;
        -moz-user-modify: read-only !important;
        user-modify: read-only !important;
    }

    /* Fix for teal blocks around interactive elements */
    .gr-dataframe button,
    .gr-dataframe .gr-button,
    .gr-dataframe .svelte-vzs2gq,
    .cell-menu-button.svelte-vt38nd {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Hide cell menu buttons */
    .cell-menu-button.svelte-vt38nd,
    button[aria-label="Open cell menu"],
    .cell-menu-button {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        position: absolute !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }

    /* Hide selection buttons */
    .selection-button.svelte-1mp8yw1,
    button.selection-button,
    .selection-button-row,
    .selection-button-column {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        position: absolute !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }

    /* Style the expand/collapse arrow */
    button.svelte-vzs2gq.padded {
        background: transparent !important;
        border: none !important;
        padding: 4px !important;
        cursor: pointer !important;
        width: 24px !important;
        height: 24px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Remove any default button styling from DataFrame cells */
    .gr-dataframe td:last-child {
        background: transparent !important;
        cursor: pointer;
    }

    .gr-dataframe td:last-child:hover {
        background: rgba(0,105,92,0.1) !important;
        border-radius: 4px;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-layout {
            flex-direction: column;
        }
        .chat-column, .info-column {
            max-width: 100%;
        }
        .header-controls {
            position: relative;
            margin-top: 1rem;
        }
        .prompt-chips {
            flex-direction: column;
        }
    }

    /* Dark mode button - Compact styling */
    .dark-mode-btn {
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        min-height: 36px !important;
        padding: 6px !important;
        font-size: 1rem !important;
        border-radius: 50% !important;
        background: rgba(0,105,92,0.1) !important;
        border: 1px solid rgba(0,105,92,0.3) !important;
        color: #00695c !important;
        box-shadow: 0 2px 6px rgba(0,105,92,0.1) !important;
        transition: all 0.2s ease !important;
    }
    .dark-mode-btn:hover {
        background: rgba(0,105,92,0.2) !important;
        transform: scale(1.05) !important;
        box-shadow: 0 3px 8px rgba(0,105,92,0.2) !important;
    }

    /* Dark mode adaptations */
    .dark {
        background-color: #111827 !important;
    }
    .dark .app-title { color: #f9fafb !important; }
    .dark .app-subtitle { color: #d1d5db !important; }
    .dark .gradio-container { background-color: #1f2937 !important; }
    .dark .onboarding-box, .dark .chat-input-area, .dark .toggles-section,
    .dark .results-header, .dark .results-dataframe, .dark .status-panel {
        background: #374151 !important;
        color: #f3f4f6 !important;
    }
    .dark .dark-mode-btn {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: #f3f4f6 !important;
    }
    .dark .dark-mode-btn:hover {
        background: rgba(255,255,255,0.2) !important;
    }
    
    /* Make chatbot response font one size bigger */
    .gr-chatbot .prose, .gr-chatbot .prose * {
        font-size: 1.25rem !important;
        line-height: 1.7 !important;
    }
""") as demo:
    # Header Section
    with gr.Row():
        with gr.Column():
            gr.HTML("""
                <div class="app-header">
                    <h1 class="app-title">🏠 NYC Voucher Housing Navigator</h1>
                    <p class="app-subtitle">Find safe, voucher-friendly housing in NYC with AI assistance</p>
                </div>
            """)
    
    # Header controls row (for language selector and dark mode toggle)
# This row sits above the main content layout and pushes controls to the right
    with gr.Row(elem_classes=["header-controls-group"]):
        with gr.Column(scale=1): # This column acts as a flexible spacer, pushing content to the right
            pass
    with gr.Column(scale=0): # This column will contain our controls, scale=0 keeps it compact
            dark_mode_toggle = gr.Button("🌙", size="sm", elem_classes=["dark-mode-btn"], scale=0)
    
    # Initialize app state
    app_state = gr.State(create_initial_state())
    
    # Create initial greeting message for Navi
    def create_initial_greeting(language="en"):
        greeting_message = {
            "role": "assistant",
            "content": i18n_dict[language]["intro_greeting"]
        }
        return [greeting_message]
    
    # Main two-column layout
    with gr.Row(elem_classes=["main-layout"]):
        # LEFT COLUMN: Chat Panel
        with gr.Column(elem_classes=["chat-column"]):
            # Chat Section
            chatbot = gr.Chatbot(
                label="💬 Conversation",
                height=400,
                type="messages",
                value=create_initial_greeting(),
                elem_classes=["gr-chatbot"],
                show_label=True,
                render_markdown=True
            )
            
                    # Chat Input Area
            with gr.Column(elem_classes=["chat-input-area"]):
                msg = gr.Textbox(
                label="Your Message",
                placeholder="Type your request, like '2 bedroom in Queens under $2500'...",
                lines=2,
                container=False
            )
            send_btn = gr.Button("Send Message", variant="primary")
            
            # NEW CODE HERE: Add the Strict Mode checkbox
            with gr.Column(elem_classes=["toggles-section"]): # Reusing the style
                gr.Markdown("#### 🎛️ Search Preferences")
                visible_strict_mode_checkbox = gr.Checkbox(
                    label=i18n_dict["en"]["strict_mode_label"], # Will be updated by i18n
                    value=False, # Initial value
                    interactive=True,
                    container=True
                )
            
        # RIGHT COLUMN: Aggregated Information Panel
        with gr.Column(elem_classes=["info-column"]):

            # Language dropdown (moved here)
            language_dropdown = gr.Dropdown(
                label=None,
                choices=[("English", "en"), ("Español", "es"), ("中文", "zh"), ("বাংলা", "bn")],
                value="en",
                container=False,
                show_label=False,
                scale=0,
                min_width=100,
                info=i18n_dict["en"]["language_selector"]
            )

            # Results Header/Status
            progress_info = gr.HTML(
                value='<div class="results-header">🏠 Ready to search for listings...</div>',
                elem_classes=["results-header"]
            )
            
            # DataFrame Section
            with gr.Column(elem_classes=["results-dataframe"]):
                            results_df = gr.DataFrame(
                value=pd.DataFrame(),
                label="📋 Found Listings",
                interactive=True,  # Make interactive for shortlist functionality
                row_count=(10, "dynamic"),
                wrap=True,
                visible=False,
                datatype=["number", "str", "str", "str", "number", "str", "html", "str", "str"],  # Changed Link column to html type
                column_widths=["50px", "300px", "100px", "100px", "100px", "120px", "100px", "200px", "80px"]  # Set fixed column widths
                )
            
            # Shortlist Panel
            with gr.Column(elem_classes=["status-panel"]):
                def create_initial_shortlist_display():
                    return """
                    <div style="text-align: center; color: #666;">
                        <h4>📌 Your Shortlist (0 saved)</h4>
                        <p>Click ➕ in the listings table to save properties to your shortlist.<br/>
                        Use chat commands like "show my shortlist" to manage saved listings.</p>
                        <hr style="margin: 1rem 0; border: 1px solid #eee;">
                        <div style="color: #999; font-style: italic;">No saved listings yet</div>
                    </div>
                    """
                
                shortlist_display = gr.HTML(
                    value=create_initial_shortlist_display(),
                    elem_id="shortlist-display"
                )

    # Add all the handler functions before wiring up events
    def update_shortlist_display(state: Dict) -> str:
        """Create HTML for the shortlist display panel."""
        shortlist = get_shortlist(state)
        count = len(shortlist)
        
        if count == 0:
            return """
            <div style="text-align: center; color: #666;">
                <h4>📌 Your Shortlist (0 saved)</h4>
                <p>Click ➕ in the listings table to save properties to your shortlist.<br/>
                Use chat commands like "show my shortlist" to manage saved listings.</p>
                <hr style="margin: 1rem 0; border: 1px solid #eee;">
                <div style="color: #999; font-style: italic;">No saved listings yet</div>
            </div>
            """
        
        # Create HTML for shortlist items
        items_html = ""
        for i, item in enumerate(shortlist[:5], 1):  # Show top 5
            priority_badge = ""
            if item.get("priority"):
                priority_badge = f'<span style="background: #ff9800; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;">⭐ {item["priority"]}</span>'
            
            items_html += f"""
            <div style="margin: 0.5rem 0; padding: 0.5rem; background: #f9f9f9; border-radius: 6px; text-align: left;">
                <div style="font-weight: 600; font-size: 0.9em;">{item['address'][:40]}{'...' if len(item['address']) > 40 else ''}</div>
                <div style="color: #666; font-size: 0.8em;">{item['price']} • {item['risk_level']}</div>
                {priority_badge}
            </div>
            """
        
        if count > 5:
            items_html += f'<div style="color: #999; font-style: italic; text-align: center;">... and {count - 5} more</div>'
        
        return f"""
        <div style="color: #666;">
            <h4 style="text-align: center;">📌 Your Shortlist ({count} saved)</h4>
            <p style="text-align: center; font-size: 0.9em;">Click ➕/✅ in the table or use chat commands</p>
            <hr style="margin: 1rem 0; border: 1px solid #eee;">
            {items_html}
        </div>
        """

    def handle_shortlist_click(evt: gr.SelectData, state: Dict):
        """Handle shortlist button clicks and link clicks in the DataFrame."""
        try:
            # Handle clicks on the Link column (index 6)
            if evt.index[1] == 6:  # Link column
                listings = state.get("listings", [])
                if listings and evt.index[0] < len(listings):
                    listing = listings[evt.index[0]]
                    url = listing.get("url", "")
                    if url and url != "No link available":
                        # The URL will be opened by the browser since we're using an HTML anchor tag
                        return gr.update(), gr.update(), gr.update(), state
                return gr.update(), gr.update(), gr.update(), state
            
            # Handle clicks on the Shortlist column (index 8)
            if evt.index[1] != 8:  # Shortlist column is index 8 (0-based)
                return gr.update(), gr.update(), gr.update(), state
            
            listings = state.get("listings", [])
            if not listings or evt.index[0] >= len(listings):
                return gr.update(), gr.update(), gr.update(), state
                
            listing = listings[evt.index[0]]
            
            # Toggle shortlist status
            if is_shortlisted(listing, state):
                # Remove from shortlist
                listing_id = str(listing.get("id", listing.get("address", "")))
                updated_state, message = remove_from_shortlist(listing_id, state)
            else:
                # Add to shortlist
                updated_state, message = add_to_shortlist(listing, state)
                
            # Update DataFrame display
            df = create_listings_dataframe(listings, updated_state)
            
            # Update progress info with shortlist count
            shortlist_count = len(updated_state.get('shortlist', []))
            status_text = f"Showing {len(listings)} listings ({shortlist_count} in shortlist)"
            
            # Update shortlist display
            shortlist_html = update_shortlist_display(updated_state)
            
            return gr.update(value=df), gr.update(value=status_text), gr.update(value=shortlist_html), updated_state
            
        except Exception as e:
            print(f"Error in handle_shortlist_click: {e}")
            return gr.update(), gr.update(), gr.update(), state

    def handle_shortlist_command(message: str, history: list, state: Dict):
        """Handle shortlist-related chat commands."""
        message_lower = message.lower()
        listings = state.get("listings", [])
        
        # Show shortlist command
        if "show shortlist" in message_lower or "view shortlist" in message_lower or "my shortlist" in message_lower:
            shortlist_summary = get_shortlist_summary(state)
            shortlist_msg = create_chat_message_with_metadata(
                shortlist_summary,
                "📋 Your Shortlist"
            )
            history.append(shortlist_msg)
            
            # Update DataFrame and shortlist display
            if listings:
                current_df = create_listings_dataframe(listings, state)
                shortlist_count = len(state.get("shortlist", []))
                status_text = f"Showing {len(listings)} listings ({shortlist_count} in shortlist)"
                return (history, gr.update(value=current_df, visible=True), 
                       gr.update(value=status_text), state)
            else:
                return (history, gr.update(), gr.update(value="Shortlist displayed"), state)
        
        # Save listing command (e.g., "save listing 2", "add listing 3 to shortlist")
        save_patterns = ["save listing", "add listing", "shortlist listing"]
        if any(pattern in message_lower for pattern in save_patterns):
            # Extract listing number
            import re
            numbers = re.findall(r'\d+', message_lower)
            if numbers and listings:
                try:
                    listing_index = int(numbers[0]) - 1  # Convert to 0-based index
                    if 0 <= listing_index < len(listings):
                        listing = listings[listing_index]
                        updated_state, status_message = add_to_shortlist(listing, state)
                        
                        success_msg = create_chat_message_with_metadata(
                            status_message,
                            "📌 Shortlist Updated"
                        )
                        history.append(success_msg)
                        
                        # Update DataFrame and shortlist display
                        current_df = create_listings_dataframe(listings, updated_state)
                        shortlist_count = len(updated_state.get("shortlist", []))
                        status_text = f"Showing {len(listings)} listings ({shortlist_count} in shortlist)"
                        return (history, gr.update(value=current_df, visible=True), 
                               gr.update(value=status_text), updated_state)
                    else:
                        error_msg = create_chat_message_with_metadata(
                            f"❌ Invalid listing number. Please specify a number between 1 and {len(listings)}.",
                            "❌ Error"
                        )
                        history.append(error_msg)
                except ValueError:
                    error_msg = create_chat_message_with_metadata(
                        "❌ Please specify a valid listing number (e.g., 'save listing 2').",
                        "❌ Error"
                    )
                    history.append(error_msg)
            else:
                if not listings:
                    error_msg = create_chat_message_with_metadata(
                        "❌ No listings available to save. Please search for apartments first.",
                        "❌ No Listings"
                    )
                else:
                    error_msg = create_chat_message_with_metadata(
                        "❌ Please specify which listing to save (e.g., 'save listing 2').",
                        "❌ Missing Number"
                    )
                history.append(error_msg)
        
        # Clear shortlist command
        elif "clear shortlist" in message_lower or "empty shortlist" in message_lower:
            from shortlist_utils import clear_shortlist
            updated_state, status_message = clear_shortlist(state)
            
            clear_msg = create_chat_message_with_metadata(
                status_message,
                "📋 Shortlist Cleared"
            )
            history.append(clear_msg)
            
            # Update DataFrame and shortlist display
            if listings:
                current_df = create_listings_dataframe(listings, updated_state)
                status_text = f"Showing {len(listings)} listings (shortlist cleared)"
                return (history, gr.update(value=current_df, visible=True), 
                       gr.update(value=status_text), updated_state)
            else:
                return (history, gr.update(), gr.update(value="Shortlist cleared"), updated_state)
        
        # Default: preserve current state
        if listings:
            current_df = create_listings_dataframe(listings, state)
            shortlist_count = len(state.get("shortlist", []))
            status_text = f"Showing {len(listings)} listings ({shortlist_count} in shortlist)"
            return (history, gr.update(value=current_df, visible=True), 
                   gr.update(value=status_text), state)
        else:
            return (history, gr.update(), gr.update(value="Shortlist command processed"), state)
    
    def handle_listing_question(message: str, history: list, state: Dict):
        """Handle questions about existing listings."""
        listings = state.get("listings", [])
        
        if not listings:
            no_listings_msg = create_chat_message_with_metadata(
                "I don't have any listings to show you yet. Please search for apartments first!",
                "📋 No Listings Available"
            )
            history.append(no_listings_msg)
            return (history, gr.update(), gr.update(value="No search criteria set"), state)
        
        message_lower = message.lower()
        
        # Parse which listing they're asking about
        listing_index = None
        
        # Number word mapping
        number_words = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
            'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
        }
        
        # Navigation patterns that depend on current state
        if "current_listing_index" in state and state["current_listing_index"] is not None:
            current_idx = state["current_listing_index"]
            if any(word in message_lower for word in ["next", "forward"]):
                listing_index = min(current_idx + 1, len(listings) - 1)
            elif any(word in message_lower for word in ["previous", "prev", "back"]):
                listing_index = max(current_idx - 1, 0)
        
        # If navigation wasn't used, try other patterns
        if listing_index is None:
            # Check for relative position patterns first
            relative_patterns = {
                r"(?:the\s+)?last(?:\s+listing)?": lambda: len(listings) - 1,
                r"(?:the\s+)?(?:second\s+to\s+last|next\s+to\s+last|penultimate|last\s+but\s+one)(?:\s+listing)?": lambda: len(listings) - 2 if len(listings) > 1 else 0,
                r"(?:the\s+)?(first|1st)(?:\s+listing)?": lambda: 0,
                r"(?:the\s+)?(second|2nd)(?:\s+listing)?": lambda: 1,
                r"(?:the\s+)?(third|3rd)(?:\s+listing)?": lambda: 2,
                r"(?:the\s+)?(fourth|4th)(?:\s+listing)?": lambda: 3,
                r"(?:the\s+)?(fifth|5th)(?:\s+listing)?": lambda: 4
            }
            
            for pattern, index_func in relative_patterns.items():
                if re.search(pattern, message_lower):
                    listing_index = index_func()
                    break
            
            # If no relative position found, try numeric numbers
            if listing_index is None:
                numbers = re.findall(r'\b(-?\d+(?:\.\d+)?)\b', message_lower)
                if numbers:
                    try:
                        # Convert to float first to handle decimals
                        num = float(numbers[0])
                        # Check if it's a whole number and non-negative
                        if num.is_integer() and num > 0:
                            listing_index = int(num) - 1
                    except:
                        pass
                
                # If no valid numeric number found, try word numbers
                if listing_index is None:
                    for word, number in number_words.items():
                        word_patterns = [
                            f"number {word}",
                            f"no. {word}",
                            f"#{word}",
                            f"listing {word}",
                            f" {word} ",  # Space-bounded word
                            f"^{word} ",  # Start of string
                            f" {word}$"   # End of string
                        ]
                        if any(pattern in f" {message_lower} " for pattern in word_patterns):
                            if number > 0:  # Only accept positive numbers
                                listing_index = number - 1
                            break
                    
                    # If still no match, try patterns
                    if listing_index is None:
                        # Check for various patterns of asking about a listing
                        listing_patterns = {
                            # Basic patterns with flexible spacing
                            r"(?:can\s+(?:i|you)\s+)?(?:see|show|tell\s+(?:me\s+)?about|what\s+about|view)\s+listing\s*#?\s*(-?\d+)": lambda x: int(x) - 1,
                            r"(?:what\s+is|what's|whats|how\s+about|details\s+for)\s+listing\s*#?\s*(-?\d+)": lambda x: int(x) - 1,
                            r"#\s*(-?\d+)": lambda x: int(x) - 1,
                            r"listing\s*#?\s*(-?\d+)": lambda x: int(x) - 1,
                            
                            # Informal/casual patterns
                            r"(?:hey|please|could you|i'd like to|let me)\s+(?:see|show)\s+listing\s*#?\s*(-?\d+)": lambda x: int(x) - 1,
                            r"(?:apartment|property|unit)\s*#?\s*(-?\d+)": lambda x: int(x) - 1,
                            r"number\s*(-?\d+)(?:\s+please)?": lambda x: int(x) - 1,
                            
                            # Alternative number formats
                            r"listing\s+(?:no\.?|number)\s+(-?\d+)": lambda x: int(x) - 1,
                            
                            # Mixed format patterns
                            r"(?:first|1st)\s+(?:show|see)\s+listing\s*#?\s*(-?\d+)": lambda x: int(x) - 1,
                            r"(?:either\s+)?listing\s*#?\s*(-?\d+)(?:\s+or\s+(?:the\s+)?(?:second|2nd|third|3rd)\s+(?:one|listing))?": lambda x: int(x) - 1
                        }
                        
                        # Try each pattern
                        for pattern, index_func in listing_patterns.items():
                            match = re.search(pattern, message_lower)
                            if match:
                                try:
                                    num = int(match.group(1))
                                    if num > 0:  # Only accept positive numbers
                                        listing_index = index_func(match.group(1))
                                    break
                                except:
                                    continue
        
        # Validate index if one was found
        if listing_index is not None:
            # Handle special cases
            if listing_index < 0 or listing_index >= len(listings):
                invalid_msg = create_chat_message_with_metadata(
                    f"I only have {len(listings)} listings available. Please ask about a listing number between 1 and {len(listings)}.",
                    "❌ Invalid Listing Number"
                )
                history.append(invalid_msg)
                # Preserve the current DataFrame
                current_df = create_listings_dataframe(listings, state)
                return (history, gr.update(value=current_df, visible=True), 
                       gr.update(value=f"Showing {len(listings)} listings"), state)
        else:
            # Default to first listing if no specific index found
            listing_index = 0
        
        # Get the requested listing
        listing = listings[listing_index]
        listing_num = listing_index + 1
        
        # Update state to track current listing
        updated_state = update_app_state(state, {
            "current_listing": listing,
            "current_listing_index": listing_index
        })
        
        # Create detailed response
        address = listing.get("address") or listing.get("title", "N/A")
        price = listing.get("price", "N/A")
        url = listing.get("url", "No link available")
        risk_level = listing.get("risk_level", "❓")
        violations = listing.get("building_violations", 0)
        
        response_text = f"""
**Listing #{listing_num} Details:**

🏠 **Address:** {address}
💰 **Price:** {price}
{risk_level} **Safety Level:** {violations} violations
🔗 **Link:** {url}

You can copy and paste this link into your browser to view the full listing with photos and contact information!

**Would you like to know more about this listing? I can help you with:**
1. 🚇 See the nearest subway/transit options
2. 🏫 See nearby schools
3. 📧 Draft an email to inquire about this listing
4. 🏠 View another listing

Just let me know what information you'd like to see!
        """.strip()
        
        listing_response_msg = create_chat_message_with_metadata(
            response_text,
            f"🏠 Listing #{listing_num} Details"
        )
        history.append(listing_response_msg)
        
        # Preserve existing DataFrame
        current_df = create_listings_dataframe(listings, updated_state)
        return (history, gr.update(value=current_df, visible=True), 
               gr.update(value=f"Showing {len(listings)} listings"), updated_state)

    # Add this function before handle_chat_message
    def handle_listing_context_question(message: str, history: list, state: Dict):
        """Handle context-dependent questions about the current listing (subway, school proximity)."""
        current_listing = state.get("current_listing")
        current_listing_index = state.get("current_listing_index")
        
        # If no current listing but user is asking about transit/schools, give helpful response
        if not current_listing:
            message_lower = message.lower().strip()
            
            # Check if it's a transit/school question
            transit_school_patterns = [
                r'nearest\s+(subway|train|school|transit)',
                r'closest\s+(subway|train|school|transit)',
                r'what.*?(nearest|closest)\s+(subway|train|school|transit)',
                r'where.*?(nearest|closest)\s+(subway|train|school|transit)',
                r'how.*?far.*?(subway|train|school|transit)',
                r'^(subway|train|school|transit)\?$'
            ]
            
            import re
            if any(re.search(pattern, message_lower) for pattern in transit_school_patterns):
                response_text = """🚇 **Transit & School Information**

To find the nearest subway stations and schools for a specific listing, I need to know which property you're interested in. 

**Please:**
1. First search for listings using a command like "find me apartments in Brooklyn" or "search for Section 8 housing"
2. Then ask about transit/schools for a specific listing (e.g., "what's the nearest subway for listing #1")

**Or if you have a specific address in mind:**
Tell me the address and I can look up transit and school information for that location.

Would you like me to help you search for listings first?"""
                
                context_msg = create_chat_message_with_metadata(
                    response_text,
                    "🚇 Transit & School Info"
                )
                history.append(context_msg)
                return (history, gr.update(), gr.update(value="Please search for listings first"), state)
            else:
                return None  # Not a transit/school question, continue with normal flow
        
        # Continue with normal context question handling for when we have a current listing
        
        message_lower = message.lower().strip()
        listing_num = (current_listing_index or 0) + 1
        address = current_listing.get("address") or current_listing.get("title", "N/A")
        
        # Check for subway/transit request
        subway_patterns = [
            r'subway', r'transit', r'train', r'nearest.*subway', r'closest.*subway',
            r'nearest.*transit', r'closest.*transit', r'what.*nearest.*subway', 
            r'where.*nearest.*subway', r'how.*far.*subway', r'what.*nearest.*transit',
            r'where.*nearest.*transit', r'how.*far.*transit'
        ]
        
        # Check for school request  
        school_patterns = [
            r'school', r'nearest.*school', r'closest.*school', r'what.*nearest.*school',
            r'where.*nearest.*school', r'how.*far.*school'
        ]
        
        import re
        
        def get_coordinates_for_listing(listing):
            """Get coordinates for a listing, using geocoding if necessary."""
            # First try to get coordinates directly from listing
            if listing.get("latitude") and listing.get("longitude"):
                return (float(listing["latitude"]), float(listing["longitude"]))
            
            # If no direct coordinates, try to geocode the address
            address = listing.get("address")
            if not address or address == "N/A":
                return None
            
            try:
                # Use the geocoding tool
                from geocoding_tool import GeocodingTool
                geocoder = GeocodingTool()
                geocode_result_json = geocoder.forward(address)
                geocode_result = json.loads(geocode_result_json)
                
                if geocode_result.get("status") == "success":
                    data = geocode_result.get("data", {})
                    lat = data.get("latitude")
                    lon = data.get("longitude")
                    if lat and lon:
                        return (float(lat), float(lon))
                
                return None
            except Exception as e:
                print(f"❌ Geocoding error: {e}")
                return None
        
        # Handle subway questions
        if any(re.search(pattern, message_lower) for pattern in subway_patterns):
            # Try to get coordinates from the current listing
            coordinates = get_coordinates_for_listing(current_listing)
            
            if coordinates:
                try:
                    # Use the nearest subway tool directly
                    from nearest_subway_tool import nearest_subway_tool
                    subway_result_json = nearest_subway_tool.forward(coordinates[0], coordinates[1])
                    subway_result = json.loads(subway_result_json)
                    
                    if subway_result.get("status") == "success":
                        data = subway_result.get("data", {})
                        station_name = data.get("station_name", "Unknown")
                        lines = data.get("lines", "N/A")
                        distance = data.get("distance_miles", 0)
                        is_accessible = data.get("is_accessible", False)
                        entrance_type = data.get("entrance_type", "Unknown")
                        
                        accessibility_text = "♿ Wheelchair accessible" if is_accessible else f"⚠️ Not wheelchair accessible ({entrance_type} entrance)"
                        walking_time = round(distance * 20) if distance else "N/A"  # 20 minutes per mile at 3 mph
                        
                        response_text = f"""
🚇 **Nearest Subway Information for Listing #{listing_num}:**

**Station:** {station_name}
**Lines:** {lines}
**Distance:** {distance:.2f} miles (about {walking_time} minute walk)
**Accessibility:** {accessibility_text}

Would you like to:
1. 🏫 See nearby schools for this listing?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
                        """.strip()
                    else:
                        response_text = f"""
🚇 **Subway Information for Listing #{listing_num}:**

I couldn't find detailed subway information for this listing at the moment. 

**Address:** {address}

You can check the MTA website or app for nearby stations using this address.

Would you like to:
1. 🏫 See nearby schools for this listing?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
                        """.strip()
                        
                except Exception as e:
                    response_text = f"""
🚇 **Subway Information for Listing #{listing_num}:**

I encountered an error while looking up subway information: {str(e)}

**Address:** {address}

You can check the MTA website or app for nearby stations using this address.

Would you like to:
1. 🏫 See nearby schools for this listing?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
                    """.strip()
            else:
                response_text = f"""
🚇 **Subway Information for Listing #{listing_num}:**

I don't have coordinate data for this listing to find nearby subway stations.

**Address:** {address}

You can check the MTA website or app for nearby stations using this address.

Would you like to:
1. 🏫 See nearby schools for this listing?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
            """.strip()
            
            subway_msg = create_chat_message_with_metadata(
                response_text,
                f"🚇 Subway Info - Listing #{listing_num}"
            )
            history.append(subway_msg)
            
            # Preserve existing DataFrame
            listings = state.get("listings", [])
            current_df = create_listings_dataframe(listings, state)
            return (history, gr.update(value=current_df, visible=True), 
                   gr.update(value=f"Showing {len(listings)} listings"), state)
        
        # Handle school questions
        elif any(re.search(pattern, message_lower) for pattern in school_patterns):
            # Try to get coordinates from the current listing
            coordinates = get_coordinates_for_listing(current_listing)
            
            if coordinates:
                try:
                    # Use the near school tool directly
                    from near_school_tool import near_school_tool
                    school_result_json = near_school_tool.forward(coordinates[0], coordinates[1])
                    school_result = json.loads(school_result_json)
                    
                    if school_result.get("status") == "success":
                        schools = school_result.get("data", {}).get("schools", [])
                        
                        if schools:
                            response_text = f"🏫 **Nearby Schools for Listing #{listing_num}:**\n\n"
                            
                            for i, school in enumerate(schools[:3], 1):  # Show top 3 schools
                                name = school.get("school_name", "Unknown School")
                                school_type = school.get("school_type", "Unknown")
                                grades = school.get("grades", "N/A")
                                distance = school.get("distance_miles", 0)
                                walking_time = school.get("walking_time_minutes", "N/A")
                                school_address = school.get("address", "N/A")
                                
                                response_text += f"""
{i}. **{name}**
   - Type: {school_type}
   - Grades: {grades}
   - Distance: {distance:.2f} miles ({walking_time} minute walk)
   - Address: {school_address}
"""
                            
                            response_text += f"""
Would you like to:
1. 🚇 See the nearest subway/transit options?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
                            """.strip()
                        else:
                            response_text = f"""
🏫 **School Information for Listing #{listing_num}:**

No schools found within a reasonable distance of this listing.

**Address:** {address}

You can check the NYC Department of Education website for school zone information.

Would you like to:
1. 🚇 See the nearest subway/transit options?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
                            """.strip()
                    else:
                        response_text = f"""
🏫 **School Information for Listing #{listing_num}:**

I couldn't find detailed school information for this listing at the moment.

**Address:** {address}

You can check the NYC Department of Education website for nearby schools using this address.

Would you like to:
1. 🚇 See the nearest subway/transit options?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
                        """.strip()
                        
                except Exception as e:
                    response_text = f"""
🏫 **School Information for Listing #{listing_num}:**

I encountered an error while looking up school information: {str(e)}

**Address:** {address}

You can check the NYC Department of Education website for nearby schools using this address.

Would you like to:
1. 🚇 See the nearest subway/transit options?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
                    """.strip()
            else:
                response_text = f"""
🏫 **School Information for Listing #{listing_num}:**

I don't have coordinate data for this listing to find nearby schools.

**Address:** {address}

You can check the NYC Department of Education website for nearby schools using this address.

Would you like to:
1. 🚇 See the nearest subway/transit options?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
            """.strip()
            
            school_msg = create_chat_message_with_metadata(
                response_text,
                f"🏫 School Info - Listing #{listing_num}"
            )
            history.append(school_msg)
            
            # Preserve existing DataFrame
            listings = state.get("listings", [])
            current_df = create_listings_dataframe(listings, state)
            return (history, gr.update(value=current_df, visible=True), 
                   gr.update(value=f"Showing {len(listings)} listings"), state)
        
        # Not a recognized context question
        return None

    def handle_chat_message(message: str, history: list, current_state: Dict, 
                           strict_mode: bool):
        """Enhanced chat handler with new agent workflow and state management."""
        
        # CRITICAL DEBUG: Log everything at the entry point
        print(f"🚨 CHAT HANDLER CALLED:")
        print(f"  Message: '{message}'")
        print(f"  Strict mode: {strict_mode}")
        
        log_tool_action("GradioApp", "user_message_received", {
            "message": message,
            "timestamp": current_timestamp()
        })
        
        # Detect language from user message
        detected_language = detect_language_from_message(message)
        current_language = current_state.get("preferences", {}).get("language", "en")
        
        # Check if language has changed based on user input
        language_changed = False
        if detected_language != current_language and detected_language != "en":
            # Language changed - update state and greeting
            current_language = detected_language
            language_changed = True
            print(f"🌍 Language detected: {detected_language}")
        
        # Add user message to history
        history.append({"role": "user", "content": message})
        
        # Update preferences in state (including detected language)
        new_state = update_app_state(current_state, {
            "preferences": {
                "strict_mode": strict_mode,
                "language": current_language
            }
        })
        
        try:
            # Check for context-dependent questions about current listing first
            if detect_context_dependent_question(message) and new_state.get("current_listing"):
                print(f"🔍 CALLING handle_listing_context_question")
                context_result = handle_listing_context_question(message, history, new_state)
                if context_result:
                    return context_result
            
            # Use V0's enhanced classification
            message_type = enhanced_classify_message(message, new_state)
            
            if message_type == "email_request":
                print(f"📧 CALLING enhanced_handle_email_request")
                # Call V0's enhanced email handler
                enhanced_result = enhanced_handle_email_request(message, history, new_state)
                # Return with state preservation
                return (enhanced_result[0], enhanced_result[1], 
                       gr.update(value="Email template generated"), new_state)
            elif message_type == "shortlist_command":
                print(f"📌 CALLING handle_shortlist_command")
                return handle_shortlist_command(message, history, new_state)
            elif message_type == "new_search":
                print(f"🏠 CALLING handle_housing_search")
                return handle_housing_search(message, history, new_state, strict_mode)
            elif message_type == "listing_question":
                print(f"📋 CALLING handle_listing_question")
                return handle_listing_question(message, history, new_state)
            else:
                print(f"💬 CALLING handle_general_conversation")
                # Handle general conversation with caseworker agent
                return handle_general_conversation(message, history, new_state)
                
        except Exception as e:
            log_tool_action("GradioApp", "error", {
                "error": str(e),
                "message": message
            })
            
            error_msg = create_chat_message_with_metadata(
                f"I apologize, but I encountered an error: {str(e)}",
                "❌ Error"
            )
            history.append(error_msg)
            
            return (history, gr.update(value=pd.DataFrame(), visible=False), 
                   gr.update(value="Error occurred"), new_state)

    def handle_housing_search(message: str, history: list, state: Dict, 
                            strict_mode: bool):
        """Handle housing search requests with the new agent workflow."""
        search_id = f"search_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        # Extract borough from message if mentioned
        message_lower = message.lower()
        detected_borough = None
        borough_map = {
            "bronx": "bronx",
            "brooklyn": "brooklyn", 
            "manhattan": "manhattan",
            "queens": "queens",
            "staten island": "staten_island"
        }
        
        for borough_name, borough_code in borough_map.items():
            if borough_name in message_lower:
                detected_borough = borough_code
                break
        
        # Use detected borough from message
        if detected_borough:
            target_borough = detected_borough
            print(f"🎯 Using detected borough from message: {detected_borough}")
        else:
            target_borough = None
            print(f"🌍 No borough specified - will search all boroughs")
        
        # Update search message based on target
        if target_borough:
            search_text = f"🔍 Searching for voucher-friendly listings in {target_borough.title()}..."
            print(f"🎯 BOROUGH FILTER ACTIVE: Searching only {target_borough.upper()}")
        else:
            search_text = "🔍 Searching for voucher-friendly listings across NYC..."
            print(f"🌍 NO BOROUGH FILTER: Searching all NYC boroughs")
            
        search_msg = create_chat_message_with_metadata(
            search_text,
            "🔍 Searching Listings",
            parent_id=search_id
        )
        history.append(search_msg)
        
        try:
            # Use BrowserAgent to search for listings
            search_query = "Section 8"
            
            # Debug: Log exactly what we're passing to browser agent
            boroughs_param = target_borough if target_borough else ""
            print(f"📡 Calling browser_agent.forward with boroughs='{boroughs_param}'")
            
            browser_result = browser_agent.forward(
                query=search_query,
                boroughs=boroughs_param
            )
            
            browser_data = json.loads(browser_result)
            
            if browser_data.get("status") != "success":
                error_msg = create_chat_message_with_metadata(
                    f"❌ Search failed: {browser_data.get('error', 'Unknown error')}",
                    "❌ Search Failed"
                )
                history.append(error_msg)
                return (history, gr.update(), gr.update(value="Search failed"), state)
            
            listings = browser_data["data"]["listings"]
            search_duration = browser_data["data"]["metadata"]["duration"]
            
            # Update search completion message
            search_complete_msg = create_chat_message_with_metadata(
                f"✅ Found {len(listings)} potential listings",
                "🔍 Search Complete",
                duration=search_duration,
                parent_id=search_id
            )
            history.append(search_complete_msg)
            
            if not listings:
                no_results_msg = create_chat_message_with_metadata(
                    "I couldn't find any voucher-friendly listings matching your criteria. Try adjusting your search parameters.",
                    "📋 No Results"
                )
                history.append(no_results_msg)
                return (history, gr.update(), gr.update(value="No listings found"), state)
            
            # Stage 2: Enrich listings with violation data
            violation_msg = create_chat_message_with_metadata(
                f"🏢 Checking building safety for {len(listings)} listings...",
                "🏢 Safety Analysis",
                parent_id=search_id
            )
            history.append(violation_msg)
            
            enriched_listings = []
            for i, listing in enumerate(listings):
                address = listing.get("address") or listing.get("title", "")
                if not address:
                    # Add default violation data if no address
                    enriched_listing = {
                        **listing,
                        "building_violations": 0,
                        "risk_level": RiskLevel.UNKNOWN.value,
                        "last_inspection": "N/A",
                        "violation_summary": "No address available"
                    }
                    enriched_listings.append(enriched_listing)
                    continue
                
                try:
                    violation_result = violation_agent.forward(address)
                    violation_data = json.loads(violation_result)
                    
                    if violation_data.get("status") == "success":
                        data = violation_data.get("data", {})
                        enriched_listing = {
                            **listing,
                            "building_violations": data.get("violations", 0),
                            "risk_level": data.get("risk_level", RiskLevel.UNKNOWN.value),
                            "last_inspection": data.get("last_inspection", "N/A"),
                            "violation_summary": data.get("summary", "No data available")
                        }
                    else:
                        # Add default violation data if check failed
                        enriched_listing = {
                            **listing,
                            "building_violations": 0,
                            "risk_level": RiskLevel.UNKNOWN.value,
                            "last_inspection": "N/A",
                            "violation_summary": "Could not verify"
                        }
                    
                    enriched_listings.append(enriched_listing)
                    
                except Exception as e:
                    print(f"❌ Failed to check violations for {address}: {str(e)}")
                    # Add default violation data on error
                    enriched_listing = {
                        **listing,
                        "building_violations": 0,
                        "risk_level": RiskLevel.UNKNOWN.value,
                        "last_inspection": "N/A",
                        "violation_summary": "Check failed"
                    }
                    enriched_listings.append(enriched_listing)
            
            # Update enrichment completion message
            enrichment_complete_msg = create_chat_message_with_metadata(
                f"✅ Safety analysis complete for {len(enriched_listings)} listings",
                "🏢 Safety Analysis Complete",
                parent_id=search_id
            )
            history.append(enrichment_complete_msg)
            
            # Apply strict mode filtering if enabled
            filtered_listings = filter_listings_strict_mode(enriched_listings, strict_mode)
            
            # Update state with listings
            updated_state = update_app_state(state, {
                "listings": filtered_listings,
                "current_listing": None,
                "current_listing_index": None
            })
            
            # Create DataFrame for display
            if filtered_listings:
                df = create_listings_dataframe(filtered_listings, updated_state)
                
                results_msg = create_chat_message_with_metadata(
                    f"🎉 Found {len(filtered_listings)} voucher-friendly listings for you!",
                    "✅ Search Results"
                )
                history.append(results_msg)
                
                return (history, gr.update(value=df, visible=True), 
                       gr.update(value=f"Showing {len(filtered_listings)} listings"), 
                       updated_state)
            else:
                no_safe_msg = create_chat_message_with_metadata(
                    "No safe listings found with current criteria. Try adjusting your filters.",
                    "📋 No Safe Listings"
                )
                history.append(no_safe_msg)
                
                return (history, gr.update(visible=False), 
                       gr.update(value="No listings match criteria"), 
                       updated_state)
                
        except Exception as e:
            error_msg = create_chat_message_with_metadata(
                f"Search failed with error: {str(e)}",
                "❌ Search Error"
            )
            history.append(error_msg)
            return (history, gr.update(), gr.update(value="Search error occurred"), state)

    def handle_general_conversation(message: str, history: list, state: Dict):
        """Handle general conversation using the caseworker agent."""
        try:
            current_language = state.get("preferences", {}).get("language", "en")
            
            # Enhanced message context with comprehensive question type detection
            message_lower = message.lower()
            
            # Detect question type
            is_documentation_request = any(pattern in message_lower for pattern in [
                "where can i find", "how do i find", "where do i find",
                "documentation", "guide", "tutorial", "instructions",
                "forms", "paperwork", "application", "documents",
                "where are the", "where is the", "where are", "where is"
            ])
            
            is_voucher_how_to = any(pattern in message_lower for pattern in [
                "how do i", "how can i", "what do i do", "what's the process",
                "how to use", "how does", "what should i"
            ])
            
            is_voucher_info = any(pattern in message_lower for pattern in [
                "what's the difference", "what does", "can i", "does my voucher",
                "am i eligible", "do i have to", "is it possible",
                "difference between", "vs", "versus", "compared to"
            ])
            
            is_timeline_question = any(pattern in message_lower for pattern in [
                "when do i", "how long does", "why haven't i", "what's the status",
                "when will", "deadline", "extension", "expire", "expiration"
            ])
            
            is_rights_question = any(pattern in message_lower for pattern in [
                "can a landlord", "is it legal", "discrimination", "rights",
                "allowed to", "required to", "refuse", "deny", "reject"
            ])
            
            # Determine question type for context
            if is_documentation_request:
                question_type = "documentation request"
            elif is_voucher_how_to:
                question_type = "voucher usage guidance"
            elif is_timeline_question:
                question_type = "timeline and process question"
            elif is_rights_question:
                question_type = "rights and legal information"
            elif is_voucher_info:
                question_type = "voucher information request"
            else:
                question_type = "general voucher question"
            
            enhanced_message = f"""
User message: {message}

Context: This is a {question_type} from someone seeking information about voucher-friendly housing in NYC.

Key Response Guidelines:
1. If this is a voucher usage question, provide step-by-step guidance
2. If this is about rights/discrimination, include relevant legal information
3. If this is about timelines/deadlines, be specific about processes and requirements
4. If they ask about specific listings without having searched, let them know they need to search first
5. Always be helpful, empathetic, and knowledgeable about housing, NYC neighborhoods, and voucher programs

For voucher questions, include:
- Clear, actionable steps when applicable
- References to relevant agencies or resources
- Common pitfalls to avoid
- Next steps or follow-up actions
            """.strip()
            
            # Add language context to the message
            language_context = f"""
IMPORTANT: The user's preferred language is '{current_language}'. Please respond in this language:
- en = English
- es = Spanish  
- zh = Chinese (Simplified)
- bn = Bengali

User message: {enhanced_message}
            """.strip()
            
            agent_output = caseworker_agent.run(language_context, reset=False)
            response_text = str(agent_output)
            
            # Use appropriate title based on question type
            title_map = {
                "voucher usage guidance": "📋 Voucher Usage Guide",
                "voucher information request": "ℹ️ Voucher Information",
                "timeline and process question": "⏱️ Timeline & Process",
                "rights and legal information": "⚖️ Rights & Legal Info",
                "documentation request": "📚 Documentation Help",
                "general voucher question": "💬 Voucher Assistance"
            }
            
            title = title_map.get(question_type, "💬 General Response")
            
            general_msg = {
                "role": "assistant",
                "content": response_text,
                "metadata": {
                    "title": title,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            history.append(general_msg)
            
            # Preserve existing DataFrame if we have listings
            listings = state.get("listings", [])
            if listings:
                current_df = create_listings_dataframe(listings, state)
                return (history, gr.update(value=current_df, visible=True), 
                       gr.update(value=f"Showing {len(listings)} listings"), state)
            else:
                return (history, gr.update(), gr.update(value="Conversation mode"), state)
            
        except Exception as e:
            error_msg = create_chat_message_with_metadata(
                f"I apologize, but I encountered an error: {str(e)}",
                "❌ Error"
            )
            history.append(error_msg)
            
            # Preserve existing DataFrame even on error
            listings = state.get("listings", [])
            if listings:
                current_df = create_listings_dataframe(listings, state)
                return (history, gr.update(value=current_df, visible=True), 
                       gr.update(value=f"Error occurred - {len(listings)} listings still available"), state)
            else:
                return (history, gr.update(), gr.update(value="Error in conversation"), state)

    def create_listings_dataframe(listings: List[Dict], app_state: Dict = None) -> pd.DataFrame:
        """Create a formatted DataFrame from listings data with shortlist status."""
        df_data = []
        
        # Get shortlisted IDs for quick lookup
        shortlisted_ids = set()
        if app_state:
            shortlisted_ids = get_shortlisted_ids(app_state)
        
        for i, listing in enumerate(listings, 1):  # Start enumeration at 1
            # Get the address from either 'address' or 'title' field
            address = listing.get("address") or listing.get("title", "N/A")
            
            # Get the URL for the listing and create a shorter display version
            url = listing.get("url", "No link available")
            if url != "No link available":
                # Create a shorter display version of the URL with styling
                url_display = f"""
                <div style="text-align: center;">
                    <a href="{url}" 
                       target="_blank" 
                       style="color: #2196F3; 
                              text-decoration: none; 
                              padding: 4px 8px; 
                              border-radius: 4px;
                              transition: all 0.2s ease;
                              display: inline-block;
                              font-weight: 500;"
                       onmouseover="this.style.backgroundColor='#e3f2fd'; this.style.textDecoration='underline';"
                       onmouseout="this.style.backgroundColor='transparent'; this.style.textDecoration='none';">
                        View Listing →
                    </a>
                </div>"""
            else:
                url_display = '<div style="text-align: center; color: #666;">No link</div>'
            
            # Check if listing is shortlisted
            listing_id = str(listing.get("id", address))
            shortlist_status = "★" if listing_id in shortlisted_ids else "+"
            
            # Format the address to be more readable
            formatted_address = address.replace("section-8", "").replace("section 8", "").strip()
            formatted_address = re.sub(r'\s+', ' ', formatted_address)  # Remove extra spaces
            
            df_data.append({
                "#": i,  # Add the listing number
                "Address": formatted_address,
                "Price": listing.get("price", "N/A"),
                "Risk Level": listing.get("risk_level", "❓"),
                "Violations": listing.get("building_violations", 0),
                "Last Inspection": listing.get("last_inspection", "N/A"),
                "Link": url_display,  # Use the HTML anchor tag version
                "Summary": listing.get("violation_summary", "")[:50] + "..." if len(listing.get("violation_summary", "")) > 50 else listing.get("violation_summary", ""),
                "Shortlist": shortlist_status
            })
        
        return pd.DataFrame(df_data)

    # Wire up the submit action with state management
    send_btn.click(
        handle_chat_message, 
        [msg, chatbot, app_state, visible_strict_mode_checkbox], 
        [chatbot, results_df, progress_info, app_state]
    )
    # Add a secondary submit to clear the input box for better UX
    send_btn.click(lambda: "", [], [msg])
    
    # Wire up Enter key submission
    msg.submit(
        handle_chat_message, 
        [msg, chatbot, app_state, visible_strict_mode_checkbox], 
        [chatbot, results_df, progress_info, app_state]
    )
    msg.submit(lambda: "", [], [msg])
    
    # Wire up DataFrame shortlist click handler
    results_df.select(
        handle_shortlist_click,
        [app_state],
        [results_df, progress_info, shortlist_display, app_state]
    )
    
    # Language change handler
    def change_language(language, current_state, current_history):
        """Handle language change with greeting update."""
        # Update the language in state
        new_state = update_app_state(current_state, {
            "preferences": {"language": language}
        })
        
        # Create new greeting in the selected language
        new_greeting = create_initial_greeting(language)
        
        # Replace the first message (greeting) if it exists, otherwise add it
        if current_history and len(current_history) > 0 and current_history[0]["role"] == "assistant":
            updated_history = [new_greeting[0]] + current_history[1:]
        else:
            updated_history = new_greeting + current_history
        
        return updated_history, new_state
    
    # Language change event
    language_dropdown.change(
        change_language,
        [language_dropdown, app_state, chatbot],
        [chatbot, app_state]
    )
    
    # Dark mode toggle using the correct JavaScript approach
    dark_mode_toggle.click(
        fn=None,
        js="""
        () => {
            document.body.classList.toggle('dark');
        }
        """
    )
    
if __name__ == "__main__":
    demo.launch(i18n=i18n) 