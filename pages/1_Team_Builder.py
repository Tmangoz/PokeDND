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
    for i, p_data in enumerate(st.session_state['team']):
        with st.container(border=True):
            main_col1, main_col2 = st.columns([2, 3])
            
            with main_col1:
                st.subheader(f"{p_data['name'].capitalize()}")
                img_col, stat_col = st.columns([1, 1])
                with img_col:
                    st.image(p_data['sprites']['front_default'], width=120)
                    if st.button("🗑️ Remove", key=f"rem_{i}"):
                        st.session_state['team'].pop(i)
                        st.rerun()
                
                with stat_col:
                    for s in p_data['stats']:
                        short_name = s['stat']['name'].replace("special-attack", "Sp.Atk").replace("special-defense", "Sp.Def").upper()
                        st.write(f"**{short_name}**: {s['base_stat']}")

            with main_col2:
                # RESTRUCTURED MOVE LIST: Formatting names and including TMs
                # We filter to make sure we show moves learned by level-up OR machine (TM)
                all_possible_moves = []
                for m in p_data['moves']:
                    # Check if move is learned by 'level-up' or 'machine'
                    methods = [d['move_learn_method']['name'] for d in m['version_group_details']]
                    if 'level-up' in methods or 'machine' in methods:
                        clean_name = m['move']['name'].replace("-", " ").title()
                        all_possible_moves.append(clean_name)
                
                # Sort alphabetically for easier searching
                all_possible_moves = sorted(list(set(all_possible_moves)))

                selected = st.multiselect(
                    f"Select 4 Moves for {p_data['name'].capitalize()}", 
                    options=all_possible_moves, 
                    max_selections=4, 
                    key=f"move_sel_{i}"
                )
                
                # Render Colored Badges
                move_html = '<div style="display: flex; flex-wrap: wrap;">'
                for m_display_name in selected:
                    # Convert display name back to API format to find URL
                    api_name = m_display_name.lower().replace(" ", "-")
                    m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == api_name)
                    m_info = get_move_details(m_url)
                    
                    if m_info:
                        m_type = m_info['type']['name']
                        m_power = m_info.get('power') if m_info.get('power') else "—"
                        bg = TYPE_COLORS.get(m_type, "#777")
                        
                        move_html += f'''
                            <div style="background-color:{bg}; color:white; padding:8px 12px; border-radius:10px; margin:4px; font-size:12px; font-weight:bold; min-width:150px; text-align:center; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
                                {m_display_name.upper()}<br>
                                <span style="font-size:10px; opacity:0.9;">PWR: {m_power} | {m_type.upper()}</span>
                            </div>
                        '''
                move_html += '</div>'
                st.markdown(move_html, unsafe_allow_html=True)

    st.divider()
    if st.button("Clear Full Team"):
        st.session_state['team'] = []
        st.rerun()
