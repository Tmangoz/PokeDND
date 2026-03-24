import streamlit as st
import requests

# 1. Page Config (Forces sidebar to stay open)
st.set_page_config(page_title="PokéDex Explorer", layout="wide", initial_sidebar_state="expanded")

# 2. Type Colors Dictionary
TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

if 'team' not in st.session_state:
    st.session_state['team'] = []

# --- CACHED FUNCTIONS ---
@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}")
        return res.json() if res.status_code == 200 else None
    except: return None

@st.cache_data(ttl=86400)
def get_move_type(move_url):
    """Fetches the type of a specific move."""
    try:
        res = requests.get(move_url).json()
        return res['type']['name']
    except: return "normal"

@st.cache_data(ttl=86400)
def get_all_tm_moves():
    url = "https://pokeapi.co/api/v2/move-learn-method/4/" 
    res = requests.get(url).json()
    return {m['name'].replace("-", " ").title() for m in res['names']}

# --- UI ---
st.title("🔍 Pokémon Explorer")

search_name = st.text_input("Search Pokémon Name", value="Pikachu")

if search_name:
    data = get_pokemon_data(search_name)
    all_tms = get_all_tm_moves()
    
    if data:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(data['sprites']['other']['official-artwork']['front_default'], width=220)
            if st.button("➕ Add to Team"):
                if len(st.session_state['team']) < 6:
                    st.session_state['team'].append(data)
                    st.success(f"Added {data['name'].capitalize()}!")
                else:
                    st.error("Team is full!")
        
        with col2:
            st.header(data['name'].capitalize())
            # Stat display
            for s in data['stats']:
                st.write(f"**{s['stat']['name'].upper()}**: {s['base_stat']}")

        st.divider()
        st.subheader("💿 TM Compatibility (Colored by Type)")
        
        # We use a spinner because fetching 50+ move types can take a moment
        with st.spinner('Fetching move types...'):
            can_learn_html = []
            can_learn_set = set()

            for m in data['moves']:
                # Filter for TMs
                is_tm = any(d['move_learn_method']['name'] == 'machine' for d in m['version_group_details'])
                if is_tm:
                    m_name = m['move']['name']
                    m_url = m['move']['url']
                    m_type = get_move_type(m_url)
                    bg = TYPE_COLORS.get(m_type, "#777")
                    
                    # Store for 'Can Learn' HTML
                    badge = f'<span style="background-color:{bg}; color:white; padding:4px 10px; border-radius:12px; margin:4px; display:inline-block; font-size:11px; font-weight:bold; border: 1px solid rgba(255,255,255,0.2);">{m_name.replace("-"," ").upper()}</span>'
                    can_learn_html.append(badge)
                    can_learn_set.add(m_name.replace("-", " ").title())

            # Calculate Cannot Learn
            cant_learn_list = sorted(list(all_tms - can_learn_set))

            tm_col1, tm_col2 = st.columns(2)
            with tm_col1:
                st.success(f"✅ **Can Learn ({len(can_learn_html)})**")
                st.markdown("".join(can_learn_html), unsafe_allow_html=True)
            
            with tm_col2:
                st.error(f"❌ **Cannot Learn ({len(cant_learn_list)})**")
                st.write(", ".join(cant_learn_list))
    else:
        st.error("Pokémon not found.")
