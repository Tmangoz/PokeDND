import streamlit as st
import requests

# 1. Page Config
st.set_page_config(page_title="PokéDex Explorer", layout="wide", initial_sidebar_state="expanded")

# 2. Type Colors
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
    try:
        res = requests.get(move_url).json()
        return res['type']['name']
    except: return "normal"

# --- UI ---
st.title("🔍 Pokémon Explorer")

search_name = st.text_input("Search Pokémon Name", value="Pikachu")

if search_name:
    data = get_pokemon_data(search_name)
    
    if data:
        col1, col2 = st.columns([1, 2])
        with col1:
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
            # Display stats in a compact list
            for s in data['stats']:
                stat_name = s['stat']['name'].upper().replace("-", " ")
                st.write(f"**{stat_name}**: {s['base_stat']}")

        st.divider()
        st.subheader("💿 Learnable TMs")
        
        with st.spinner('Loading move types...'):
            tm_badges = ""
            # Extract moves learned via 'machine'
            for m in data['moves']:
                is_tm = any(d['move_learn_method']['name'] == 'machine' for d in m['version_group_details'])
                if is_tm:
                    m_name = m['move']['name']
                    m_url = m['move']['url']
                    m_type = get_move_type(m_url)
                    bg = TYPE_COLORS.get(m_type, "#777")
                    
                    # Create the badge HTML
                    tm_badges += f'''
                        <div style="
                            background-color:{bg}; 
                            color:white; 
                            padding:6px 14px; 
                            border-radius:20px; 
                            margin:6px; 
                            font-size:12px; 
                            font-weight:bold; 
                            display: inline-block;
                            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                            white-space: nowrap;
                        ">
                            {m_name.replace("-"," ").upper()}
                        </div>
                    '''

            if tm_badges:
                # Use a wrapper div with flex-wrap to force the grid behavior
                full_html = f'''
                    <div style="display: flex; flex-wrap: wrap; justify-content: flex-start;">
                        {tm_badges}
                    </div>
                '''
                st.markdown(full_html, unsafe_allow_html=True)
            else:
                st.info("No TM data found for this Pokémon.")
    else:
        st.error("Pokémon not found.")

st.sidebar.write(f"**Team Size:** {len(st.session_state['team'])}/6")
