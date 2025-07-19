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
        "link_not_available": "No link available",
        "intro_greeting": """👋 **Hi there! I'm Navi, your personal NYC Housing Navigator!**

I'm here to help you find safe, affordable, and voucher-friendly housing in New York City. I understand that finding the right home can feel overwhelming, but you don't have to do this alone - I'm here to guide you every step of the way! 😊

**Here's how I can help you:**
• 🏠 **Find voucher-friendly apartments** that accept your specific voucher type
• 🏢 **Check building safety** and provide violation reports for peace of mind  
• 🚇 **Show nearby subway stations** and transit accessibility
• 🏫 **Find nearby schools** for families with children
• 📧 **Draft professional emails** to landlords and property managers
• 💡 **Answer questions** about voucher programs, neighborhoods, and housing rights

**To get started, just tell me:**
• What type of voucher do you have? (Section 8, CityFHEPS, HASA, etc.)
• How many bedrooms do you need? 🛏️
• What's your maximum rent budget? 💰
• Do you have a preferred borough? 🗽

I'm patient, kind, and here to support you through this journey. Let's find you a wonderful place to call home! ✨🏡"""
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
        "link_not_available": "Sin enlace disponible",
        "intro_greeting": """👋 **¡Hola! Soy Navi, tu Navegadora Personal de Vivienda de NYC!**

Estoy aquí para ayudarte a encontrar vivienda segura, asequible y que acepta vouchers en la Ciudad de Nueva York. Entiendo que encontrar el hogar perfecto puede sentirse abrumador, pero no tienes que hacerlo solo - ¡estoy aquí para guiarte en cada paso del camino! 😊

**Así es como puedo ayudarte:**
• 🏠 **Encontrar apartamentos que aceptan vouchers** que acepten tu tipo específico de voucher
• 🏢 **Verificar la seguridad del edificio** y proporcionar reportes de violaciones para tu tranquilidad
• 🚇 **Mostrar estaciones de metro cercanas** y accesibilidad de transporte
• 🏫 **Encontrar escuelas cercanas** para familias con niños
• 📧 **Redactar emails profesionales** a propietarios y administradores de propiedades
• 💡 **Responder preguntas** sobre programas de vouchers, vecindarios y derechos de vivienda

**Para comenzar, solo dime:**
• ¿Qué tipo de voucher tienes? (Section 8, CityFHEPS, HASA, etc.)
• ¿Cuántas habitaciones necesitas? 🛏️
• ¿Cuál es tu presupuesto máximo de renta? 💰
• ¿Tienes un distrito preferido? 🗽

Soy paciente, amable y estoy aquí para apoyarte en este viaje. ¡Encontremos un lugar maravilloso al que puedas llamar hogar! ✨🏡"""
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
        "link_not_available": "无可用链接",
        "intro_greeting": """👋 **您好！我是Navi，您的个人纽约市住房导航员！**

我在这里帮助您在纽约市找到安全、经济实惠且接受住房券的住房。我理解找到合适的家可能让人感到不知所措，但您不必独自面对这一切 - 我会在每一步中指导您！😊

**我可以为您提供以下帮助：**
• 🏠 **寻找接受住房券的公寓** - 找到接受您特定类型住房券的房源
• 🏢 **检查建筑安全** - 提供违规报告和安全评估，让您安心
• 🚇 **显示附近的地铁站** - 提供交通便利性和可达性信息
• 🏫 **寻找附近的学校** - 为有孩子的家庭提供学校信息
• 📧 **起草专业邮件** - 帮您给房东和物业管理员写邮件
• 💡 **回答问题** - 关于住房券项目、社区特点和住房权利的各种问题

**开始使用时，请告诉我：**
• 您有什么类型的住房券？(Section 8联邦住房券、CityFHEPS城市住房援助、HASA艾滋病服务券等)
• 您需要多少间卧室？🛏️
• 您的最高租金预算是多少？💰
• 您有首选的行政区吗？(布朗克斯、布鲁克林、曼哈顿、皇后区、史坦顿岛) 🗽

我很有耐心、善良，会在整个找房过程中支持您。让我们一起为您找到一个可以称之为家的美好地方！我了解纽约市的住房市场和各种住房券项目，会帮您找到既安全又符合预算的理想住所。✨🏡"""
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
        "link_not_available": "কোন লিংক উপলব্ধ নেই",
        "intro_greeting": """👋 **নমস্কার! আমি নবি, আপনার ব্যক্তিগত NYC হাউজিং নেভিগেটর!**

আমি এখানে আছি নিউইয়র্ক সিটিতে আপনাকে নিরাপদ, সাশ্রয়ী এবং ভাউচার-বান্ধব আবাসন খুঁজে পেতে সাহায্য করার জন্য। আমি বুঝি যে সঠিক বাড়ি খোঁজা অভিভূতকর মনে হতে পারে, কিন্তু আপনাকে একা এটি করতে হবে না - আমি প্রতিটি পদক্ষেপে আপনাকে গাইড করার জন্য এখানে আছি! 😊

**আমি যেভাবে আপনাকে সাহায্য করতে পারি:**
• 🏠 **ভাউচার-বান্ধব অ্যাপার্টমেন্ট খুঁজুন** যা আপনার নির্দিষ্ট ভাউচার ধরন গ্রহণ করে
• 🏢 **বিল্ডিং নিরাপত্তা পরীক্ষা করুন** এবং মানসিক শান্তির জন্য লঙ্ঘনের রিপোর্ট প্রদান করুন
• 🚇 **নিকটবর্তী সাবওয়ে স্টেশন দেখান** এবং ট্রানজিট অ্যাক্সেসিবলিটি
• 🏫 **নিকটবর্তী স্কুল খুঁজুন** শিশুদের সাথে পরিবারের জন্য
• 📧 **পেশাদার ইমেইল খসড়া করুন** বাড়িওয়ালা এবং সম্পত্তি ব্যবস্থাপকদের কাছে
• 💡 **প্রশ্নের উত্তর দিন** ভাউচার প্রোগ্রাম, পাড়া এবং আবাসন অধিকার সম্পর্কে

**শুরু করতে, শুধু আমাকে বলুন:**
• আপনার কি ধরনের ভাউচার আছে? (Section 8, CityFHEPS, HASA, ইত্যাদি)
• আপনার কতটি বেডরুম প্রয়োজন? 🛏️
• আপনার সর্বোচ্চ ভাড়ার বাজেট কত? 💰
• আপনার কি কোন পছন্দের বরো আছে? 🗽

আমি ধৈর্যশীল, দয়ালু, এবং এই যাত্রায় আপনাকে সমর্থন করার জন্য এখানে আছি। আসুন আপনার জন্য একটি চমৎকার জায়গা খুঁজে পাই যাকে আপনি বাড়ি বলতে পারেন! ✨🏡"""
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
        "favorites": []
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
        r'nearest\s+(subway|train|school)', # "nearest subway", "nearest school", "nearest train"
        r'closest\s+(subway|train|school)', # "closest subway", "closest school", "closest train"
        r'what\'?s\s+the\s+(nearest|closest)\s+(subway|train|school)', # "what's the nearest/closest subway"
        r'where\s+is\s+the\s+(nearest|closest)\s+(subway|train|school)', # "where is the nearest/closest subway"
        r'how\s+far\s+is\s+the\s+(subway|train|school)', # "how far is the subway"
        r'(subway|train|school)\s+(distance|proximity)', # "subway distance", "school proximity"
        r'^(subway|train|school)\?$',      # just "subway?", "school?"
        r'^closest\s+(subway|train|school)\?$', # "closest subway?", "closest school?"
    ]
    
    # Check if message matches context-dependent patterns
    import re
    for pattern in context_patterns:
        if re.match(pattern, message_lower):
            return True
    
    # Also check for very short questions (likely context-dependent)
    words = message_lower.split()
    if len(words) <= 3 and any(word in ['which', 'what', 'how', 'where', 'lines', 'train', 'subway'] for word in words):
        return True
    
    return False

def detect_language_from_message(message: str) -> str:
    """Detect language from user message using simple keyword matching."""
    message_lower = message.lower()
    
    # Spanish keywords
    spanish_keywords = [
        'hola', 'apartamento', 'vivienda', 'casa', 'alquiler', 'renta', 'busco', 
        'necesito', 'ayuda', 'donde', 'como', 'que', 'soy', 'tengo', 'quiero',
        'habitacion', 'habitaciones', 'dormitorio', 'precio', 'costo', 'dinero',
        'section', 'cityFHEPS', 'voucher', 'bronx', 'brooklyn', 'manhattan',
        'queens', 'gracias', 'por favor', 'dime', 'dame', 'encuentro'
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
    if spanish_count >= 2:
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
with gr.Blocks(theme=theme) as demo:
    gr.Markdown(f"# {i18n('app_title')}")
    gr.Markdown(i18n("app_subtitle"))
    
    # Initialize app state
    app_state = gr.State(create_initial_state())
    
    # Controls at the top: Language selector and Dark/Light mode toggle
    with gr.Row():
        language_dropdown = gr.Dropdown(
            label=i18n("language_selector"),
            choices=[("English", "en"), ("Español", "es"), ("中文", "zh"), ("বাংলা", "bn")],
            value="en",
            allow_custom_value=False,
            scale=2
        )
        dark_mode_toggle = gr.Checkbox(
            label="🌙 Dark Mode",
            value=False,
            scale=1
        )
    
    # Create initial greeting message for Navi
    def create_initial_greeting(language="en"):
        greeting_message = {
            "role": "assistant",
            "content": i18n_dict[language]["intro_greeting"]
        }
        return [greeting_message]
    
    # Chat Section (Full Width) - Initialize with greeting
    chatbot = gr.Chatbot(
        label=i18n("conversation_label"),
        height=600,
        type="messages",
        value=create_initial_greeting()  # Add initial greeting
    )
    msg = gr.Textbox(
        label=i18n("message_label"), 
        placeholder=i18n("message_placeholder")
    )

    # Preferences and Status Row (Compact)
    with gr.Row():
        with gr.Column(scale=2):
            with gr.Group():
                gr.Markdown(f"### {i18n('preferences_title')}")
                strict_mode_toggle = gr.Checkbox(
                    label=i18n("strict_mode_label"),
                    value=False
                )
        with gr.Column(scale=3):
            progress_info = gr.Textbox(
                label=i18n("status_label"),
                value=i18n("status_ready"),
                interactive=False,
                visible=True
            )
    
    # Results Display (Full Width)
    results_df = gr.DataFrame(
        value=pd.DataFrame(),
        label=i18n("listings_label"),
        interactive=False,
        row_count=(10, "dynamic"),
        wrap=True,
        visible=False,
        datatype=["number", "str", "str", "str", "number", "str", "str", "str"]  # #, Address, Price, Risk, Violations, Inspection, Link, Summary
    )

    # Using V0's enhanced classification - now imported from email_handler.py
    
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
        if "first" in message_lower or "1st" in message_lower or "#1" in message_lower:
            listing_index = 0
        elif "second" in message_lower or "2nd" in message_lower or "#2" in message_lower:
            listing_index = 1
        elif "third" in message_lower or "3rd" in message_lower or "#3" in message_lower:
            listing_index = 2
        elif "last" in message_lower:
            listing_index = len(listings) - 1
        else:
            # Try to extract number
            numbers = re.findall(r'\d+', message_lower)
            if numbers:
                try:
                    listing_index = int(numbers[0]) - 1  # Convert to 0-based index
                except:
                    pass
        
        # Default to first listing if no specific index found
        if listing_index is None:
            listing_index = 0
        
        # Validate index
        if listing_index < 0 or listing_index >= len(listings):
            invalid_msg = create_chat_message_with_metadata(
                f"I only have {len(listings)} listings available. Please ask about a listing number between 1 and {len(listings)}.",
                "❌ Invalid Listing Number"
            )
            history.append(invalid_msg)
            # Preserve the current DataFrame
            current_df = create_listings_dataframe(listings)
            return (history, gr.update(value=current_df, visible=True), 
                   gr.update(value=f"Showing {len(listings)} listings"), state)
        
        # Get the requested listing
        listing = listings[listing_index]
        listing_num = listing_index + 1
        
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
        
        # Update state to track current listing context
        updated_state = update_app_state(state, {
            "current_listing": listing,
            "current_listing_index": listing_index
        })
        
        # Preserve the current DataFrame
        current_df = create_listings_dataframe(listings)
        return (history, gr.update(value=current_df, visible=True), 
               gr.update(value=f"Showing {len(listings)} listings"), updated_state)

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
        
        # If language changed, update the greeting message
        if language_changed and len(history) > 1:  # Don't replace if this is the first user message
            # Find and replace the greeting (first assistant message)
            for i, msg in enumerate(history):
                if msg["role"] == "assistant" and "I'm Navi" in msg["content"] or "Soy Navi" in msg["content"] or "我是Navi" in msg["content"] or "আমি নবি" in msg["content"]:
                    # Replace with new language greeting
                    new_greeting = create_initial_greeting(current_language)
                    history[i] = new_greeting[0]
                    break
        
        try:
            # Use V0's enhanced classification
            message_type = enhanced_classify_message(message, new_state)
            
            if message_type == "email_request":
                # Call V0's enhanced email handler
                enhanced_result = enhanced_handle_email_request(message, history, new_state)
                # Return with state preservation
                return (enhanced_result[0], enhanced_result[1], 
                       gr.update(value="Email template generated"), new_state)
            elif message_type == "what_if_scenario":
                print(f"🔄 CALLING handle_what_if_scenario")
                return handle_what_if_scenario(message, history, new_state, strict_mode)
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
        
        # Debug logging to see what's happening
        log_tool_action("GradioApp", "borough_detection", {
            "message": message,
            "detected_borough": detected_borough,
            "final_target_borough": target_borough
        })
        
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
            log_tool_action("GradioApp", "browser_search_started", {
                "borough": target_borough,
                "detected_from_message": detected_borough,
                "message": message
            })
            
            search_query = "Section 8"
            
            # Debug: Log exactly what we're passing to browser agent
            boroughs_param = target_borough if target_borough else ""
            print(f"📡 Calling browser_agent.forward with boroughs='{boroughs_param}'")
            
            log_tool_action("GradioApp", "browser_agent_call", {
                "query": search_query,
                "boroughs_param": boroughs_param,
                "target_borough": target_borough,
                "detected_borough": detected_borough
            })
            
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
            
            # Stage 2: Checking Violations
            violation_msg = create_chat_message_with_metadata(
                f"🏢 Checking building safety for {len(listings)} listings...",
                "🏢 Checking Violations",
                parent_id=search_id
            )
            history.append(violation_msg)
            
            # Enrich listings with violation data
            enriched_listings = []
            for i, listing in enumerate(listings):
                address = listing.get("address") or listing.get("title", "")
                if not address:
                    continue
                
                violation_result = violation_agent.forward(address)
                violation_data = json.loads(violation_result)
                
                if violation_data.get("status") == "success":
                    enriched_listing = {
                        **listing,
                        "building_violations": violation_data["data"]["violations"],
                        "risk_level": violation_data["data"]["risk_level"],
                        "last_inspection": violation_data["data"]["last_inspection"],
                        "violation_summary": violation_data["data"]["summary"]
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
            
            # Stage 3: Apply strict mode filtering
            if strict_mode:
                filtered_listings = filter_listings_strict_mode(enriched_listings, strict=True)
                filter_msg = create_chat_message_with_metadata(
                    f"✅ Applied strict mode filter - {len(filtered_listings)} safe listings found",
                    "✅ Strict Mode Applied"
                )
                history.append(filter_msg)
            else:
                filtered_listings = enriched_listings
            
            # Update state with listings and clear current listing context (new search)
            updated_state = update_app_state(state, {
                "listings": filtered_listings,
                "current_listing": None,
                "current_listing_index": None
            })
            
            # Create DataFrame for display
            if filtered_listings:
                df = create_listings_dataframe(filtered_listings)
                
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

    def handle_what_if_scenario(message: str, history: list, state: Dict, strict_mode: bool):
        """Handle what-if scenarios where users want to modify search parameters"""
        try:
            from what_if_handler import process_what_if_scenario
            
            # Process the what-if scenario
            updated_history, updated_state = process_what_if_scenario(message, history, state)
            
            # If changes were applied, execute a new search with the modified parameters
            if "last_what_if_changes" in updated_state:
                new_prefs = updated_state["preferences"]
                target_borough = new_prefs.get("borough", "")
                
                # Create a search message that includes the borough for detection
                search_message = f"Search with modified parameters: {updated_state['last_what_if_changes']}"
                if target_borough:
                    search_message += f" in {target_borough}"
                
                # Execute search with modified parameters
                return handle_housing_search(
                    search_message, 
                    updated_history, 
                    updated_state, 
                    strict_mode
                )
            
            # If no changes were made, just return the updated history
            listings = updated_state.get("listings", [])
            if listings:
                current_df = create_listings_dataframe(listings)
                return (updated_history, gr.update(value=current_df, visible=True), 
                       gr.update(value=f"Showing {len(listings)} listings"), updated_state)
            else:
                return (updated_history, gr.update(), gr.update(value="What-if analysis complete"), updated_state)
                
        except Exception as e:
            log_tool_action("GradioApp", "what_if_error", {
                "error": str(e),
                "message": message
            })
            
            error_msg = create_chat_message_with_metadata(
                f"What-if scenario error: {str(e)}",
                "❌ What-if Error"
            )
            history.append(error_msg)
            
            # Preserve existing state
            listings = state.get("listings", [])
            if listings:
                current_df = create_listings_dataframe(listings)
                return (history, gr.update(value=current_df, visible=True), 
                       gr.update(value=f"Error occurred - {len(listings)} listings available"), state)
            else:
                return (history, gr.update(), gr.update(value="Error processing what-if scenario"), state)

    def handle_listing_follow_up(message: str, history: list, state: Dict):
        """Handle specific follow-up actions for the current listing using enriched data."""
        current_listing = state.get("current_listing")
        current_listing_index = state.get("current_listing_index")
        
        if not current_listing:
            # No current listing context - pass to general conversation
            return None
        
        message_lower = message.lower().strip()
        listing_num = (current_listing_index or 0) + 1
        address = current_listing.get("address") or current_listing.get("title", "N/A")
        
        # Check for subway/transit request
        subway_patterns = [
            r'subway', r'transit', r'train', r'nearest.*subway', r'closest.*subway',
            r'see.*subway', r'show.*subway', r'subway.*options', r'transit.*options'
        ]
        
        # Check for school request  
        school_patterns = [
            r'school', r'nearest.*school', r'closest.*school', r'see.*school',
            r'show.*school', r'school.*nearby', r'nearby.*school'
        ]
        
        # Check for another listing request
        another_listing_patterns = [
            r'another.*listing', r'different.*listing', r'next.*listing', r'other.*listing',
            r'view.*another', r'see.*another', r'show.*another', r'view.*different'
        ]
        
        import re
        
        # Handle subway/transit request
        if any(re.search(pattern, message_lower) for pattern in subway_patterns):
            return handle_subway_info_request(current_listing, listing_num, history, state)
        
        # Handle school request
        elif any(re.search(pattern, message_lower) for pattern in school_patterns):
            return handle_school_info_request(current_listing, listing_num, history, state)
        
        # Handle another listing request
        elif any(re.search(pattern, message_lower) for pattern in another_listing_patterns):
            return handle_another_listing_request(history, state)
        
        # If no specific follow-up detected, return None to pass to general conversation
        return None

    def handle_subway_info_request(listing: Dict, listing_num: int, history: list, state: Dict):
        """Handle subway/transit information request for current listing."""
        address = listing.get("address") or listing.get("title", "N/A")
        
        # Check if we have enriched subway data
        subway_access = listing.get("subway_access")
        if subway_access and subway_access.get("nearest_station"):
            station_name = subway_access.get("nearest_station", "Unknown")
            lines = subway_access.get("subway_lines", "N/A")
            distance = subway_access.get("distance_miles", 0)
            is_accessible = subway_access.get("is_accessible", False)
            entrance_type = subway_access.get("entrance_type", "Unknown")
            
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
            # No enriched data available - provide helpful message
            response_text = f"""
🚇 **Subway Information for Listing #{listing_num}:**

I don't have detailed subway information for this specific listing yet. However, I can help you find this information! 

**Address:** {address}

You can:
- Check the MTA website or app for nearby stations
- Use Google Maps to find transit options
- Ask me to search for subway information using the address

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
        current_df = create_listings_dataframe(listings)
        return (history, gr.update(value=current_df, visible=True), 
               gr.update(value=f"Showing {len(listings)} listings"), state)

    def handle_school_info_request(listing: Dict, listing_num: int, history: list, state: Dict):
        """Handle school information request for current listing."""
        address = listing.get("address") or listing.get("title", "N/A")
        
        # Check if we have enriched school data
        school_access = listing.get("school_access")
        if school_access and school_access.get("nearby_schools"):
            schools = school_access.get("nearby_schools", [])
            
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
🏫 **Schools Information for Listing #{listing_num}:**

No school data is currently available for this listing.

**Address:** {address}

You can research schools in the area using:
- NYC School Finder website
- GreatSchools.org
- Local Department of Education resources

Would you like to:
1. 🚇 See the nearest subway/transit options?
2. 📧 Draft an email to inquire about this listing?
3. 🏠 View another listing?
                """.strip()
        else:
            # No enriched data available
            response_text = f"""
🏫 **Schools Information for Listing #{listing_num}:**

I don't have detailed school information for this specific listing yet.

**Address:** {address}

You can research schools in the area using:
- NYC School Finder website  
- GreatSchools.org
- Local Department of Education resources

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
        current_df = create_listings_dataframe(listings)
        return (history, gr.update(value=current_df, visible=True), 
               gr.update(value=f"Showing {len(listings)} listings"), state)

    def handle_another_listing_request(history: list, state: Dict):
        """Handle request to view another listing."""
        listings = state.get("listings", [])
        current_listing_index = state.get("current_listing_index", 0)
        
        if not listings:
            no_listings_msg = create_chat_message_with_metadata(
                "I don't have any other listings to show you. Please search for apartments first!",
                "📋 No Listings Available"
            )
            history.append(no_listings_msg)
            return (history, gr.update(), gr.update(value="No listings available"), state)
        
        if len(listings) == 1:
            only_one_msg = create_chat_message_with_metadata(
                "I only have one listing available right now. Try searching for more apartments to see additional options!",
                "📋 Only One Listing"
            )
            history.append(only_one_msg)
            current_df = create_listings_dataframe(listings)
            return (history, gr.update(value=current_df, visible=True), 
                   gr.update(value=f"Showing {len(listings)} listings"), state)
        
        # Show next listing (cycle through)
        next_index = (current_listing_index + 1) % len(listings)
        next_listing = listings[next_index]
        next_listing_num = next_index + 1
        
        # Create response for next listing
        address = next_listing.get("address") or next_listing.get("title", "N/A")
        price = next_listing.get("price", "N/A")
        url = next_listing.get("url", "No link available")
        risk_level = next_listing.get("risk_level", "❓")
        violations = next_listing.get("building_violations", 0)
        
        response_text = f"""
**Listing #{next_listing_num} Details:**

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
        
        next_listing_msg = create_chat_message_with_metadata(
            response_text,
            f"🏠 Listing #{next_listing_num} Details"
        )
        history.append(next_listing_msg)
        
        # Update state to track new current listing
        updated_state = update_app_state(state, {
            "current_listing": next_listing,
            "current_listing_index": next_index
        })
        
        # Preserve existing DataFrame
        current_df = create_listings_dataframe(listings)
        return (history, gr.update(value=current_df, visible=True), 
               gr.update(value=f"Showing {len(listings)} listings"), updated_state)

    def handle_general_conversation(message: str, history: list, state: Dict):
        """Handle general conversation using the caseworker agent with listing context."""
        try:
            # First check if this is a specific follow-up action we can handle directly
            follow_up_result = handle_listing_follow_up(message, history, state)
            if follow_up_result:
                return follow_up_result
            
            # Get the current language from state
            current_language = state.get("preferences", {}).get("language", "en")
            
            # Check if this is a context-dependent question and we have a current listing
            is_context_dependent = detect_context_dependent_question(message)
            current_listing = state.get("current_listing")
            current_listing_index = state.get("current_listing_index")
            
            # Enhance the message with context if needed
            enhanced_message = message
            if is_context_dependent and current_listing:
                listing_num = (current_listing_index or 0) + 1
                address = current_listing.get("address") or current_listing.get("title", "N/A")
                
                # Add context to the message for the agent
                enhanced_message = f"""
User is asking about Listing #{listing_num}: {address}

Current listing details:
- Address: {address}
- Price: {current_listing.get("price", "N/A")}
- Violations: {current_listing.get("building_violations", 0)}
- Risk Level: {current_listing.get("risk_level", "❓")}

User's question: {message}

Please answer their question specifically about this listing. If they're asking about subway lines or transit, use the geocoding and subway tools to get specific information about this address.
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
            
            general_msg = create_chat_message_with_metadata(
                response_text,
                "💬 General Response"
            )
            history.append(general_msg)
            
            # Preserve existing DataFrame if we have listings
            listings = state.get("listings", [])
            if listings:
                current_df = create_listings_dataframe(listings)
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
                current_df = create_listings_dataframe(listings)
                return (history, gr.update(value=current_df, visible=True), 
                       gr.update(value=f"Error occurred - {len(listings)} listings still available"), state)
            else:
                return (history, gr.update(), gr.update(value="Error in conversation"), state)

    def create_listings_dataframe(listings: List[Dict]) -> pd.DataFrame:
        """Create a formatted DataFrame from listings data."""
        df_data = []
        
        for i, listing in enumerate(listings, 1):  # Start enumeration at 1
            # Get the address from either 'address' or 'title' field
            address = listing.get("address") or listing.get("title", "N/A")
            
            # Get the URL for the listing
            url = listing.get("url", "No link available")
            
            df_data.append({
                "#": i,  # Add the listing number
                "Address": address,
                "Price": listing.get("price", "N/A"),
                "Risk Level": listing.get("risk_level", "❓"),
                "Violations": listing.get("building_violations", 0),
                "Last Inspection": listing.get("last_inspection", "N/A"),
                "Link": url,
                "Summary": listing.get("violation_summary", "")[:50] + "..." if len(listing.get("violation_summary", "")) > 50 else listing.get("violation_summary", "")
            })
        
        return pd.DataFrame(df_data)

    # Wire up the submit action with state management
    msg.submit(
        handle_chat_message, 
        [msg, chatbot, app_state, strict_mode_toggle], 
        [chatbot, results_df, progress_info, app_state]
    )
    # Add a secondary submit to clear the input box for better UX
    msg.submit(lambda: "", [], [msg])
    
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
    
    # Update preferences when controls change
    def update_preferences(strict, current_state):
        """Update preferences in state when UI controls change."""
        return update_app_state(current_state, {
            "preferences": {
                "strict_mode": strict
            }
        })
    
    strict_mode_toggle.change(
        update_preferences,
        [strict_mode_toggle, app_state],
        [app_state]
    )
    
    # Language change event
    language_dropdown.change(
        change_language,
        [language_dropdown, app_state, chatbot],
        [chatbot, app_state]
    )
    
    # Dark mode toggle functionality
    def toggle_dark_mode(is_dark_mode):
        """Toggle between dark and light mode"""
        if is_dark_mode:
            return gr.HTML("""
                <script>
                document.body.classList.add('dark');
                document.documentElement.classList.add('dark');
                </script>
            """)
        else:
            return gr.HTML("""
                <script>
                document.body.classList.remove('dark');
                document.documentElement.classList.remove('dark');
                </script>
            """)
    
    # Hidden HTML component for dark mode script injection
    dark_mode_script = gr.HTML(visible=False)
    
    dark_mode_toggle.change(
        toggle_dark_mode,
        [dark_mode_toggle],
        [dark_mode_script]
    )
    
if __name__ == "__main__":
    demo.launch(i18n=i18n) 