import streamlit as st
import requests

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
def get_move_details(move_url):
    try:
        return requests.get(move_url).json()
    except: return None

st.title("🏆 My Pokémon Team")

if 'team' not in st.session_state or len(st.session_state['team']) == 0:
    st.info("Your team is empty! Go back to the Explorer to add some Pokémon.")
else:
    # Use a container to hold the grid
    for i, p_data in enumerate(st.session_state['team']):
        # Create a box for each Pokemon
        with st.container(border=True):
            # Split the slot into Image/Stats side and Move Selection side
            main_col1, main_col2 = st.columns([2, 3])
            
            with main_col1:
                st.subheader(f"{p_data['name'].capitalize()}")
                
                # Nested columns: Image on Left, Stats on Right
                img_col, stat_col = st.columns([1, 1])
                with img_col:
                    st.image(p_data['sprites']['front_default'], width=120)
                    if st.button("🗑️ Remove", key=f"rem_{i}"):
                        st.session_state['team'].pop(i)
                        st.rerun()
                
                with stat_col:
                    for s in p_data['stats']:
                        # Shorten stat names to fit better (e.g., Special Attack -> Sp.Atk)
                        short_name = s['stat']['name'].replace("special-attack", "Sp.Atk").replace("special-defense", "Sp.Def").upper()
                        st.write(f"**{short_name}**: {s['base_stat']}")

            with main_col2:
                # Move Selection
                move_names = [m['move']['name'] for m in p_data['moves']]
                selected = st.multiselect(
                    f"Select 4 Moves for {p_data['name'].capitalize()}", 
                    options=move_names, 
                    max_selections=4, 
                    key=f"move_sel_{i}"
                )
                
                # Render Colored Badges with Power
                move_html = '<div style="display: flex; flex-wrap: wrap;">'
                for m_name in selected:
                    m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == m_name)
                    m_info = get_move_details(m_url)
                    
                    if m_info:
                        m_type = m_info['type']['name']
                        m_power = m_info.get('power') if m_info.get('power') else "—"
                        bg = TYPE_COLORS.get(m_type, "#777")
                        
                        move_html += f'''
                            <div style="background-color:{bg}; color:white; padding:5px 12px; border-radius:10px; margin:4px; font-size:12px; font-weight:bold; min-width:140px; text-align:center; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">
                                {m_name.replace("-"," ").upper()}<br>
                                <span style="font-size:10px; opacity:0.9;">PWR: {m_power} | {m_type.upper()}</span>
                            </div>
                        '''
                move_html += '</div>'
                st.markdown(move_html, unsafe_allow_html=True)

    st.divider()
    if st.button("Clear Full Team"):
        st.session_state['team'] = []
        st.rerun()
