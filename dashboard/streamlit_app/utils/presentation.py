"""Presentation only: accessible colours, audience language and unchanged evidence values.

The UI facade delegates to Streamlit. It never changes source data, calculations,
selectors, validation or downloads. Numeric chart inputs are existing table cells.
"""
import html
import re
import pandas as pd
import plotly.graph_objects as go
import streamlit as _st
from pandas.io.formats.style import Styler

BLUE = '#155B83'
TEAL = '#087F83'
GOLD = '#B88420'
INK = '#153447'
PALETTE = [BLUE, TEAL, GOLD, '#735D91', '#5F8395']
SCALE = [[0, '#EAF3F7'], [0.5, '#62ABB6'], [1, '#155B83']]

CSS = '''
<style>
.stApp {background:#F5F8FA;color:#153447;}
[data-testid="stMainBlockContainer"] {max-width:1480px;padding-top:4.5rem;padding-bottom:4rem;}
[data-testid="stSidebar"] {background:#EAF2F6;border-right:1px solid #D5E4EB;}
h1,h2,h3 {color:#155B83!important;letter-spacing:-.025em;}
h1 {font-size:2.65rem!important;line-height:1.15!important;}
h2 {font-size:1.65rem!important;padding-top:.6rem!important;}
h3 {font-size:1.2rem!important;}
[data-testid="stCaptionContainer"] {color:#526B7A;}
[data-testid="stVerticalBlockBorderWrapper"] {background:#fff;border-color:#D4E3E9!important;border-radius:14px!important;}
[class*="st-key-anc_card_"] {background:#fff;border:1px solid #D4E3E9!important;border-top:4px solid #B88420!important;border-radius:14px!important;}
[data-testid="stExpander"] {background:#fff;border-radius:10px;}
[data-testid="stDataFrame"] {border:1px solid #D4E3E9;border-radius:10px;overflow:hidden;}
[data-testid="stAlert"] {border-radius:10px;border-left:4px solid #218A98;}
[data-testid="stMetric"] {background:#fff;border:1px solid #DAE7EC;border-top:4px solid #087F83;border-radius:12px;padding:16px;}
.anc-brand {border-top:5px solid #B88420;padding:18px 2px 10px;}
.anc-brand small {color:#155B83;font-weight:700;letter-spacing:.12em;}
.anc-brand h2 {font-size:1.5rem!important;line-height:1.2;}
.anc-cue {background:#E9F5F3;border:1px solid #BFDCD8;border-left:5px solid #087F83;border-radius:10px;padding:15px 18px;margin:4px 0 14px;}
.anc-cue .label {color:#086767;font-weight:750;font-size:.78rem;text-transform:uppercase;letter-spacing:.09em;margin-bottom:6px;}
.anc-cue p {color:#153447;line-height:1.5;margin:0;}
.anc-record {background:white;border:1px solid #D5E4EB;border-top:4px solid #B88420;border-radius:12px;padding:20px;margin:8px 0 14px;}
.anc-record h3 {margin:0 0 12px;color:#155B83;}
.anc-record p {margin:.5rem 0;line-height:1.55;}
.anc-record strong {color:#155B83;}
[data-testid="stTabs"] [role="tablist"] {gap:6px;flex-wrap:wrap;height:auto;overflow:visible;padding-bottom:10px;}
[data-testid="stTabs"] [role="tab"] {background:#E5EEF3;border-radius:8px;padding:8px 13px;height:auto;color:#155B83;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {background:#155B83;color:white;}
[data-testid="stSelectbox"] {background:#E9F5F3;border:1px solid #BEDAD7;border-radius:10px;padding:10px 12px;margin:5px 0 10px;}
@media(max-width:700px){h1{font-size:2rem!important;}[data-testid="stMainBlockContainer"]{padding:1rem;}}
@media print {[data-testid="stSidebar"],header{display:none!important;}.stApp{background:white;}}
</style>
'''

CUES = {
 '1. Final ANC attendance profile': 'Which attendance groups warrant closer service review? Check access to first contact separately from support for completing later contacts.',
 '2. National ANC pathway': 'Which conditional stage warrants follow-up? Check the eligible population for each stage before discussing possible service gaps.',
 '3. Wealth equity': 'Does the selected indicator suggest an equity gap that merits local investigation? Consider uncertainty and verify financial, service-access and other barriers before choosing a response.',
 '4. Travel-time equity': 'Where might access arrangements need review? Explore local transport, outreach and referral conditions; the observed pattern alone does not identify its cause.',
 '5. Regional equity map': 'Which regional patterns need a closer look? Read the confidence intervals and denominators alongside local service information before setting priorities.',
 '6. Regional diagnostic table': 'Is the regional pattern more consistent with an entry, timing or continuation concern? Review indicators separately; do not combine them into a performance score.',
 '1. Early versus later initiation and ANC8+': 'Should early entry and continued attendance be reviewed together? Check local booking and follow-up processes; this comparison does not estimate the effect of changing initiation timing.',
 '2. Timing-specific ANC pathway': 'Within each timing group, which stage warrants follow-up? Keep the ANC4+ and ANC8+-among-ANC4+ denominators distinct.',
 '3. Regional timing and continuation synthesis': 'Which regions merit a joint review of initiation timing and continued attendance? Confirm the pattern using local service evidence before selecting an action.',
 '1. Programme review brief': 'Select a review domain, examine its evidence and caution, then identify the local information needed to decide whether action is warranted.',
 '2. Core programme review matrix': 'Use the listed review focus to structure discussion. Assign a team to verify the local evidence before adopting a programme response.',
 '3. Contextual overlays': 'Which contextual explanation needs testing locally? Treat these signals as prompts for investigation, not established causes.',
 '4. Programme guidance register': 'Check the original guidance, its date and applicability before using it in a local decision. The register provides context, not new estimates of programme benefit.',
 '5. Regional review cues': 'Choose a region and take its review question to the local team. Record the evidence needed, a responsible person and a review date before agreeing an action.',
}

def audience_text(value):
    """Translate development references in narrative only; preserve analytical meaning."""
    if not isinstance(value, str):
        return value
    if 'Those pages currently remain development previews' in value:
        return '**Continue the review:** use Attendance and equity, Timing and continuation, then Programme review in the page menu.'
    value=value.replace('What Notebook 4 shows','What the evidence shows').replace('Observed Notebook 4 pattern','Observed pattern').replace('Relevant Notebook 4 signals','Relevant evidence')
    value = re.sub(r'frozen Notebook [24] (?:outputs|package|evidence package)', 'verified analytical evidence', value, flags=re.I)
    value = re.sub(r'Notebook [24]|\bNB[24]\b', 'the verified analysis', value)
    value = value.replace('the the verified analysis', 'the verified analysis')
    value = value.replace('frozen the verified analysis', 'verified analytical')
    value = value.replace('exact frozen values and source', 'detailed evidence and source')
    value = value.replace('frozen ', 'saved ')
    return value

def cue(text):
    _st.markdown('<div class="anc-cue"><div class="label">Decision cue · for local review</div><p>'
                 + html.escape(audience_text(text)) + '</p></div>', unsafe_allow_html=True)

def apply_theme():
    _st.markdown(CSS, unsafe_allow_html=True)
    _st.session_state['_anc_card_index']=0

def style_figure(figure):
    """Copy before styling so analytical builders remain deterministic."""
    fig = go.Figure(figure)
    fig.update_layout(template='plotly_white', colorway=PALETTE, paper_bgcolor='white',
                      plot_bgcolor='white', font=dict(family='Arial, sans-serif',size=14,color=INK),
                      hoverlabel=dict(bgcolor='white',font_size=14),
                      legend=dict(orientation='h',y=-.22,x=0), margin=dict(t=30,b=80))
    fig.update_xaxes(gridcolor='#E4EDF2', zerolinecolor='#A7BDC8',automargin=True)
    fig.update_yaxes(gridcolor='#E4EDF2', zerolinecolor='#A7BDC8',automargin=True)
    for i,trace in enumerate(fig.data):
        if trace.type in ('bar','scatter'):
            trace.update(marker_color=PALETTE[i % len(PALETTE)])
            for axis in ('error_x','error_y'):
                if getattr(trace, axis, None) and getattr(trace, axis).array is not None:
                    trace.update(**{axis:dict(color=INK,thickness=1.5,width=4)})
        elif trace.type=='heatmap':
            trace.update(colorscale=SCALE)
        elif trace.type=='choropleth' and trace.showscale is not False:
            trace.update(colorscale=SCALE)
    return fig

def comparison_chart(frame):
    """Supplement three model tables using only supplied values; return None otherwise."""
    if {'Paired estimate','CI lower','CI upper','Metric','Algorithm'}.issubset(frame):
        labels=frame['Algorithm']+' · '+frame['Metric']
        fig=go.Figure(go.Scatter(x=frame['Paired estimate'],y=labels,mode='markers',
            marker=dict(size=10),error_x=dict(type='data',symmetric=False,
                array=frame['CI upper']-frame['Paired estimate'],
                arrayminus=frame['Paired estimate']-frame['CI lower']),
            customdata=frame[['CI lower','CI upper']],
            hovertemplate='%{y}<br>Estimate %{x:+.4f}<br>95% CI %{customdata[0]:+.4f} to %{customdata[1]:+.4f}<extra></extra>'))
        fig.add_vline(x=0,line_dash='dash',line_color='#7D8D95')
        fig.update_layout(height=max(300,len(frame)*40+120),xaxis_title='Paired difference · original metric scale',yaxis_title=None)
        fig.update_yaxes(autorange='reversed')
        return fig, 'Points and 95% confidence intervals show the supplied paired comparisons. The dashed line marks no difference; the three metrics remain distinct.'
    if {'Category','Weighted mean signed SHAP'}.issubset(frame):
        values=frame['Weighted mean signed SHAP']
        fig=go.Figure(go.Bar(x=values,y=frame['Category'],orientation='h',
            customdata=frame[['Women (n)']],
            hovertemplate='%{y}<br>Signed contribution: %{x:+.4f}<br>Women: %{customdata[0]:,.0f}<extra></extra>'))
        fig.add_vline(x=0,line_color=INK,line_width=1)
        fig.update_layout(height=max(310,len(frame)*36+120),yaxis_autorange='reversed',
            xaxis_title='Weighted mean signed SHAP · model output scale',yaxis_title=None)
        return fig, 'Bars show signed model contributions. Positive and negative directions are not intervention effects or subgroup outcome rates. No uncertainty intervals are supplied.'
    ranks=[c for c in frame if 'rank' in c.lower()]
    if 'Predictor' in frame and len(ranks)==4:
        fig=go.Figure(go.Heatmap(z=frame[ranks].to_numpy(),x=['Logistic\npermutation','Random Forest\npermutation','XGBoost\npermutation','XGBoost\nSHAP'],
            y=frame['Predictor'],zmin=1,zmax=len(frame),reversescale=True,
            text=frame[ranks].to_numpy(),texttemplate='%{text:.0f}',xgap=3,ygap=2,
            hovertemplate='%{y}<br>%{x}: rank %{z}<extra></extra>',colorbar=dict(title='Rank')))
        fig.update_layout(height=max(580,len(frame)*27+100),xaxis_side='top',yaxis_autorange='reversed')
        return fig, 'Darker cells indicate a higher within-model rank (1 is highest). Rankings are separate summaries; no combined score or causal importance is implied.'
    cols=['Baseline mean absolute SHAP','Extended mean absolute SHAP']
    if 'Predictor' in frame and set(cols).issubset(frame):
        fig=go.Figure()
        for _,row in frame.iterrows():
            fig.add_trace(go.Scatter(x=[row[cols[0]],row[cols[1]]],y=[row['Predictor']]*2,mode='lines',line=dict(color='#BDD0D9',width=2),showlegend=False,hoverinfo='skip'))
        for j,c in enumerate(cols):
            fig.add_trace(go.Scatter(x=frame[c],y=frame.Predictor,mode='markers',name=c,marker=dict(size=9,symbol=['circle','diamond'][j]),hovertemplate='%{y}<br>%{x:.4f}<extra>%{fullData.name}</extra>'))
        fig.update_layout(height=max(580,len(frame)*26+130),xaxis_title='Mean absolute SHAP · supplied magnitude',yaxis_autorange='reversed')
        return fig, 'Circles show baseline and diamonds show extended-model magnitudes. Connecting segments show the two saved values, not causal pathways or uncertainty intervals.'
    return None

class PolicyUI:
    """A small, explicit presentation boundary, not a global Streamlit patch."""
    def __getattr__(self,name):
        return getattr(_st,name)

    def header(self,text,*args,**kwargs):
        result=_st.header(audience_text(text),*args,**kwargs)
        if text in CUES:
            cue(CUES[text])
        return result

    def caption(self,text,*args,**kwargs):
        if isinstance(text,str) and any(x in text.lower() for x in ['development preview','page structure preview','all four pages implemented','displays are implemented']):
            return None
        return _st.caption(audience_text(text),*args,**kwargs)

    def markdown(self,text,*args,**kwargs):
        return _st.markdown(audience_text(text),*args,**kwargs)

    def write(self,*args,**kwargs):
        return _st.write(*(audience_text(x) for x in args),**kwargs)

    def info(self,text,*args,**kwargs):
        return _st.info(audience_text(text),*args,**kwargs)

    def warning(self,text,*args,**kwargs):
        return _st.warning(audience_text(text),*args,**kwargs)

    def expander(self,label,*args,**kwargs):
        return _st.expander(audience_text(label),*args,**kwargs)

    def decision_cue(self,text):
        # The caller supplies the existing source review question, verbatim apart from audience wording.
        cue(text)

    def container(self,*args,**kwargs):
        if kwargs.get('border') and 'key' not in kwargs:
            index=_st.session_state.get('_anc_card_index',0)
            _st.session_state['_anc_card_index']=index+1
            kwargs['key']=f'anc_card_{index}'
        return _st.container(*args,**kwargs)

    def plotly_chart(self,figure,*args,**kwargs):
        kwargs.pop('use_container_width',None)
        kwargs.setdefault('width','stretch')
        if kwargs.get('key')=='attendance_profile_chart':
            trace=figure.data[0]
            for col,label,value,details in zip(_st.columns(4),trace.x,trace.y,trace.customdata):
                with col:
                    _st.metric('ANC contacts: '+str(label),f'{value:.1f}%',
                               help=f'Weighted percentage in the resolved analytical population. 95% CI {details[0]:.1f}–{details[1]:.1f}%; unweighted n={int(details[2]):,}.')
            _st.caption('Weighted attendance distribution · the chart below shows the same values and their 95% confidence intervals.')
        return _st.plotly_chart(style_figure(figure),*args,**kwargs)

    def dataframe(self,data,*args,**kwargs):
        # Retain existing formatters and the untouched dataframe for source inspection.
        frame=data.data if isinstance(data,Styler) else data
        if not isinstance(frame,pd.DataFrame):
            return _st.dataframe(data,*args,**kwargs)
        styler=data if isinstance(data,Styler) else frame.style
        def stripes(row):
            index=frame.index.get_loc(row.name)
            return ['background-color: '+('#EEF5F8' if index%2==0 else '#FFFFFF')+'; color: #153447']*len(row)
        styler=styler.apply(stripes,axis=1)
        for col in frame.select_dtypes(include='number'):
            if 'rank' in col.lower():
                styler=styler.background_gradient(cmap='Blues_r',subset=[col],vmin=1,vmax=max(2,len(frame)))
        kwargs.pop('use_container_width',None)
        kwargs.setdefault('width','stretch')
        chart=comparison_chart(frame)
        if chart:
            figure,explanation=chart
            self.plotly_chart(figure)
            self.caption(explanation)
            with _st.expander('Detailed values · '+('paired comparisons' if 'Paired estimate' in frame else 'predictor evidence')):
                return _st.dataframe(styler,*args,**kwargs)
        # Regional narrative fields become readable cards; the exact source remains available.
        if 'Region' in frame and len(frame.select_dtypes(include='number').columns)==0 and len(frame.columns)>1:
            for _,row in frame.iterrows():
                body=''.join('<p><strong>'+html.escape(audience_text(str(k)))+'</strong><br>'+html.escape(audience_text(str(v)))+'</p>' for k,v in row.items() if k not in ['Region','Programme-review question'])
                with _st.expander(str(row['Region']),expanded=len(frame)==1):
                    _st.markdown('<div class="anc-record">'+body+'</div>',unsafe_allow_html=True)
                    if 'Programme-review question' in row:
                        cue(str(row['Programme-review question']))
            with _st.expander('Detailed source records'):
                return _st.dataframe(styler,*args,**kwargs)
        return _st.dataframe(styler,*args,**kwargs)

ui=PolicyUI()
