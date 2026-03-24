import streamlit as st
import requests

st.set_page_config(page_title="PokéDex Explorer", layout="wide")

# Initialize team in session state so it persists across pages
if 'team' not in st.session_state:
    st.session_state['team'] = []

@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}")
        return res.json() if res.status_code == 200 else None
    except: return None

st.title("🔍 Pokémon Explorer")

search_name = st.text_input("Search Pokémon Name", value="Pikachu")

if search_name:
    data = get_pokemon_data(search_name)
    if data:
        col1, col2 = st.columns([1, 2])
        with col1:
            # Small, clean image
            st.image(data['sprites']['other']['official-artwork']['front_default'], width=250)
            
            if st.button("➕ Add to Team"):
                if len(st.session_state['team']) < 6:
                    # Check if already in team
                    if any(p['name'] == data['name'] for p in st.session_state['team']):
                        st.warning("Already in team!")
                    else:
                        st.session_state['team'].append(data)
                        st.success(f"Added {data['name'].capitalize()}!")
                else:
                    st.error("Team is full (Max 6)!")
        
        with col2:
            st.header(data['name'].capitalize())
            # Simple Stats List
            for s in data['stats']:
                st.write(f"**{s['stat']['name'].upper()}**: {s['base_stat']}")
    else:
        st.error("Pokémon not found.")
