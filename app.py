import streamlit as st
import requests

st.set_page_config(page_title="PokéDex Explorer", layout="wide", initial_sidebar_state="expanded")

if 'team' not in st.session_state:
    st.session_state['team'] = []

@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}")
        return res.json() if res.status_code == 200 else None
    except: return None

@st.cache_data(ttl=86400)
def get_all_tm_moves():
    # Fetches the master list of all moves that can be taught via TM (Machine)
    url = "https://pokeapi.co/api/v2/move-learn-method/4/" 
    res = requests.get(url).json()
    return {m['name'].replace("-", " ").title() for m in res['names']}

st.title("🔍 Pokémon Explorer")

search_name = st.text_input("Search Pokémon Name", value="Pikachu")

if search_name:
    data = get_pokemon_data(search_name)
    all_tms = get_all_tm_moves()
    
    if data:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(data['sprites']['other']['official-artwork']['front_default'], width=250)
            if st.button("➕ Add to Team"):
                if len(st.session_state['team']) < 6:
                    st.session_state['team'].append(data)
                    st.success(f"Added {data['name'].capitalize()}!")
                else:
                    st.error("Team is full!")
        
        with col2:
            st.header(data['name'].capitalize())
            for s in data['stats']:
                st.write(f"**{s['stat']['name'].upper()}**: {s['base_stat']}")

        # --- THE TM SECTION (RESTORING THIS) ---
        st.divider()
        st.subheader("💿 TM Compatibility")
        
        can_learn = {
            m['move']['name'].replace("-", " ").title() 
            for m in data['moves'] 
            if any(d['move_learn_method']['name'] == 'machine' for d in m['version_group_details'])
        }
        
        cant_learn = sorted(list(all_tms - can_learn))
        can_learn_list = sorted(list(can_learn))

        tm_col1, tm_col2 = st.columns(2)
        with tm_col1:
            st.success(f"✅ **Can Learn ({len(can_learn_list)})**")
            st.write(", ".join(can_learn_list))
        with tm_col2:
            st.error(f"❌ **Cannot Learn ({len(cant_learn)})**")
            st.write(", ".join(cant_learn))
    else:
        st.error("Pokémon not found.")
