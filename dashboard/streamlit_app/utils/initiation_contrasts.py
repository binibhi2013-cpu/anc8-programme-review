"""Frozen hypothetical early-ANC model responses; no causal simulation."""
import numpy as np
import pandas as pd
from utils.presentation import ui as st
from utils.data_loader import DashboardDataError, load_frozen_table

SOURCE = 'model_evidence/initiation_contrasts.csv'
COLUMNS = ['population','algorithm','specification','weighted_mean_p_later',
           'weighted_mean_p_early','weighted_mean_difference_pp','interpretation']
HEADERS = {'population':'Population','algorithm':'Algorithm','specification':'Specification',
           'weighted_mean_p_later':'Later-initiation setting: mean probability',
           'weighted_mean_p_early':'Early-initiation setting: mean probability',
           'weighted_mean_difference_pp':'Difference (percentage points)',
           'interpretation':'Interpretation'}

def contrasts_table():
    table = load_frozen_table(SOURCE)
    if not set(COLUMNS).issubset(table.columns):
        raise DashboardDataError('Initiation contrasts are missing required fields.')
    if len(table)!=3 or table[COLUMNS].isna().any().any() or not table.algorithm.is_unique:
        raise DashboardDataError('Expected three complete, distinct algorithm contrasts.')
    if set(table.population)!={'ANC-entry'} or set(table.specification)!={'Extended'}:
        raise DashboardDataError('Expected ANC-entry extended-model contrasts.')
    if set(table.algorithm)!={'Logistic regression','Random Forest','XGBoost'}:
        raise DashboardDataError('Unexpected model in initiation contrasts.')
    numeric = ['weighted_mean_p_later','weighted_mean_p_early','weighted_mean_difference_pp']
    if not all(pd.api.types.is_numeric_dtype(table[c]) for c in numeric) or not np.isfinite(table[numeric].to_numpy()).all():
        raise DashboardDataError('Initiation contrasts must contain finite numeric values.')
    if not table[numeric[:2]].ge(0).all().all() or not table[numeric[:2]].le(1).all().all():
        raise DashboardDataError('Model probabilities must lie between 0 and 1.')
    if not table.weighted_mean_difference_pp.between(-100,100).all():
        raise DashboardDataError('Invalid percentage-point contrast.')
    if not table.interpretation.eq('Hypothetical model response; not a causal effect').all():
        raise DashboardDataError('Unexpected initiation-contrast interpretation contract.')
    return table

def render_initiation_contrasts(selected):
    contract = selected.loc[selected.visual_id.eq('P1_V7')]
    if len(contract)!=1 or contract.iloc[0].source_paths!=SOURCE:
        raise DashboardDataError('Initiation contrasts do not match the P1_V7 blueprint.')
    table = contrasts_table()
    st.header('7. Early-ANC model contrasts')
    st.caption('Evidence population: ' + contract.iloc[0].denominator_note)
    st.markdown('**ANC-entry · extended specifications.** These frozen summaries show model responses under later- and early-initiation settings. They are hypothetical model outputs, not observed outcomes for two groups of women.')
    st.dataframe(table[COLUMNS].rename(columns=HEADERS).reset_index(drop=True).style.format({
        HEADERS['weighted_mean_p_later']:'{:.4f}',
        HEADERS['weighted_mean_p_early']:'{:.4f}',
        HEADERS['weighted_mean_difference_pp']:'{:+.2f}'
    }), hide_index=True, width='stretch')
    st.caption('Probabilities use the 0–1 scale. Differences use percentage points and are copied directly from NB4; they are not recomputed from rounded probabilities. No uncertainty intervals are supplied in this table.')
    st.info('Hypothetical model response; not a causal effect. These contrasts cannot be interpreted as the expected benefit of an early-ANC intervention, a preventable fraction or observed subgroup differences.')
    with st.expander('Early-ANC contrasts: source and interpretation'):
        st.markdown('**Source:** `' + SOURCE + '`')
        st.markdown('**Interpretation boundary:** ' + contract.iloc[0].interpretation_boundary)
        st.markdown('The application reads the saved aggregate contrasts only. It does not score women, alter predictors, rerun models or generate new scenarios. The other panels’ selectors do not change these three results.')
    st.markdown('**Next: observed attendance and equity.** Use page 2 for the planned descriptive evidence, and page 3 for the planned timing and continuation evidence. Those pages currently remain development previews.')
