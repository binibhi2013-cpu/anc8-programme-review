"""Present frozen ANC-entry extended predictor evidence without recomputing rankings."""
import numpy as np
import pandas as pd
from utils.presentation import ui as st
from utils.data_loader import DashboardDataError, load_frozen_table

SOURCE = 'model_evidence/entry_extended_model_evidence.csv'
RANKS = ['Logistic permutation rank', 'RF permutation rank', 'XGB permutation rank', 'XGB SHAP rank']
DISPLAY = ['predictor_label'] + RANKS + ['XGB mean |SHAP|']
SORT_LABELS = {
    'XGB SHAP rank': 'XGBoost · SHAP rank',
    'Logistic permutation rank': 'Logistic regression · permutation rank',
    'RF permutation rank': 'Random Forest · permutation rank',
    'XGB permutation rank': 'XGBoost · permutation rank',
}
HEADERS = {'predictor_label': 'Predictor',
           'Logistic permutation rank': 'Logistic regression permutation rank',
           'RF permutation rank': 'Random Forest permutation rank',
           'XGB permutation rank': 'XGBoost permutation rank',
           'XGB SHAP rank': 'XGBoost SHAP rank',
           'XGB mean |SHAP|': 'XGBoost mean absolute SHAP'}

def entry_extended_table():
    table = load_frozen_table(SOURCE)
    required = ['predictor'] + DISPLAY
    if not set(required).issubset(table.columns):
        raise DashboardDataError('ANC-entry extended predictor evidence is missing required columns.')
    if len(table) != 22 or table[required].isna().any().any():
        raise DashboardDataError('Expected 22 complete ANC-entry extended predictor records.')
    for column in ['predictor', 'predictor_label']:
        if not table[column].is_unique or not table[column].astype(str).str.strip().ne('').all():
            raise DashboardDataError(f'Missing or duplicate predictor identifier: {column}')
    for column in RANKS:
        if not pd.api.types.is_numeric_dtype(table[column]) or set(table[column]) != set(range(1, 23)):
            raise DashboardDataError(f'Expected frozen ranks 1–22 without duplicates: {column}')
    magnitude = table['XGB mean |SHAP|']
    if not pd.api.types.is_numeric_dtype(magnitude) or not np.isfinite(magnitude.to_numpy()).all() or (magnitude < 0).any():
        raise DashboardDataError('Mean absolute SHAP must contain finite nonnegative values.')
    if 'early_anc' not in set(table['predictor']):
        raise DashboardDataError('Extended predictor source must include early ANC initiation.')
    return table

def render_entry_extended_predictors(selected):
    contract = selected.loc[selected.visual_id.eq('P1_V4')]
    if len(contract) != 1 or contract.iloc[0].source_paths != SOURCE:
        raise DashboardDataError('ANC-entry extended predictor panel does not match the P1_V4 blueprint.')
    table = entry_extended_table()
    st.header('4. ANC-entry extended predictor evidence')
    st.caption('Evidence population: ' + contract.iloc[0].denominator_note)
    st.markdown('Compare the frozen model-specific rankings. **Rank 1 is the highest-ranked predictor within that model and method.** This panel always shows ANC-entry extended evidence; the population and algorithm selectors above apply to their own panels.')
    rank = st.selectbox('Order ANC-entry extended predictors by', list(SORT_LABELS),
                        format_func=lambda name: SORT_LABELS[name], key='entry_extended_rank')
    shown = table.sort_values(rank, kind='stable')[DISPLAY].rename(columns=HEADERS).reset_index(drop=True)
    st.caption('All 22 predictors shown · ordering changes only the display; the frozen ranks and SHAP values remain unchanged.')
    formats = {HEADERS[column]: '{:.0f}' for column in RANKS}
    formats[HEADERS['XGB mean |SHAP|']] = '{:.4f}'
    st.dataframe(shown.style.format(formats), hide_index=True, width='stretch', height=780)
    st.caption('Extended specification: includes early ANC initiation. Panel 3 uses a different population/model; the raw SHAP magnitudes across these panels are not a measure of the effect of adding early ANC. The next shared-predictor panel provides the specified within-ANC-entry comparison.')
    st.info('Model prominence is not causal importance. Mean absolute SHAP describes magnitude, not whether a predictor increases or decreases predictions. These values are not outcome percentages or intervention effects.')
    with st.expander('Predictor rankings: methods and source'):
        st.markdown('Permutation ranks are presented separately for logistic regression, Random Forest and XGBoost. The SHAP rank and mean absolute SHAP column apply only to XGBoost. They are different summaries; no average or combined importance score is calculated.')
        st.markdown('This source supplies rankings and XGBoost SHAP magnitudes, but no uncertainty intervals for them. Rank differences do not establish statistically distinct importance.')
        st.markdown('**Source:** `' + SOURCE + '`')
        st.markdown('**Interpretation boundary:** ' + contract.iloc[0].interpretation_boundary)
        st.caption('The NB4 manifest is checked before loading. No model is refitted and no permutation or SHAP quantity is recomputed.')
