import streamlit as st
import requests

# This ensures the session state (your team) is accessible
if 'team' not in st.session_state:
    st.session_state['team'] = []

# 1. Page Config
st.set_page_config(page_title="Team Builder", layout="wide", initial_sidebar_state="expanded")

# 2. Type Colors
TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

@st.cache_data(ttl=86400)
def get_move_info(move_url):
    try:
        return requests.get(move_url).json()
    except: return None

st.title("🏆 My Pokémon Team")

# Safety check for the session state
if 'team' not in st.session_state or len(st.session_state['team']) == 0:
    st.info("Your team is empty! Go back to the Explorer to add some Pokémon.")
else:
    # Create 2 rows of 3 columns
    row1 = st.columns(3)
    row2 = st.columns(3)
    all_cols = row1 + row2

    for i, p_data in enumerate(st.session_state['team']):
        with all_cols[i]:
            st.markdown(f"### {p_data['name'].capitalize()}")
            # Smaller sprite for the team view
            st.image(p_data['sprites']['front_default'], width=120)
            
            # Stats Summary
            stats_list = [f"{s['stat']['name'][:2].upper()}:{s['base_stat']}" for s in p_data['stats']]
            st.caption(" | ".join(stats_list))
            
            # Move Selection (Max 4)
            move_names = [m['move']['name'] for m in p_data['moves']]
            selected_moves = st.multiselect(
                "Moves", 
                options=move_names, 
                max_selections=4, 
                key=f"team_move_{i}"
            )
            
            # Render Selected Moves as Colored Badges
            move_html = ""
            for m_name in selected_moves:
                # Find the URL for this specific move
                m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == m_name)
                m_info = get_move_info(m_url)
                m_type = m_info['type']['name'] if m_info else "normal"
                bg = TYPE_COLORS.get(m_type, "#777")
                
                move_html += f'<div style="background-color:{bg}; color:white; padding:4px 10px; border-radius:10px; margin:3px 0; font-size:11px; font-weight:bold; text-align:center;">{m_name.replace("-"," ").upper()}</div>'
            
            st.markdown(move_html, unsafe_allow_html=True)
            
            if st.button("🗑️ Remove", key=f"rem_{i}"):
                st.session_state['team'].pop(i)
                st.rerun()

    st.divider()
    if st.button("Clear Full Team"):
        st.session_state['team'] = []
        st.rerun()
