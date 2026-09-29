"""
Contexto: AI-Powered Spanish Learning for Expats in Querétaro
Phase 2: Production RAG Architecture
- All content loaded from JSON files
- Backend-only Groq control (environment variable)
- No UI toggle for AI feature
- Clean, maintainable codebase (~500 lines)
"""

import streamlit as st
import json
import os
from groq import Groq
from gtts import gTTS
import io
import pandas as pd

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

st.set_page_config(
    page_title="Contexto - Spanish Learning for Expats",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# AUDIO GENERATION
# ============================================================================

def create_audio(text, lang='es'):
    """Generate audio from text using gTTS"""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        st.warning(f"Audio generation failed: {str(e)[:50]}")
        return None

# ============================================================================
# GROQ SETUP (Backend Control Only)
# ============================================================================

# Check if Groq is enabled via environment variable (admin control)
ENABLE_AI_VOCAB = os.getenv("ENABLE_AI_VOCAB", "false").lower() == "true"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
has_groq = (GROQ_API_KEY is not None) and ENABLE_AI_VOCAB

if has_groq:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception:
        has_groq = False

# ============================================================================
# JSON DATA LOADING (RAG Layer)
# ============================================================================

@st.cache_resource
def load_all_data():
    """Load all content from JSON files (cached for performance)"""
    data = {
        "vocabulary": {},
        "grammar": {},
        "content": {}
    }
    
    # Load vocabulary files
    vocab_files = {
        "market": "vocab_json/market_vocab.json",
        "hospital": "vocab_json/hospital_vocab.json",
        "papeleria": "vocab_json/papeleria_vocab.json",
        "school": "vocab_json/school_context_vocab.json",
        "expanded": "vocab_json/expanded_vocab.json"
    }
    
    for lesson_name, filepath in vocab_files.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data["vocabulary"][lesson_name] = json.load(f)
        except FileNotFoundError:
            st.warning(f"⚠️ {filepath} not found")
        except json.JSONDecodeError:
            st.warning(f"⚠️ {filepath} has invalid JSON")
    
    # Load grammar content files
    content_files = {
        "grammar_verbs": "content_json/grammar_verbs.json",
        "pronouns": "content_json/pronouns.json",
        "conversations": "content_json/conversations.json",
        "references": "content_json/references.json",
        "phrases": "content_json/phrases.json"
    }
    
    for content_type, filepath in content_files.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data["content"][content_type] = json.load(f)
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass
    
    return data

all_data = load_all_data()

# ============================================================================
# SEARCH & RETRIEVAL FUNCTIONS
# ============================================================================

def sanitize_input(text):
    """Prevent injection attacks"""
    if not text:
        return ""
    if len(text) > 500:
        return text[:500]
    text = text.replace("<", "").replace(">", "").replace("&", "")
    return text.strip()

def search_vocabulary(query, lesson=None):
    """Search vocabulary across all lessons"""
    query = sanitize_input(query).lower()
    if not query:
        return []
    
    results = []
    vocab_data = all_data["vocabulary"]
    
    lessons_to_search = [lesson] if lesson else vocab_data.keys()
    
    for lesson_name in lessons_to_search:
        if lesson_name not in vocab_data:
            continue
        
        lesson_data = vocab_data[lesson_name]
        if "vocabulary" not in lesson_data:
            continue
        
        for item in lesson_data["vocabulary"]:
            if (query in item.get("spanish", "").lower() or 
                query in item.get("english", "").lower()):
                results.append({
                    "lesson": lesson_name,
                    "spanish": item.get("spanish", ""),
                    "english": item.get("english", ""),
                    "pronunciation": item.get("pronunciation", "N/A"),
                    "example_spanish": item.get("example_spanish", ""),
                    "example_english": item.get("example_english", "")
                })
    
    return results

# ============================================================================
# AI VOCABULARY (Groq) - Backend Control Only
# ============================================================================

def get_ai_vocab_response(query, lesson=""):
    """Generate translation + explanation using Groq (only if enabled)"""
    if not has_groq:
        return {"error": "AI vocabulary disabled"}
    
    try:
        # CALL 1: Translation
        is_spanish = any(ord(c) > 127 for c in query)
        if is_spanish:
            trans_prompt = f"What is the English translation of: {query}"
        else:
            trans_prompt = f"What is the Spanish translation of: {query}"
        
        response_trans = client.messages.create(
            model="mixtral-8x7b-32768",
            max_tokens=30,
            temperature=0.1,
            messages=[{"role": "user", "content": trans_prompt}]
        )
        translation = response_trans.content[0].text.strip().split('\n')[0] if response_trans.content else "N/A"
        
        # CALL 2: Spanish Explanation
        exp_prompt = f"Explain '{query}' in Spanish. 2-3 sentences, simple and clear."
        response_exp = client.messages.create(
            model="mixtral-8x7b-32768",
            max_tokens=100,
            temperature=0.3,
            messages=[{"role": "user", "content": exp_prompt}]
        )
        explanation = response_exp.content[0].text.strip() if response_exp.content else "N/A"
        
        return {
            "query": query,
            "is_spanish": is_spanish,
            "translation": translation,
            "explanation": explanation,
            "error": None
        }
    except Exception as e:
        return {"error": f"API Error: {str(e)[:50]}"}

# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_vocabulary_entry(item):
    """Display single vocabulary item with audio"""
    with st.expander(f"**{item['spanish']}** - {item['english']}"):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("🇪🇸 Spanish")
            st.write(f"**{item['spanish']}**")
            st.caption(f"*{item['pronunciation']}*")
            audio_es = create_audio(item['spanish'], lang='es')
            if audio_es:
                st.audio(audio_es, format='audio/mp3')
        
        with col2:
            st.markdown("🇬🇧 English")
            st.write(f"**{item['english']}**")
        
        if item.get('example_spanish'):
            st.divider()
            st.markdown("**Example:**")
            st.write(f"🇪🇸 {item['example_spanish']}")
            audio_ex = create_audio(item['example_spanish'], lang='es')
            if audio_ex:
                st.audio(audio_ex, format='audio/mp3')
            st.write(f"🇬🇧 {item['example_english']}")

def display_ai_vocab(result):
    """Display AI-generated vocabulary response"""
    if result.get("error"):
        st.error(f"❌ {result['error']}")
        return
    
    st.success("✅ AI Response")
    st.markdown("### 📚 Spanish Explanation:")
    st.markdown(f"> {result['explanation']}")
    
    st.markdown("### 🔄 Translation:")
    st.write(f"**{result['translation']}**")

def display_verb_conjugation(verb_data):
    """Display verb conjugation with examples"""
    verb = verb_data["infinitive"]
    english = verb_data["english"]
    
    st.subheader(f"{verb} ({english})")
    
    conjugations = verb_data["conjugations"]
    people = [("yo", "I"), ("tú", "You (singular)"), 
              ("él_ella_usted", "He/She/You (formal)"),
              ("nosotros", "We"), ("ustedes_ellos_ellas", "You all/They")]
    
    for key, label in people:
        if key in conjugations.get("present", {}):
            present = conjugations["present"][key]
            preterite = conjugations["preterite"].get(key, {})
            future = conjugations["future"].get(key, {})
            
            with st.expander(f"**{label}** → {present['form']} (present)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Present:** " + present['form'])
                    st.caption(present['example'])
                    audio = create_audio(present['example'], lang='es')
                    if audio:
                        st.audio(audio, format='audio/mp3')
                
                with col2:
                    st.write("**Past:** " + preterite.get('form', 'N/A'))
                    st.caption(preterite.get('example', 'N/A'))
                    if preterite.get('example'):
                        audio = create_audio(preterite['example'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                
                st.write("**Future:** " + future.get('form', 'N/A'))
                st.caption(future.get('example', 'N/A'))
                if future.get('example'):
                    audio = create_audio(future['example'], lang='es')
                    if audio:
                        st.audio(audio, format='audio/mp3')

# ============================================================================
# MAIN APP - 11 TABS
# ============================================================================

st.title("🌍 Contexto: Spanish Learning for Expats in Querétaro")
st.markdown("Real Spanish for real situations. Built by expats, for expats.")

tabs = st.tabs([
    "💬 Conversations",
    "📚 Grammar",
    "🏪 Market (Mercado)",
    "🏥 Hospital",
    "📝 Paper Store (Papelería)",
    "🎓 School (Escuela)",
    "📐 Measurements",
    "⏰ Time",
    "🔢 Numbers",
    "💰 Money",
    "🚗 Transportation"
])

# ============================================================================
# TAB 1: CONVERSATIONS
# ============================================================================

with tabs[0]:
    st.header("💬 Real Conversations")
    
    if "conversations" in all_data["content"]:
        conversations = all_data["content"]["conversations"]["conversations"]
        
        scenario_names = [c["scenario"] for c in conversations]
        selected = st.selectbox("Choose a scenario:", scenario_names)
        
        for conv in conversations:
            if conv["scenario"] == selected:
                st.markdown(f"**Setting:** {conv['setting']}")
                st.markdown(f"**Difficulty:** {conv['difficulty']}")
                st.divider()
                
                for exchange in conv["exchanges"]:
                    emoji = conv["emoji"] if exchange["speaker"] == conv["customer_name"] else conv["vendor_emoji"]
                    st.markdown(f"**{emoji} {exchange['speaker']}**")
                    st.write(f"🇪🇸 *{exchange['spanish']}*")
                    st.write(f"🇬🇧 {exchange['english']}")
                    
                    # Audio for Spanish
                    audio = create_audio(exchange['spanish'], lang='es')
                    if audio:
                        st.audio(audio, format='audio/mp3')
                    st.divider()

# ============================================================================
# TAB 2: GRAMMAR
# ============================================================================

with tabs[1]:
    st.header("📚 Grammar")
    
    grammar_tab1, grammar_tab2, grammar_tab3 = st.tabs(["Pronouns", "Verbs", "Phrases"])
    
    # Pronouns
    with grammar_tab1:
        if "pronouns" in all_data["content"]:
            pronouns_data = all_data["content"]["pronouns"]
            st.subheader("Spanish Pronouns")
            
            for pronoun in pronouns_data["pronouns"]:
                with st.expander(f"**{pronoun['person']}**"):
                    for ptype in ["subject", "object", "possessive"]:
                        p = pronoun["pronouns"][ptype]
                        st.write(f"**{ptype.upper()}:** {p['form']} - {p['english']}")
                        st.caption(f"Ex: {p['example']} = {p['example_english']}")
                        audio = create_audio(p['example'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                        st.divider()
    
    # Verbs
    with grammar_tab2:
        if "grammar_verbs" in all_data["content"]:
            verbs = all_data["content"]["grammar_verbs"]["verbs"]
            verb_names = [v["infinitive"] for v in verbs]
            selected_verb = st.selectbox("Choose a verb:", verb_names)
            
            for verb in verbs:
                if verb["infinitive"] == selected_verb:
                    display_verb_conjugation(verb)
    
    # Phrases
    with grammar_tab3:
        if "phrases" in all_data["content"]:
            phrases = all_data["content"]["phrases"]["phrases"]
            for phrase in phrases[:20]:  # Display first 20
                with st.expander(f"**{phrase['spanish']}**"):
                    st.write(f"🇬🇧 {phrase['english']}")
                    st.caption(f"*{phrase['pronunciation']}*")
                    st.caption(f"Context: {phrase['context']}")
                    audio = create_audio(phrase['spanish'], lang='es')
                    if audio:
                        st.audio(audio, format='audio/mp3')

# ============================================================================
# TABS 3-6: SCENARIO-BASED VOCAB (Market, Hospital, Papelería, School)
# ============================================================================

scenarios = [
    (tabs[2], "market", "🏪 Market Vocabulary"),
    (tabs[3], "hospital", "🏥 Hospital Vocabulary"),
    (tabs[4], "papeleria", "📝 Paper Store Vocabulary"),
    (tabs[5], "school", "🎓 School Vocabulary")
]

for tab, scenario_key, title in scenarios:
    with tab:
        st.header(title)
        
        query = st.text_input("🔍 Search for a word:", key=f"search_{scenario_key}")
        
        if query:
            results = search_vocabulary(query, scenario_key)
            
            if results:
                st.success(f"Found {len(results)} match(es)")
                for item in results:
                    display_vocabulary_entry(item)
            else:
                st.warning("Word not found in vocabulary")
                
                # AI Vocab fallback
                if has_groq:
                    if st.button(f"💡 Ask AI about '{query}'", key=f"ai_{scenario_key}"):
                        ai_result = get_ai_vocab_response(query, scenario_key)
                        display_ai_vocab(ai_result)
                else:
                    st.info("This word is not in the vocabulary database yet.")

# ============================================================================
# TABS 7-11: REFERENCES
# ============================================================================

with tabs[6]:  # Measurements
    st.header("📐 Measurements")
    if "references" in all_data["content"]:
        refs = all_data["content"]["references"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Weight")
            for item in refs["measurements"]["weight"]:
                st.write(f"{item['spanish']} = {item['english']}")
        
        with col2:
            st.subheader("Volume")
            for item in refs["measurements"]["volume"]:
                st.write(f"{item['spanish']} = {item['english']}")

with tabs[7]:  # Time
    st.header("⏰ Time Expressions")
    if "references" in all_data["content"]:
        refs = all_data["content"]["references"]["time"]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("Days")
            for day in refs["days"]:
                st.write(f"{day['spanish']} - {day['english']}")
        
        with col2:
            st.subheader("Months")
            for month in refs["months"][:6]:
                st.write(f"{month['spanish']} - {month['english']}")
        
        with col3:
            st.subheader("Time of Day")
            for expr in refs["time_expressions"]:
                st.write(f"{expr['spanish']} - {expr['english']}")

with tabs[8]:  # Numbers
    st.header("🔢 Numbers")
    if "references" in all_data["content"]:
        refs = all_data["content"]["references"]["numbers"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Basic (0-10)")
            for num in refs["basic"]:
                st.write(f"{num['spanish']} = {num['number']}")
        
        with col2:
            st.subheader("Tens")
            for num in refs["tens"]:
                st.write(f"{num['spanish']} = {num['number']}")

with tabs[9]:  # Money
    st.header("💰 Money & Currencies")
    if "references" in all_data["content"]:
        refs = all_data["content"]["references"]["money"]
        
        st.subheader("Currencies")
        for curr in refs["currencies"]:
            st.write(f"**{curr['name']}** ({curr['code']}) - {curr['spanish']}")
        
        st.divider()
        st.subheader("Payment Methods")
        for method in refs["payment_methods"]:
            st.write(f"{method['spanish']} = {method['english']}")

with tabs[10]:  # Transportation
    st.header("🚗 Transportation")
    if "expanded" in all_data["vocabulary"]:
        expanded = all_data["vocabulary"]["expanded"]
        if "neighborhoods" in expanded:
            neighborhoods = expanded["neighborhoods"]
            
            st.subheader("Querétaro Areas")
            for area in neighborhoods["querétaro_areas"][:5]:
                st.write(f"**{area['spanish']}** - {area['english']}: {area['characteristics']}")
            
            st.divider()
            st.subheader("Transportation Options")
            for transport in neighborhoods["transportation"]:
                st.write(f"{transport['spanish']} = {transport['english']}")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
---
**Contexto MVP** • Built for expats in Querétaro • Phase 2: RAG Architecture
- Total Vocabulary: 1500+ items
- Verbs: 18 (3 tenses each)
- Conversations: 4 real scenarios
- AI Vocabulary: Backend-controlled (Groq API)

[GitHub](https://github.com/dpabas22/contexto-ai-learning) • [Live Demo](https://contexto-rag-demo.streamlit.app)
""")
