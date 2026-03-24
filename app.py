import streamlit as st
import requests

st.set_page_config(page_title="PokeDND: The ultimate web guide", layout="wide")

# --- CACHING FUNCTIONS ---

@st.cache_data(ttl=86400)
def get_all_tm_moves():
    """Fetches every move that is a TM/HM in the games to create a 'Master List'."""
    # We query the 'move-learn-method' for 'machine' to get the full list
    # This is a bit of a shortcut to get common TMs across generations
    url = "https://pokeapi.co/api/v2/move-learn-method/4/" 
    res = requests.get(url).json()
    return {m['name'].replace("-", " ").title() for m in res['names']} # Using a set for math

@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    try:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}")
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=86400)
def get_evolution_info(pokemon_name):
    # (Same evolution logic as before)
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
            return next_evo['species']['name'], next_evo['evolution_details'][0].get('min_level') or "Special"
    except:
        return None, None
    return "No further evolution", None

# --- UI ---
st.title("🔴 PokéDex TM Tracker")
pokemon_name = st.text_input("Enter Pokémon Name", value="Pikachu").lower()

if pokemon_name:
    data = get_pokemon_data(pokemon_name)
    all_tms = get_all_tm_moves()
    
    if data:
        # Top Section: Stats & Image
        col1, col2 = st.columns([1, 1])
        with col1:
            st.header(data['name'].capitalize())
            st.image(data['sprites']['other']['official-artwork']['front_default'], use_container_width=True)
        with col2:
            st.subheader("Base Stats")
            for s in data['stats']:
                val = s['base_stat']
                st.write(f"**{s['stat']['name'].upper()}**: {val}")
                st.progress(min(val / 150, 1.0))

        # Evolution Section
        st.divider()
        evo_name, lvl = get_evolution_info(pokemon_name)
        if evo_name and evo_name != "No further evolution":
            st.subheader(f"🧬 Evolves into: {evo_name.capitalize()} (Level {lvl})")
            evo_data = get_pokemon_data(evo_name)
            if evo_data: st.image(evo_data['sprites']['other']['official-artwork']['front_default'], width=200)

        # TM SECTION: Can Learn vs Cant Learn
        st.divider()
        st.subheader("💿 Technical Machine (TM) Compatibility")
        
        # 1. Get moves this specific pokemon learns via TM
        can_learn = {
            m['move']['name'].replace("-", " ").title() 
            for m in data['moves'] 
            if any(d['move_learn_method']['name'] == 'machine' for d in m['version_group_details'])
        }
        
        # 2. Calculate what it CANNOT learn (Master List - Can Learn)
        # We filter out moves that aren't in the can_learn set
        cant_learn = sorted(list(all_tms - can_learn))
        can_learn_list = sorted(list(can_learn))

        tm_col1, tm_col2 = st.columns(2)
        
        with tm_col1:
            st.success(f"✅ **Can Learn ({len(can_learn_list)})**")
            # Using a text area or a long string to avoid huge vertical scrolling
            st.write(", ".join(can_learn_list))

        with tm_col2:
            st.error(f"❌ **Cannot Learn ({len(cant_learn)})**")
            st.write(", ".join(cant_learn))

    else:
        st.error("Pokémon not found!")
