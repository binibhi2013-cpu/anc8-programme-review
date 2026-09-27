"""Display frozen paired comparisons without recomputing differences or intervals."""
import numpy as np
import pandas as pd
from utils.presentation import ui as st
from utils.data_loader import DashboardDataError, load_frozen_table

SOURCE = 'model_evidence/paired_performance.csv'
COLUMNS = ['population', 'Algorithm', 'Metric', 'Point_estimate', 'CI_lower', 'CI_upper', 'CI_excludes_zero']
LABELS = {'Delta_AP': 'AP difference (extended − baseline)',
          'Delta_AUROC': 'AUROC difference (extended − baseline)',
          'Brier_improvement': 'Brier improvement (baseline − extended)'}
HEADERS = {'population': 'Population', 'Point_estimate': 'Paired estimate',
           'CI_lower': 'CI lower', 'CI_upper': 'CI upper', 'CI_excludes_zero': 'CI excludes zero'}

def paired_table():
    table = load_frozen_table(SOURCE)
    if not set(COLUMNS + ['source_file']).issubset(table.columns):
        raise DashboardDataError('Paired performance source is missing required columns.')
    if table.empty or table[COLUMNS].isna().any().any() or table.duplicated(['population', 'Algorithm', 'Metric']).any():
        raise DashboardDataError('Paired comparisons contain missing values or duplicate identifiers.')
    if set(table.population) != {'ANC-entry'} or set(table.Metric) != set(LABELS):
        raise DashboardDataError('Unexpected paired population or metric definitions.')
    values = table[['Point_estimate', 'CI_lower', 'CI_upper']]
    if not all(pd.api.types.is_numeric_dtype(values[c]) for c in values) or not np.isfinite(values.to_numpy()).all():
        raise DashboardDataError('Paired estimates and interval bounds must be finite numbers.')
    if not (table.CI_lower <= table.CI_upper).all():
        raise DashboardDataError('Paired confidence-interval bounds are reversed.')
    if not pd.api.types.is_bool_dtype(table.CI_excludes_zero):
        raise DashboardDataError('CI_excludes_zero must contain boolean values.')
    # Consistency check only; the displayed flag remains the frozen source flag.
    expected = (table.CI_lower > 0) | (table.CI_upper < 0)
    if not table.CI_excludes_zero.eq(expected).all():
        raise DashboardDataError('Frozen interval flags disagree with their bounds.')
    return table

def display_table(table):
    shown = table[COLUMNS].copy()
    shown['Metric'] = shown['Metric'].map(LABELS)
    shown['CI_excludes_zero'] = shown['CI_excludes_zero'].map({True: 'Yes', False: 'No'})
    return shown.rename(columns=HEADERS).reset_index(drop=True)

def render_paired_performance(selected):
    contract = selected.loc[selected.visual_id.eq('P1_V2')]
    if len(contract) != 1 or contract.iloc[0].source_paths != SOURCE:
        raise DashboardDataError('Paired panel does not match the P1_V2 blueprint.')
    table = paired_table()
    st.header('2. Paired baseline–extended performance comparison')
    st.caption('Evidence population: ' + contract.iloc[0].denominator_note)
    st.markdown('**ANC-entry only.** The extended specification adds early ANC. Positive values favour the extended specification for all three measures. These selectors apply only to this panel.')
    algorithm = st.selectbox('Paired comparison algorithm', ['All algorithms'] + table.Algorithm.drop_duplicates().tolist(), key='paired_algorithm')
    metric = st.selectbox('Paired comparison metric', ['All metrics'] + list(LABELS), format_func=lambda x: LABELS.get(x, x), key='paired_metric')
    shown = table
    if algorithm != 'All algorithms':
        shown = shown.loc[shown.Algorithm.eq(algorithm)]
    if metric != 'All metrics':
        shown = shown.loc[shown.Metric.eq(metric)]
    st.caption(f'{len(shown)} frozen paired comparisons shown. Values are on the original metric scale, not percentage points.')
    st.dataframe(display_table(shown).style.format({
        'Paired estimate': '{:+.4f}', 'CI lower': '{:+.4f}', 'CI upper': '{:+.4f}'
    }), hide_index=True, width='stretch')
    if not shown.CI_excludes_zero.any():
        st.info('Every displayed confidence interval includes zero. The paired comparisons do not clearly establish a performance improvement; this does not prove that the specifications are equivalent.')
    with st.expander('Paired comparison: definitions and source'):
        st.markdown('- **AP difference:** extended AP minus baseline AP.\n- **AUROC difference:** extended AUROC minus baseline AUROC.\n- **Brier improvement:** baseline Brier minus extended Brier, because lower Brier scores are better.')
        st.markdown('**Source:** `' + SOURCE + '`')
        st.markdown('**Interpretation boundary:** ' + contract.iloc[0].interpretation_boundary)
        st.markdown('Paired estimates, interval bounds and zero-exclusion flags are read directly from NB4. They are not derived from the rounded values or separate confidence intervals in panel 1.')
        st.caption('Upstream provenance retained in the frozen table: ' + '; '.join(table.source_file.drop_duplicates()))
