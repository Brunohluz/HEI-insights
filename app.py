import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="HEI Insights | Promoções", page_icon="🎯", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {background:#f4f7f5;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#003b2c,#00573f);}
[data-testid="stSidebar"] * {color:white;}
.block-container {padding-top:1.2rem; max-width:1500px;}
.hero {background:linear-gradient(100deg,#003b2c,#08764f);padding:22px 26px;border-radius:16px;color:white;margin-bottom:14px;}
.hero h1 {margin:0;font-size:30px;}.hero p {margin:5px 0 0;opacity:.86;}
.kpi {background:white;border:1px solid #dfe8e3;border-radius:14px;padding:16px;min-height:112px;box-shadow:0 3px 12px rgba(0,0,0,.04);}
.kpi-label {font-size:13px;color:#66756d;font-weight:600}.kpi-value {font-size:27px;color:#064b36;font-weight:750;margin-top:8px}.kpi-note {font-size:12px;color:#6e7c75;margin-top:5px}
.section {font-size:19px;font-weight:750;color:#143d30;margin:16px 0 8px}
.alert {background:#fff8e7;border-left:5px solid #e7a71b;padding:13px;border-radius:8px;margin-bottom:8px;}
</style>
""", unsafe_allow_html=True)

BASE=Path(__file__).parent
@st.cache_data(show_spinner="Carregando dados de pedidos...")
def load_data():
    p=pd.read_csv(BASE/'pedidos_app.csv',sep=';',low_memory=False)
    a=pd.read_csv(BASE/'promocoes_app.csv',sep=';',low_memory=False)
    p['erp_order_date']=pd.to_datetime('1899-12-30')+pd.to_timedelta(pd.to_numeric(p['erp_order_date'],errors='coerce'),unit='D')
    p['gross_amount']=pd.to_numeric(p['gross_amount'],errors='coerce').fillna(0)
    p['discount_amount']=pd.to_numeric(p['discount_amount'],errors='coerce').fillna(0)
    p['returned_amount']=pd.to_numeric(p['returned_amount'],errors='coerce').fillna(0)
    a['MonthYear']=pd.to_datetime(a['MonthYear'],errors='coerce')
    a['Faturamento']=pd.to_numeric(a['Faturamento'],errors='coerce').fillna(0)
    a['Volume HL']=pd.to_numeric(a['Volume HL'],errors='coerce').fillna(0)
    return p,a
p,a=load_data()

with st.sidebar:
    st.markdown("## ✦ HEI INSIGHTS")
    st.caption("INTELIGÊNCIA PROMOCIONAL")
    st.markdown("---")
    pagina=st.radio("Navegação",["Central de Promoções","Detalhe da Promoção","Fechamento","Oportunidades"])
    st.markdown("---")
    st.caption("MVP com dados reais das bases fornecidas")

if pagina=="Central de Promoções":
    st.markdown('<div class="hero"><h1>Central de Promoções</h1><p>Acompanhe ações, identifique alertas e acelere os fechamentos.</p></div>',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    ops=sorted(a['Operação'].dropna().astype(str).unique())
    tipos=sorted(a['tipo_promo'].dropna().astype(str).unique())
    with c1: op=st.selectbox("Operação",["Todas"]+ops)
    with c2: tipo=st.selectbox("Tipo de promoção",["Todos"]+tipos)
    with c3: origem=st.selectbox("Origem",["Todas"]+sorted(a['order_origin'].dropna().astype(str).unique()))
    with c4: busca=st.text_input("Buscar promoção")
    af=a.copy()
    if op!='Todas': af=af[af['Operação'].astype(str)==op]
    if tipo!='Todos': af=af[af['tipo_promo'].astype(str)==tipo]
    if origem!='Todas': af=af[af['order_origin'].astype(str)==origem]
    if busca: af=af[af['promotion_name'].astype(str).str.contains(busca,case=False,na=False)]

    k1,k2,k3,k4,k5=st.columns(5)
    metrics=[('Promoções',af['promo_id'].nunique(),'Códigos promocionais únicos'),('Operações',af['Operação'].nunique(),'Com ações identificadas'),('Clientes',af['hybris_customer_id'].nunique(),'Participantes únicos'),('Faturamento',f"R$ {af['Faturamento'].sum()/1e6:.2f} mi",'Base promocional'),('Volume',f"{af['Volume HL'].sum():,.1f} HL",'Volume das ações')]
    for col,(lab,val,note) in zip([k1,k2,k3,k4,k5],metrics):
        col.markdown(f'<div class="kpi"><div class="kpi-label">{lab}</div><div class="kpi-value">{val}</div><div class="kpi-note">{note}</div></div>',unsafe_allow_html=True)

    st.markdown('<div class="section">Ranking por operação</div>',unsafe_allow_html=True)
    # Ranking une promoções da base Export com pedidos da base principal.
    rankpromo=af.groupby(['OV','Operação'],dropna=False).agg(Promocoes=('promo_id','nunique'),Clientes_promocao=('hybris_customer_id','nunique'),Faturamento_promocional=('Faturamento','sum')).reset_index()
    pf=p[p['order_status'].eq('APROVADO')].copy()
    pf['Mes']=pf['erp_order_date'].dt.to_period('M').astype(str)
    orderop=pf.groupby(['sales_org_id','OV Desc2'],dropna=False).agg(Ultimo_pedido=('erp_order_date','max'),Pedidos_total=('erp_order_id','nunique')).reset_index()
    monthly=pf.pivot_table(index=['sales_org_id','OV Desc2'],columns='Mes',values='erp_order_id',aggfunc=pd.Series.nunique,fill_value=0).reset_index()
    orderop=orderop.merge(monthly,on=['sales_org_id','OV Desc2'],how='left')
    ranking=rankpromo.merge(orderop,left_on=['OV','Operação'],right_on=['sales_org_id','OV Desc2'],how='outer')
    ranking['Operação']=ranking['Operação'].fillna(ranking['OV Desc2'])
    ranking['OV']=ranking['OV'].fillna(ranking['sales_org_id'])
    ranking['Promocoes']=ranking['Promocoes'].fillna(0).astype(int)
    ranking['Clientes_promocao']=ranking['Clientes_promocao'].fillna(0).astype(int)
    ranking['Pedidos_total']=ranking['Pedidos_total'].fillna(0).astype(int)
    ranking['Ultimo_pedido']=pd.to_datetime(ranking['Ultimo_pedido']).dt.strftime('%d/%m/%Y')
    months=sorted([c for c in ranking.columns if c[:4].isdigit()],reverse=True)
    show=['OV','Operação','Promocoes','Ultimo_pedido','Pedidos_total']+months
    rename={'OV':'OV','Operação':'Operação','Promocoes':'Qtd. promoções','Ultimo_pedido':'Último pedido','Pedidos_total':'Pedidos no período'}
    st.dataframe(ranking[show].sort_values(['Promocoes','Pedidos_total'],ascending=False).rename(columns=rename),use_container_width=True,hide_index=True,height=420)

    left,right=st.columns([1.35,1])
    with left:
        st.markdown('<div class="section">Pedidos por mês e operação</div>',unsafe_allow_html=True)
        trend=pf.groupby(['Mes','OV Desc2'])['erp_order_id'].nunique().reset_index(name='Pedidos')
        topops=ranking.nlargest(8,'Pedidos_total')['Operação'].dropna().tolist()
        trend=trend[trend['OV Desc2'].isin(topops)]
        fig=px.line(trend,x='Mes',y='Pedidos',color='OV Desc2',markers=True,labels={'OV Desc2':'Operação','Mes':'Mês'})
        fig.update_layout(height=380,legend=dict(orientation='h',y=-.35),margin=dict(l=10,r=10,t=20,b=20))
        st.plotly_chart(fig,use_container_width=True)
    with right:
        st.markdown('<div class="section">Promoções com maior alcance</div>',unsafe_allow_html=True)
        top=af.groupby('promotion_name').agg(Clientes=('hybris_customer_id','nunique'),Faturamento=('Faturamento','sum')).reset_index().nlargest(10,'Clientes')
        fig=px.bar(top.sort_values('Clientes'),x='Clientes',y='promotion_name',orientation='h',color='Clientes',color_continuous_scale=['#9bd8b7','#08764f'])
        fig.update_layout(height=380,coloraxis_showscale=False,yaxis_title='',margin=dict(l=10,r=10,t=20,b=20))
        st.plotly_chart(fig,use_container_width=True)

elif pagina=="Detalhe da Promoção":
    st.markdown('<div class="hero"><h1>Detalhe da Promoção</h1><p>Performance, participantes e rastreabilidade da ação.</p></div>',unsafe_allow_html=True)
    nomes=sorted(a['promotion_name'].dropna().astype(str).unique())
    nome=st.selectbox("Selecione a promoção",nomes)
    d=a[a['promotion_name'].astype(str)==nome]
    promo_ids=', '.join(d['promo_id'].dropna().astype(str).unique()[:5])
    st.caption(f"Código(s): {promo_ids}")
    cs=st.columns(5)
    vals=[('Clientes',d['hybris_customer_id'].nunique()),('Operações',d['Operação'].nunique()),('Faturamento',f"R$ {d['Faturamento'].sum():,.0f}"),('Volume',f"{d['Volume HL'].sum():,.1f} HL"),('Último registro',d['MonthYear'].max().strftime('%m/%Y') if d['MonthYear'].notna().any() else '-')]
    for col,(lab,val) in zip(cs,vals): col.metric(lab,val)
    l,r=st.columns([1.4,1])
    with l:
        evo=d.groupby('MonthYear').agg(Faturamento=('Faturamento','sum'),Clientes=('hybris_customer_id','nunique')).reset_index()
        st.plotly_chart(px.line(evo,x='MonthYear',y='Faturamento',markers=True,title='Evolução do faturamento'),use_container_width=True)
    with r:
        opx=d.groupby('Operação').agg(Clientes=('hybris_customer_id','nunique'),Faturamento=('Faturamento','sum')).reset_index().nlargest(10,'Clientes')
        st.plotly_chart(px.bar(opx.sort_values('Clientes'),x='Clientes',y='Operação',orientation='h',title='Ranking de operações'),use_container_width=True)
    st.markdown('<div class="section">Participantes e produtos</div>',unsafe_allow_html=True)
    st.dataframe(d[['Operação','hybris_customer_id','tipo_promo','nome_padrao_promo','order_origin','SKU','SUB MARCA','PACKTYPE','Faturamento','Volume HL']].sort_values('Faturamento',ascending=False),use_container_width=True,hide_index=True,height=420)

elif pagina=="Fechamento":
    st.markdown('<div class="hero"><h1>Fechamento da Promoção</h1><p>Prévia rastreável para validação e exportação.</p></div>',unsafe_allow_html=True)
    st.info('Este módulo já está desenhado para receber as regras de elegibilidade, ressarcimento e exceções de cada ação.')
    nomes=sorted(a['promotion_name'].dropna().astype(str).unique())
    nome=st.selectbox("Promoção para fechamento",nomes,key='fech')
    d=a[a['promotion_name'].astype(str)==nome]
    st.dataframe(d.groupby('Operação').agg(Clientes=('hybris_customer_id','nunique'),Faturamento=('Faturamento','sum'),Volume_HL=('Volume HL','sum')).reset_index(),use_container_width=True,hide_index=True)
    st.download_button('Baixar prévia em CSV',d.to_csv(index=False,sep=';').encode('utf-8-sig'),file_name='previa_fechamento.csv',mime='text/csv')

else:
    st.markdown('<div class="hero"><h1>Oportunidades</h1><p>Transforme comportamento de compra em novas ações promocionais.</p></div>',unsafe_allow_html=True)
    st.warning('Próxima camada funcional: cross-sell, reativação, penetração de SKU e potencial por operação.')
    opbrand=p[p['order_status'].eq('APROVADO')].groupby(['OV Desc2','MARCA']).agg(Clientes=('customer_id','nunique'),Pedidos=('erp_order_id','nunique'),Faturamento=('gross_amount','sum')).reset_index()
    st.dataframe(opbrand.sort_values('Faturamento',ascending=False).head(100),use_container_width=True,hide_index=True)
