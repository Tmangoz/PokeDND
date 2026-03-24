import streamlit as st
import requests

# 1. Page Config
st.set_page_config(page_title="PokéDND Explorer", layout="wide")

# 2. Hide Default Sidebar Navigation & Custom CSS
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .stat-text { font-size: 16px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# 3. API Fetching Functions
@st.cache_data(ttl=86400)
def get_all_pokemon_names():
    try:
        url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
        response = requests.get(url).json()
        return [p['name'] for p in response['results']]
    except:
        return []

@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    if not name: return None
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# 4. Session State Initialization
if 'team' not in st.session_state:
    st.session_state['team'] = []

# --- SIDEBAR MENU ---
st.sidebar.title("🎮 PokéDND Menu")

if st.sidebar.button("🏠 Home Page", use_container_width=True):
    st.switch_page("app.py")

team_count = len(st.session_state['team'])
if st.sidebar.button(f"➡️ Team Builder ({team_count}/6)", use_container_width=True):
    st.switch_page("pages/Team_Builder.py")

st.sidebar.divider()
st.sidebar.info(f"Party: {team_count} / 6")

# --- MAIN INTERFACE ---
st.title("🔍 Pokémon Explorer")

all_names = get_all_pokemon_names()

search_query = st.selectbox(
    "Search for a Pokémon:",
    options=[""] + all_names,
    format_func=lambda x: x.capitalize() if x else "Type to search (e.g. Charizard)...",
    index=0
)

if search_query:
    with st.spinner(f"Fetching {search_query.capitalize()}..."):
        p_data = get_pokemon_data(search_query)
        
    if p_data:
        st.divider()
        # Layout: 2 parts for Image, 3 parts for Stats/Moves
        col1, col2 = st.columns([2, 3])
        
        with col1:
            # High-res Official Artwork at 400px
            artwork_url = p_data['sprites']['other']['official-artwork']['front_default']
            st.image(artwork_url if artwork_url else p_data['sprites']['front_default'], width=400)
            
            # Add to Team Button
            if st.button(f"➕ Add {p_data['name'].capitalize()} to Team", use_container_width=True, type="primary"):
                if len(st.session_state['team']) < 6:
                    if any(p['name'] == p_data['name'] for p in st.session_state['team']):
                        st.warning("Already in your team!")
                    else:
                        st.session_state['team'].append(p_data)
                        st.success(f"Added {p_data['name'].capitalize()}!")
                        st.rerun()
                else:
                    st.error("Team is full! (Max 6)")

        with col2:
            st.header(p_data['name'].capitalize())
            
            # Types displayed as badges
            type_badges = "".join([f'<span style="background-color:#555; color:white; padding:4px 12px; border-radius:15px; margin-right:8px; font-weight:bold; font-size:14px;">{t["type"]["name"].upper()}</span>' for t in p_data['types']])
            st.markdown(type_badges, unsafe_allow_html=True)
            
            st.write("### Base Stats")
            STAT_LABELS = {
                "hp": "HP", "attack": "ATK", "defense": "DEF", 
                "special-attack": "SpA", "special-defense": "SpD", "speed": "Spd"
            }
            
            # Fixed the formatting for the stat columns
            stat_cols = st.columns(2)
            for idx, s in enumerate(p_data['stats']):
                label = STAT_LABELS.get(s['stat']['name'], s['stat']['name'].upper())
                val = s['base_stat']
                with stat_cols[idx % 2]:
                    st.markdown(f"**{label}:** {val}")
                    st.progress(min(val / 160, 1.0))

            st.divider()
            
            # Learnable Moves Section
            st.write("### 📜 Learnable Moves")
            moves = sorted([m['move']['name'].replace("-", " ").title() for m in p_data['moves']])
            
            with st.expander(f"View all {len(moves)} moves for {p_data['name'].capitalize()}"):
                m_cols = st.columns(3)
                for i, m_name in enumerate(moves):
                    m_cols[i % 3].write(f"• {m_name}")

    else:
        st.error("Pokémon not found.")
else:
    st.info("Use the search bar above to find a Pokémon and view its stats.")
