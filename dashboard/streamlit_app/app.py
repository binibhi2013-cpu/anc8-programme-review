"""ANC8+ Programme Review: verified evidence for structured programme discussion."""
import streamlit as st
from utils.presentation import apply_theme
from utils.data_loader import DashboardDataError, validate_dashboard_inputs

st.set_page_config(page_title="ANC8+ | Programme Review",page_icon="🇪🇹",layout="wide")
apply_theme()
try:
    validate_dashboard_inputs()
except (DashboardDataError,OSError,ValueError) as exc:
    st.error("The evidence could not be verified. Please contact the dashboard maintainer.")
    with st.expander("Technical validation details"):
        st.code(str(exc))
    st.stop()

st.sidebar.markdown('<div class="anc-brand"><small>ETHIOPIA · MATERNAL HEALTH</small><h2>ANC8+<br>Programme Review</h2></div>',unsafe_allow_html=True)
st.sidebar.caption("Evidence to support equitable, people-centred service review.")
st.sidebar.markdown("**Start with the programme question.** Explore attendance and equity, examine timing and continuation, then use the review cues to guide local discussion.")
with st.sidebar.expander("Read the evidence correctly",expanded=False):
    st.markdown("- **ANC:** antenatal care. ANC4+ and ANC8+ mean at least four and eight contacts.\n- **95% CI:** confidence interval, showing statistical uncertainty.\n- **Weighted %:** survey-weighted estimate; **n** is an unweighted count.\n- Each indicator has its own eligible population.\n- Observed differences and model signals do not establish causal effects.")
    st.caption("Contested geography has no analytical estimate. Colours are not service targets or a regional ranking.")
st.sidebar.caption("Source: verified, saved study evidence. Model findings describe prediction, not programme effects.")
page=st.navigation([
    st.Page("pages/1_Model_Evidence.py",title="1 · Model evidence",default=True),
    st.Page("pages/2_Attendance_and_Equity.py",title="2 · Attendance and equity"),
    st.Page("pages/3_Timing_and_Continuation.py",title="3 · Timing and continuation"),
    st.Page("pages/4_Programme_Review.py",title="4 · Programme review"),
])
page.run()
