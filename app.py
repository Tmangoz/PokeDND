import streamlit as st
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="PokéDex Cloud", page_icon="Basecamp")

# --- CACHING ---
# This tells Streamlit to remember the results for 24 hours (86400 seconds)
@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    """Fetches base data, stats, and sprites."""
    try:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}")
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

@st.cache_data(ttl=86400)
def get_evolution_info(pokemon_name):
    """Fetches evolution chain and the next evolution stage."""
    try:
        species_res = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower().strip()}")
        if species_res.status_code != 200:
            return None, None
        
        species_data = species_res.json()
        evo_chain_url = species_data['evolution_chain']['url']
        evo_res = requests.get(evo_chain_url).json()
        
        chain = evo_res['chain']
        # Simple traversal to find the next evolution
        while chain and chain['species']['name'] != pokemon_name.lower().strip():
            if chain['evolves_to']:
                chain = chain['evolves_to'][0]
            else:
                break
                
        if chain and chain['evolves_to']:
            next_evo = chain['evolves_to'][0]
            evo_name = next_evo['species']['name']
            details = next_evo['evolution_details'][0]
            min_level = details.get('min_level') or "Special Condition"
            return evo_name, min_level
    except:
        return None, None
    return "No further evolution", None

# --- UI LAYOUT ---
st.title("🔴 PokéDex Cloud Explorer")
st.markdown("Enter a Pokémon name below to see its stats, TMs, and evolutions.")

pokemon_name = st.text_input("Pokémon Name", value="Charizard").lower()

if pokemon_name:
    data = get_pokemon_data(pokemon_name)
    
    if data:
        # Create two columns for General Info & Stats
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header(data['name'].capitalize())
            # Official high-res artwork
            img_url = data['sprites']['other']['official-artwork']['front_default']
            st.image(img_url, use_container_width=True)
            
        with col2:
            st.subheader("Base Stats")
            for s in data['stats']:
                stat_name = s['stat']['name'].replace("-", " ").title()
                stat_val = s['base_stat']
                st.write(f"**{stat_name}**: {stat_val}")
                # Color code the bars based on power
                bar_color = "green" if stat_val > 90 else "orange" if stat_val > 50 else "red"
                st.progress(min(stat_val / 150, 1.0))

        # --- EVOLUTIONS ---
        st.divider()
        st.subheader("🧬 Evolution")
        next_name, lvl = get_evolution_info(pokemon_name)
        
        if next_name and next_name != "No further evolution":
            next_data = get_pokemon_data(next_name)
            c1, c2 = st.columns([1, 2])
            with c1:
                if next_data:
                    st.image(next_data['sprites']['other']['official-artwork']['front_default'], width=150)
            with c2:
                st.write(f"Next Stage: **{next_name.capitalize()}**")
                st.write(f"Evolution Requirement: **Level {lvl}**")
        else:
            st.info("This Pokémon is at its final stage or has a unique evolution branching.")

        # --- TM LIST ---
        st.divider()
        with st.expander("📚 View Learnable TMs"):
            tm_moves = [
                m['move']['name'].replace("-", " ").title() 
                for m in data['moves'] 
                if any(d['move_learn_method']['name'] == 'machine' for d in m['version_group_details'])
            ]
            if tm_moves:
                st.write(", ".join(tm_moves))
            else:
                st.write("No TM data found.")
    else:
        st.error("Could not find that Pokémon. Did you spell it correctly?")
