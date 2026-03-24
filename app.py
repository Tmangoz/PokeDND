import streamlit as st
import requests
# Updated Sidebar Navigation in app.py
st.sidebar.title("🎮 PokéDND Menu")

# If you want a button that specifically acts as a "Home" reset
if st.sidebar.button("🏠 Home Page"):
    st.switch_page("app.py")

if st.sidebar.button("➡️ Go to Team Builder"):
    try:
        st.switch_page("pages/1_Team_Builder.py")
    except:
        st.switch_page("1_Team_Builder.py")
# 1. Page Config - Forces sidebar to stay open and uses wide layout
st.set_page_config(page_title="PokéDex Explorer", layout="wide", initial_sidebar_state="expanded")

# 2. Type Colors Dictionary
TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

# Initialize Team in Session State
if 'team' not in st.session_state:
    st.session_state['team'] = []

# --- CACHED DATA FETCHING ---
@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}")
        return res.json() if res.status_code == 200 else None
    except: return None

@st.cache_data(ttl=86400)
def get_move_type(move_url):
    try:
        res = requests.get(move_url).json()
        return res['type']['name']
    except: return "normal"

@st.cache_data(ttl=86400)
def get_evolution_info(pokemon_name):
    try:
        species_res = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower().strip()}")
        if species_res.status_code != 200: return None, None
        evo_chain_url = species_res.json()['evolution_chain']['url']
        evo_res = requests.get(evo_chain_url).json()
        chain = evo_res['chain']
        while chain and chain['species']['name'] != pokemon_name.lower().strip():
            if chain['evolves_to']: chain = chain['evolves_to'][0]
            else: break
        if chain and chain['evolves_to']:
            next_evo = chain['evolves_to'][0]
            lvl = next_evo['evolution_details'][0].get('min_level') or "Special"
            return next_evo['species']['name'], lvl
    except: return None, None
    return "No further evolution", None

# --- MAIN UI ---
st.title("🔍 Pokémon Explorer")

search_name = st.text_input("Search Pokémon Name", value="Pikachu")

if search_name:
    data = get_pokemon_data(search_name)
    
    if data:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Official high-res artwork
            st.image(data['sprites']['other']['official-artwork']['front_default'], width=250)
            
            if st.button("➕ Add to Team"):
                if len(st.session_state['team']) < 6:
                    if not any(p['name'] == data['name'] for p in st.session_state['team']):
                        st.session_state['team'].append(data)
                        st.success(f"Added {data['name'].capitalize()}!")
                    else:
                        st.warning("Already in team!")
                else:
                    st.error("Team is full!")
        
        with col2:
            st.header(data['name'].capitalize())
            # Display stats
            for s in data['stats']:
                name = s['stat']['name'].upper().replace("-", " ")
                val = s['base_stat']
                st.write(f"**{name}**: {val}")
                st.progress(min(val/150, 1.0))

        # --- EVOLUTION SECTION ---
        st.divider()
        st.subheader("🧬 Evolution")
        evo_name, lvl = get_evolution_info(search_name)
        if evo_name and evo_name != "No further evolution":
            evo_data = get_pokemon_data(evo_name)
            e_col1, e_col2 = st.columns([1, 3])
            with e_col1:
                if evo_data:
                    st.image(evo_data['sprites']['other']['official-artwork']['front_default'], width=150)
            with e_col2:
                st.write(f"Evolves into: **{evo_name.capitalize()}**")
                st.write(f"Level required: **{lvl}**")
        else:
            st.info("This Pokémon does not evolve further.")

        # --- TM SECTION ---
        st.divider()
        st.subheader("💿 Learnable TMs")
        
        with st.spinner('Calculating move compatibility...'):
            tm_badges_list = []
            for m in data['moves']:
                is_tm = any(d['move_learn_method']['name'] == 'machine' for d in m['version_group_details'])
                if is_tm:
                    m_name = m['move']['name'].replace("-"," ").upper()
                    m_url = m['move']['url']
                    m_type = get_move_type(m_url)
                    bg = TYPE_COLORS.get(m_type, "#777")
                    
                    # Single-line HTML string to prevent Streamlit from breaking
                    badge = f'<div style="background-color:{bg}; color:white; padding:6px 12px; border-radius:15px; margin:5px; font-size:11px; font-weight:bold; display:inline-block; box-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{m_name}</div>'
                    tm_badges_list.append(badge)

            if tm_badges_list:
                # Wrap all badges in a flex container for the grid effect
                container_html = f'<div style="display:flex; flex-wrap:wrap;">{"".join(tm_badges_list)}</div>'
                st.markdown(container_html, unsafe_allow_html=True)
            else:
                st.write("No TM data found.")

    else:
        st.error("Pokémon not found. Please check your spelling!")

# Sidebar Info
st.sidebar.title("PokéTeam Management")
st.sidebar.write(f"Current Team Members: **{len(st.session_state['team'])} / 6**")
if st.sidebar.button("Clear Team"):
    st.session_state['team'] = []
    st.rerun()
