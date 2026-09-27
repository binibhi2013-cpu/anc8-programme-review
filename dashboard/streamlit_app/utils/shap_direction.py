"""Display frozen category-level signed SHAP summaries."""
import numpy as np
import pandas as pd
from utils.presentation import ui as st
from utils.data_loader import DashboardDataError, load_frozen_table

SOURCE = 'model_evidence/nb4_shap_direction_panel.csv'
DISPLAY = ['population', 'algorithm', 'predictor_label', 'category', 'n_women',
           'weighted_mean_signed_shap', 'SHAP direction']
HEADERS = {'population':'Population', 'algorithm':'Algorithm', 'predictor_label':'Predictor',
           'category':'Category', 'n_women':'Women (n)',
           'weighted_mean_signed_shap':'Weighted mean signed SHAP'}

def direction_table():
    table = load_frozen_table(SOURCE)
    required = ['predictor'] + DISPLAY
    if not set(required).issubset(table.columns):
        raise DashboardDataError('SHAP direction source is missing required fields.')
    if table.empty or table[required].isna().any().any() or table.duplicated(['population','algorithm','predictor','category']).any():
        raise DashboardDataError('SHAP direction source has missing values or duplicate categories.')
    if set(table.algorithm) != {'XGBoost'}:
        raise DashboardDataError('Expected frozen XGBoost direction evidence.')
    for column in ['n_women','weighted_mean_signed_shap']:
        if not pd.api.types.is_numeric_dtype(table[column]) or not np.isfinite(table[column].to_numpy()).all():
            raise DashboardDataError(f'Expected finite numeric values: {column}')
    if (table.n_women <= 0).any() or (table.n_women % 1 != 0).any():
        raise DashboardDataError('Category counts must be positive integers.')
    signs = table.weighted_mean_signed_shap
    positive = table['SHAP direction'].eq('Positive contribution')
    negative = table['SHAP direction'].eq('Negative contribution')
    if not (positive | negative).all() or not ((positive & signs.gt(0)) | (negative & signs.lt(0))).all():
        raise DashboardDataError('Frozen SHAP direction labels disagree with signed values.')
    mapping = table[['predictor','predictor_label','population','algorithm']].drop_duplicates()
    if not mapping.predictor.is_unique or not mapping.predictor_label.is_unique:
        raise DashboardDataError('Predictor labels must resolve to one population/model.')
    return table

def render_shap_direction(selected):
    contract = selected.loc[selected.visual_id.eq('P1_V6')]
    if len(contract)!=1 or contract.iloc[0].source_paths!=SOURCE:
        raise DashboardDataError('SHAP direction panel does not match the P1_V6 blueprint.')
    table = direction_table()
    st.header('6. Selected SHAP direction')
    st.caption('Evidence context: ' + contract.iloc[0].denominator_note)
    predictor = st.selectbox('Predictor for signed SHAP', table.predictor_label.drop_duplicates().tolist(), key='shap_direction_predictor')
    shown = table.loc[table.predictor_label.eq(predictor)]
    st.markdown(f"**Population: {shown.iloc[0].population} · Model: {shown.iloc[0].algorithm}**")
    st.caption('This population follows the selected predictor in the frozen source. Early ANC uses ANC-entry evidence; the other available predictors use full-cohort evidence. Controls in other panels do not change this table.')
    st.dataframe(shown[DISPLAY].rename(columns=HEADERS).reset_index(drop=True).style.format({
        'Women (n)':'{:.0f}', 'Weighted mean signed SHAP':'{:+.4f}'
    }), hide_index=True, width='stretch')
    st.info('Signed SHAP values are model contributions, not subgroup ANC8+ rates, probability changes or intervention effects. The sign describes contribution direction on the model output scale; it does not establish a causal effect.')
    with st.expander('Signed SHAP: interpretation and source'):
        st.markdown('Positive and negative values indicate opposite directions of contribution relative to the model’s SHAP reference. The table reports category-level weighted mean signed contributions, not the contribution of every woman in that category.')
        st.markdown('Women (n) is the frozen category count supporting the summary. It is not a weighted population total or an ANC8+ numerator. No uncertainty intervals are supplied in this source.')
        st.markdown('**Source:** `' + SOURCE + '`')
        st.markdown('**Interpretation boundary:** ' + contract.iloc[0].interpretation_boundary)
        st.caption('Category order, counts, signed values and direction labels are preserved from NB4. No SHAP values, subgroup estimates or category averages are recalculated.')
