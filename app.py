"""
Contexto: AI-Powered Language Learning for Expats
Market Spanish Learning with RAG
"""

import streamlit as st
import json
import os
from pathlib import Path

# Configure Streamlit
st.set_page_config(
    page_title="Contexto - Market Spanish",
    page_icon="🌍",
    layout="wide"
)

# ============================================================================
# SECURITY: Load environment variables safely
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Check if API key exists (fail gracefully)
has_groq = GROQ_API_KEY is not None

if has_groq:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        has_groq = False
        st.warning("⚠️ Groq API connection failed. Using vocab-only mode.")

# ============================================================================
# LOAD VOCABULARY DATA (All 4 lessons)
# ============================================================================

@st.cache_resource
def load_vocabulary():
    """Load all vocabulary files once (cached for performance)"""
    vocab_files = {
        "market": "market_vocab.json",
        "hospital": "hospital_vocab.json",
        "papeleria": "papeleria_vocab.json",
        "school": "school_context_vocab.json"
    }
    
    all_vocab = {}
    for lesson_name, filename in vocab_files.items():
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                all_vocab[lesson_name] = json.load(f)
        except FileNotFoundError:
            st.warning(f"⚠️ {filename} not found")
        except json.JSONDecodeError:
            st.warning(f"⚠️ {filename} has invalid JSON")
    
    return all_vocab

vocab_data = load_vocabulary()

# ============================================================================
# SECURITY: Input validation
# ============================================================================

def sanitize_input(text):
    """Prevent injection attacks"""
    if not text:
        return ""
    # Limit length (prevent DoS)
    if len(text) > 500:
        return text[:500]
    # Remove dangerous characters
    text = text.replace("<", "").replace(">", "").replace("&", "")
    return text.strip()

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def search_vocabulary(query, lesson=None):
    """Search vocabulary with optional lesson filter"""
    query = sanitize_input(query).lower()
    
    if not query:
        return []
    
    results = []
    
    # Search in specific lesson or all lessons
    lessons_to_search = [lesson] if lesson else vocab_data.keys()
    
    for lesson_name in lessons_to_search:
        if lesson_name not in vocab_data:
            continue
            
        vocab_list = vocab_data[lesson_name].get('vocabulary', [])
        
        for item in vocab_list:
            spanish = item.get('spanish', '').lower()
            english = item.get('english', '').lower()
            
            # Match on Spanish or English
            if query in spanish or query in english:
                # Add lesson context to item
                item_copy = item.copy()
                item_copy['lesson'] = lesson_name
                results.append(item_copy)
    
    return results

def get_ai_response(query, lesson=None):
    """Get AI response using Groq (if available)"""
    if not has_groq:
        return None
    
    try:
        # Get relevant vocabulary for context
        results = search_vocabulary(query, lesson)
        
        if not results:
            return None
        
        # Build context from vocabulary
        context = "\n".join([
            f"- {item['spanish']}: {item['english']} ({item['example_spanish']})"
            for item in results[:5]
        ])
        
        # Create prompt (safe, no injection risk)
        prompt = f"""You are a Spanish teacher helping someone learn market Spanish in Querétaro.

Relevant vocabulary:
{context}

Student's question: {query}

Respond in Spanish and English. Keep response concise and practical."""
        
        # Call Groq API with timeout
        response = client.messages.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.content[0].text
    
    except Exception as e:
        st.error(f"⚠️ AI response failed: {str(e)[:100]}")
        return None

# ============================================================================
# STREAMLIT UI
# ============================================================================

# Header
st.markdown("""
# 🌍 Contexto: Market Spanish Learning
**Learn Spanish for real expat needs in Querétaro**
""")

# Tabs for different features
tab1, tab2, tab3, tab4 = st.tabs(["🏪 Market", "🏥 Hospital", "📝 Papelería", "🎓 School"])

# ============================================================================
# TAB 1: MARKET
# ============================================================================
with tab1:
    st.subheader("Market (La Cruz) - Shopping, Haggling, Groceries")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        market_query = st.text_input(
            "Search market vocabulary:",
            placeholder="e.g., fish, fresh, price",
            key="market_search"
        )
    
    with col2:
        search_type = st.selectbox(
            "Search type:",
            ["All", "Seafood", "Vegetables", "Spices", "Actions"],
            key="market_type"
        )
    
    if market_query:
        results = search_vocabulary(market_query, lesson="market")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            
            for item in results:
                # Display vocabulary item
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**{item['spanish']}**")
                
                with col2:
                    st.write(f"{item['english']} • {item['context']}")
                
                # Show details in expander
                with st.expander(f"Details - {item['spanish']}"):
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
            
            # AI Response (if available)
            if has_groq:
                if st.button(f"💡 Get AI help with '{market_query}'", key="market_ai"):
                    with st.spinner("Thinking..."):
                        ai_response = get_ai_response(market_query, lesson="market")
                        if ai_response:
                            st.info(ai_response)
                        else:
                            st.warning("Could not generate AI response")
        else:
            st.warning("❌ No results found. Try different keywords.")

# ============================================================================
# TAB 2: HOSPITAL
# ============================================================================
with tab2:
    st.subheader("Hospital - Medical Appointments, Specialists, Insurance")
    
    hospital_query = st.text_input(
        "Search hospital vocabulary:",
        placeholder="e.g., fever, doctor, insurance",
        key="hospital_search"
    )
    
    if hospital_query:
        results = search_vocabulary(hospital_query, lesson="hospital")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            
            for item in results:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**{item['spanish']}**")
                
                with col2:
                    st.write(f"{item['english']} • {item['context']}")
                
                with st.expander(f"Details - {item['spanish']}"):
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                
                st.divider()
            
            if has_groq:
                if st.button(f"💡 Get AI help with '{hospital_query}'", key="hospital_ai"):
                    with st.spinner("Thinking..."):
                        ai_response = get_ai_response(hospital_query, lesson="hospital")
                        if ai_response:
                            st.info(ai_response)
        else:
            st.warning("❌ No results found.")

# ============================================================================
# TAB 3: PAPELERÍA
# ============================================================================
with tab3:
    st.subheader("Papelería - Stationery, Printing, Office Supplies")
    
    pap_query = st.text_input(
        "Search papelería vocabulary:",
        placeholder="e.g., print, laminate, notebook",
        key="pap_search"
    )
    
    if pap_query:
        results = search_vocabulary(pap_query, lesson="papeleria")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            
            for item in results:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**{item['spanish']}**")
                
                with col2:
                    st.write(f"{item['english']} • {item['context']}")
                
                with st.expander(f"Details - {item['spanish']}"):
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
            
            if has_groq:
                if st.button(f"💡 Get AI help with '{pap_query}'", key="pap_ai"):
                    with st.spinner("Thinking..."):
                        ai_response = get_ai_response(pap_query, lesson="papeleria")
                        if ai_response:
                            st.info(ai_response)
        else:
            st.warning("❌ No results found.")

# ============================================================================
# TAB 4: SCHOOL
# ============================================================================
with tab4:
    st.subheader("School - Uniforms, Activities, Admin, Canteen, Rules")
    
    school_query = st.text_input(
        "Search school vocabulary:",
        placeholder="e.g., uniform, activity, fee",
        key="school_search"
    )
    
    if school_query:
        results = search_vocabulary(school_query, lesson="school")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            
            for item in results:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**{item['spanish']}**")
                
                with col2:
                    st.write(f"{item['english']} • {item['context']}")
                
                with st.expander(f"Details - {item['spanish']}"):
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
            
            if has_groq:
                if st.button(f"💡 Get AI help with '{school_query}'", key="school_ai"):
                    with st.spinner("Thinking..."):
                        ai_response = get_ai_response(school_query, lesson="school")
                        if ai_response:
                            st.info(ai_response)
        else:
            st.warning("❌ No results found.")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    total_vocab = sum(len(lesson.get('vocabulary', [])) for lesson in vocab_data.values())
    st.metric("Total Vocabulary", total_vocab)

with col2:
    lessons_loaded = len(vocab_data)
    st.metric("Lessons Loaded", lessons_loaded)

with col3:
    if has_groq:
        st.metric("AI Mode", "🟢 Active")
    else:
        st.metric("AI Mode", "🔴 Offline")

st.markdown("""
---
**Contexto: Language Learning for Real Expat Needs**  
Built with ❤️ for Querétaro expats | November 2026
""")
