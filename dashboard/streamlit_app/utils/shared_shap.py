"""Display frozen within-ANC-entry shared-predictor SHAP comparisons."""
import numpy as np
import pandas as pd
from utils.presentation import ui as st
from utils.data_loader import DashboardDataError, load_frozen_table

SOURCE = 'model_evidence/shared_shap_display.csv'
DISPLAY = ['predictor_label', 'baseline_shared_rank', 'extended_shared_rank',
           'baseline_mean_abs_shap', 'extended_mean_abs_shap', 'extended_minus_baseline']
HEADERS = {'predictor_label': 'Predictor', 'baseline_shared_rank': 'Baseline shared rank',
           'extended_shared_rank': 'Extended shared rank',
           'baseline_mean_abs_shap': 'Baseline mean absolute SHAP',
           'extended_mean_abs_shap': 'Extended mean absolute SHAP',
           'extended_minus_baseline': 'Change (extended − baseline)'}
SORTS = {'Extended shared rank': ('extended_shared_rank', True),
         'Largest increase in magnitude': ('extended_minus_baseline', False),
         'Largest decrease in magnitude': ('extended_minus_baseline', True)}

def shared_table():
    table = load_frozen_table(SOURCE)
    required = ['predictor'] + DISPLAY
    if not set(required).issubset(table.columns):
        raise DashboardDataError('Shared SHAP source is missing required fields.')
    if len(table) != 21 or table[required].isna().any().any():
        raise DashboardDataError('Expected 21 complete shared-predictor records.')
    for column in ['predictor', 'predictor_label']:
        if not table[column].is_unique or not table[column].astype(str).str.strip().ne('').all():
            raise DashboardDataError('Missing or duplicate shared-predictor identifiers.')
    if 'early_anc' in set(table.predictor):
        raise DashboardDataError('Early ANC is extended-only and cannot be a shared predictor.')
    for column in ['baseline_shared_rank', 'extended_shared_rank']:
        if not pd.api.types.is_numeric_dtype(table[column]) or set(table[column]) != set(range(1, 22)):
            raise DashboardDataError(f'Expected frozen shared ranks 1–21: {column}')
    numeric = ['baseline_mean_abs_shap', 'extended_mean_abs_shap', 'extended_minus_baseline']
    if not all(pd.api.types.is_numeric_dtype(table[c]) for c in numeric) or not np.isfinite(table[numeric].to_numpy()).all():
        raise DashboardDataError('SHAP magnitudes and changes must be finite numbers.')
    if (table[numeric[:2]] < 0).any().any():
        raise DashboardDataError('Mean absolute SHAP magnitudes must be nonnegative.')
    return table

def render_shared_shap(selected):
    contract = selected.loc[selected.visual_id.eq('P1_V5')]
    if len(contract) != 1 or contract.iloc[0].source_paths != SOURCE:
        raise DashboardDataError('Shared SHAP panel does not match the P1_V5 blueprint.')
    table = shared_table()
    st.header('5. Shared-predictor SHAP comparison')
    st.caption('Evidence population: ' + contract.iloc[0].denominator_note)
    st.markdown('Compare the **ANC-entry baseline and extended XGBoost models** on their 21 shared predictors. Early ANC initiation is excluded here because it is present only in the extended specification.')
    st.caption('Ranks are within the shared predictor set; the extended shared ranks differ from panel 4, which also includes early ANC. Other panels’ selectors do not change this comparison.')
    choice = st.selectbox('Order shared predictors by', list(SORTS), key='shared_shap_order')
    column, ascending = SORTS[choice]
    shown = table.sort_values(column, ascending=ascending, kind='stable')[DISPLAY].rename(columns=HEADERS).reset_index(drop=True)
    formats = {HEADERS[c]: '{:.0f}' for c in ['baseline_shared_rank', 'extended_shared_rank']}
    formats.update({HEADERS[c]: '{:.4f}' for c in ['baseline_mean_abs_shap', 'extended_mean_abs_shap']})
    formats[HEADERS['extended_minus_baseline']] = '{:+.4f}'
    st.dataframe(shown.style.format(formats), hide_index=True, width='stretch', height=780)
    st.caption('All 21 shared predictors shown. Positive change means a larger mean absolute SHAP magnitude in the extended model; negative change means a smaller magnitude. It does not indicate an increase or decrease in predicted ANC8+ probability.')
    st.info('Changes in SHAP magnitude do not establish mediation or causal pathways. A smaller magnitude does not prove that early ANC explains a predictor’s association with ANC8+.')
    with st.expander('Shared SHAP comparison: interpretation and source'):
        st.markdown('**Source:** `' + SOURCE + '`')
        st.markdown('**Interpretation boundary:** ' + contract.iloc[0].interpretation_boundary)
        st.markdown('Mean absolute SHAP describes contribution magnitude, not the direction of a predictor’s contribution. This source provides no uncertainty intervals for these changes.')
        st.markdown('The change column is read directly from the frozen source, not recomputed from its rounded baseline and extended values. Small apparent arithmetic differences can therefore occur. Sorting changes display order only.')
        st.caption('This is a within-ANC-entry model comparison, not a comparison with the full-cohort model in panel 3.')
