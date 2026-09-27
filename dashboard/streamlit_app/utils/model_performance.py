"""First Page 1 display: frozen held-out model performance."""
import pandas as pd
from utils.presentation import ui as st
from utils.data_loader import DashboardDataError, load_frozen_table, load_specifications
from utils.paired_performance import render_paired_performance
from utils.full_cohort_predictors import render_full_cohort_predictors
from utils.entry_extended_predictors import render_entry_extended_predictors
from utils.shared_shap import render_shared_shap
from utils.shap_direction import render_shap_direction
from utils.initiation_contrasts import render_initiation_contrasts
SOURCE = 'model_evidence/nb4_performance_panel.csv'
KEYS = ['Population', 'Algorithm', 'Specification']
DISPLAY = KEYS + ['AP (95% CI)', 'AUROC (95% CI)', 'Weighted Brier', 'CITL', 'Calibration slope']
NUMERIC = ['Weighted AP', 'AP CI lower', 'AP CI upper', 'Weighted AUROC', 'AUROC CI lower', 'AUROC CI upper', 'Weighted Brier', 'CITL', 'Calibration slope']

def performance_table():
    table = load_frozen_table(SOURCE)
    missing = sorted(set(DISPLAY + NUMERIC) - set(table.columns))
    if missing:
        raise DashboardDataError(f'Performance panel is missing columns: {missing}')
    if table.empty or table.duplicated(KEYS).any() or table[KEYS].isna().any().any():
        raise DashboardDataError('Performance panel has empty, missing or duplicate model identifiers.')
    for name in NUMERIC:
        if not pd.api.types.is_numeric_dtype(table[name]):
            raise DashboardDataError(f'Performance field must be numeric: {name}')
    return table

def render_model_evidence():
    st.caption('ANC8+ Programme Review · Page 1 of 4')
    st.title('Model evidence')
    st.markdown('### What predictive signals led to the programme deep dives?')
    st.info('Predictive performance, model prominence and SHAP describe model behaviour. They do not establish causal effects.')
    st.caption('Development preview · all seven Model evidence panels are implemented. Pages 2–4 remain development previews.')
    try:
        st.caption('Choose a view below. Filters apply to the view where they appear; estimates and eligible populations remain unchanged.')
        evidence_tabs = st.tabs(['Performance', 'Paired comparison', 'Full cohort', 'ANC-entry', 'Shared predictors', 'Direction', 'Model contrasts'])
        with evidence_tabs[0]:
            table = performance_table()
            visuals = load_specifications()['visual']
            selected = visuals.loc[visuals['page_order'].eq('1')].copy()
            selected['display_order'] = selected['visual_order'].astype(int)
            selected = selected.sort_values('display_order')
            panel_spec = selected.loc[selected['visual_id'].eq('P1_V1')]
            if len(panel_spec) != 1 or panel_spec.iloc[0]['source_paths'] != SOURCE:
                raise DashboardDataError('Performance panel does not match the approved P1_V1 blueprint.')
            contract = panel_spec.iloc[0]
            st.header('1. Held-out model performance')
            st.caption('Evidence population: ' + contract['denominator_note'])
            st.markdown('Select a population first. The full-cohort and ANC-entry panels describe different evaluation populations and should be interpreted separately.')
            population = st.selectbox('Evaluation population', table['Population'].drop_duplicates().tolist(), key='performance_population')
            population_table = table.loc[table['Population'].eq(population)]
            algorithm = st.selectbox('Algorithm', ['All algorithms'] + population_table['Algorithm'].drop_duplicates().tolist(), key=f'performance_algorithm_{population}')
            available = population_table if algorithm == 'All algorithms' else population_table.loc[population_table['Algorithm'].eq(algorithm)]
            specification = st.selectbox('Model specification', ['All specifications'] + available['Specification'].drop_duplicates().tolist(), key=f'performance_specification_{population}_{algorithm}')
            shown = available if specification == 'All specifications' else available.loc[available['Specification'].eq(specification)]
            st.caption(f'{len(shown)} model results shown · estimates and confidence intervals are frozen NB4 values.')
            st.dataframe(shown[DISPLAY].reset_index(drop=True).style.format({'Weighted Brier': '{:.3f}', 'CITL': '{:.3f}', 'Calibration slope': '{:.3f}'}, na_rep='Not available'), hide_index=True, width='stretch')
            st.caption('AP and AUROC retain the source’s 95% confidence-interval text. Brier and calibration measures are rounded for display only; their confidence intervals are not supplied in this table.')
            with st.expander('How to read these measures'):
                st.markdown('- **AP:** average precision; depends on the outcome prevalence in the evaluation population.\n- **AUROC:** discrimination across classification thresholds.\n- **Brier score:** overall probabilistic prediction error; lower values indicate less error.\n- **CITL:** calibration-in-the-large; the reference value is 0.\n- **Calibration slope:** the reference value is 1.')
                st.markdown('No model is designated a winner here. Baseline–extended uncertainty is shown in the paired-performance panel below.')
            with st.expander('Evidence source and interpretation'):
                st.markdown('**Source:** `' + SOURCE + '`')
                st.markdown('**Interpretation boundary:** ' + contract['interpretation_boundary'])
                st.markdown('Source integrity is checked against the frozen NB4 manifest. Filters select existing rows; no estimates or confidence intervals are recalculated.')
        with evidence_tabs[1]:
            render_paired_performance(selected)
        with evidence_tabs[2]:
            render_full_cohort_predictors(selected)
        with evidence_tabs[3]:
            render_entry_extended_predictors(selected)
        with evidence_tabs[4]:
            render_shared_shap(selected)
        with evidence_tabs[5]:
            render_shap_direction(selected)
        with evidence_tabs[6]:
            render_initiation_contrasts(selected)
    except (DashboardDataError, OSError, KeyError, ValueError) as exc:
        st.error('The performance evidence could not be displayed. Please contact the dashboard maintainer.')
        with st.expander('Validation details'):
            st.code(str(exc))
        st.stop()
