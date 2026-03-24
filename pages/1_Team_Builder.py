import streamlit as st
import requests
st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.set_page_config(page_title="Team Builder", layout="wide")

# Colors for Move Types
TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

@st.cache_data(ttl=86400)
def get_move_details(move_url):
    return requests.get(move_url).json()

st.title("🏆 My Pokémon Team")

if not st.session_state.get('team'):
    st.info("Your team is empty! Go to the Home page to find some Pokémon.")
else:
    # Display team in a grid
    rows = [st.columns(3), st.columns(3)]
    
    for i, p_data in enumerate(st.session_state['team']):
        col = rows[i // 3][i % 3]
        with col:
            st.markdown(f"### {p_data['name'].capitalize()}")
            st.image(p_data['sprites']['front_default'], width=100) # Smaller sprite
            
            # Show stats succinctly
            stats_str = " | ".join([f"{s['stat']['name'][:2].upper()}: {s['base_stat']}" for s in p_data['stats']])
            st.caption(stats_str)
            
            # Move Selection
            move_options = [m['move']['name'] for m in p_data['moves']]
            selected = st.multiselect("Select 4 Moves", move_options, max_selections=4, key=f"m_{i}")
            
            # Display colored moves
            for m_name in selected:
                # Find move URL to get the type
                m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == m_name)
                m_info = get_move_details(m_url)
                m_type = m_info['type']['name']
                bg_color = TYPE_COLORS.get(m_type, "#777")
                
                st.markdown(
                    f'<div style="background-color:{bg_color}; color:white; padding:3px 10px; border-radius:5px; margin:2px 0; font-size:12px; text-align:center; font-weight:bold;">'
                    f'{m_name.replace("-"," ").upper()} ({m_type.upper()})</div>', 
                    unsafe_allow_html=True
                )
            
            if st.button("🗑️ Remove", key=f"remove_{i}"):
                st.session_state['team'].pop(i)
                st.rerun()

    if st.button("Clear Team"):
        st.session_state['team'] = []
        st.rerun()
