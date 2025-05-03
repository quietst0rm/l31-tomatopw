import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback, State
import dash
from dash.dependencies import Input, Output
import dash_table

# Classe per simulare la produzione di pomodori
class SimulatoreProduzionePuglia:
    def __init__(self):
        # Parametri base della produzione di pomodori in Puglia
        self.parametri = {
            # Temperatura media mensile in Puglia (°C)
            'temperatura_media': {
                'primavera': 18,  # Marzo-Maggio
                'estate': 28,    # Giugno-Agosto
                'autunno': 20,  # Settembre-Novembre
                'inverno': 12    # Dicembre-Febbraio
            },
            # Umidità media mensile (%)
            'umidita_media': {
                'primavera': 65,
                'estate': 50,
                'inverno': 75,
                'autunno': 70
            },
            # Precipitazioni medie mensili (mm)
            'precipitazioni_medie': {
                'primavera': 40,
                'estate': 20,
                'autunno': 60,
                'inverno': 70
            },
            # Produzione media per ettaro (quintali/ha)
            'produzione_media': 650,
            
            # Costi e prezzi
            'costo_per_ettaro': 8000,  # Euro/ettaro
            'prezzo_medio_quintale': 45,  # Euro/quintale
            
            # Varietà principali di pomodoro in Puglia
            'varieta': ['San Marzano', 'Fiaschetto', 'Regina', 'Ciliegino', 'Datterino']
        }
        
        # Coefficienti di impatto ambientale sulla produzione
        self.coefficienti = {
            'temperatura': {
                'ottimale': 25,  # temperatura ottimale in °C
                'min': 10,    # min temperatura per crescita
                'max': 35,    # max temperatura tollerabile
                'impatto': 0.3  # peso del fattore temperatura
            },
            'umidita': {
                'ottimale': 60,  # umidità ottimale in %
                'min': 40,
                'max': 85,
                'impatto': 0.2
            },
            'precipitazioni': {
                'ottimale': 30,  # precipitazioni mensili ottimali in mm
                'min': 15,
                'max': 80,
                'impatto': 0.25
            }
        }

    def _calcola_stagione(self, mese):
        """Determina la stagione in base al mese"""
        if mese in [3, 4, 5]:
            return 'primavera'
        elif mese in [6, 7, 8]:
            return 'estate'
        elif mese in [9, 10, 11]:
            return 'autunno'
        else:
            return 'inverno'
    
    def _genera_temperatura(self, mese, anno, variabilita=2.5):
        """Genera temperatura giornaliera con variabilità stagionale e annuale"""
        stagione = self._calcola_stagione(mese)
        base = self.parametri['temperatura_media'][stagione]
        
        # Aggiungi variazione annuale (cambiamento climatico o annate particolari)
        variazione_annuale = (anno - 2020) * 0.1  # leggero aumento nel tempo
        
        # Aggiungi variazione casuale
        variazione_casuale = np.random.normal(0, variabilita)
        
        return base + variazione_annuale + variazione_casuale
    
    def _genera_umidita(self, mese, temp_giornaliera, variabilita=10):
        """Genera umidità giornaliera correlata alla temperatura"""
        stagione = self._calcola_stagione(mese)
        base = self.parametri['umidita_media'][stagione]
        
        # L'umidità tende ad essere inversamente proporzionale alla temperatura
        corr_temp = (self.parametri['temperatura_media'][stagione] - temp_giornaliera) * 1.5
        variazione_casuale = np.random.normal(0, variabilita)
        
        umidita = base + corr_temp + variazione_casuale
        return max(min(umidita, 100), 30)  # limita tra 30% e 100%
    
    def _genera_precipitazioni(self, mese, umidita_giornaliera):
        """Genera precipitazioni giornaliere correlate all'umidità"""
        stagione = self._calcola_stagione(mese)
        prob_pioggia = (umidita_giornaliera - 50) / 100  # maggiore umidità, maggiore probabilità
        prob_pioggia = max(min(prob_pioggia, 0.8), 0.05)  # limita tra 5% e 80%
        
        # Determina se piove
        if np.random.random() < prob_pioggia:
            base = self.parametri['precipitazioni_medie'][stagione] / 5  # ipotizzando 5 giorni di pioggia medi nel mese
            intensita = np.random.gamma(shape=2.0, scale=base/2)
            return intensita
        else:
            return 0
    
    def _calcola_fattore_ambientale(self, temp, umidita, precipitazioni):
        """Calcola l'impatto complessivo dei fattori ambientali sulla produzione"""
        # Funzione che calcola quanto è ottimale un valore rispetto al range ideale (0-1)
        def calcola_ottimalita(valore, ottimale, minimo, massimo):
            if valore < minimo or valore > massimo:
                return 0.3  # condizioni estreme, bassa produttività
            
            if valore < ottimale:
                return 0.7 + 0.3 * (valore - minimo) / (ottimale - minimo)
            else:
                return 0.7 + 0.3 * (massimo - valore) / (massimo - ottimale)
        
        # Calcola ottimalità per ogni fattore
        temp_factor = calcola_ottimalita(
            temp,
            self.coefficienti['temperatura']['ottimale'],
            self.coefficienti['temperatura']['min'],
            self.coefficienti['temperatura']['max']
        )
        
        umidita_factor = calcola_ottimalita(
            umidita,
            self.coefficienti['umidita']['ottimale'],
            self.coefficienti['umidita']['min'],
            self.coefficienti['umidita']['max']
        )
        
        precip_factor = calcola_ottimalita(
            precipitazioni,
            self.coefficienti['precipitazioni']['ottimale'],
            self.coefficienti['precipitazioni']['min'],
            self.coefficienti['precipitazioni']['max']
        )
        
        # Fattore complessivo ponderato
        fattore_complessivo = (
            temp_factor * self.coefficienti['temperatura']['impatto'] +
            umidita_factor * self.coefficienti['umidita']['impatto'] +
            precip_factor * self.coefficienti['precipitazioni']['impatto'] +
            0.25  # fattore base per altri elementi non modellati
        )
        
        return fattore_complessivo
    
    def genera_dati(self, anni=3, ettari=10):
        """
        Genera dati di simulazione completi per un periodo di anni per una singola azienda.
        Genera dati per tutte le varietà di pomodoro.
        """
        # Lista per raccogliere tutti i dati
        dati_simulati = []
        
        # Genera dati per ogni giorno e ogni anno
        for anno in range(2025, 2025 + anni):
            for mese in range(1, 13):
                # Il ciclo di produzione principale va da aprile a settembre in Puglia
                if 4 <= mese <= 9:  # periodo di produzione
                    # Determina la fase di produzione
                    if mese in [4, 5]:
                        fase = "Crescita"
                    elif mese in [6, 7]:
                        fase = "Maturazione"
                    else:
                        fase = "Raccolta"
                    
                    for giorno in range(1, 31):  # semplifichiamo a 30 giorni per mese
                        # Simulazione delle condizioni ambientali
                        temperatura = self._genera_temperatura(mese, anno)
                        umidita = self._genera_umidita(mese, temperatura)
                        precipitazioni = self._genera_precipitazioni(mese, umidita)
                        
                        # Calcola il fattore ambientale per la produzione
                        fattore_ambientale = self._calcola_fattore_ambientale(temperatura, umidita, precipitazioni)
                        
                        # Genera dati per ogni varietà
                        for varieta in self.parametri['varieta']: # Usa la lista completa delle varietà
                            # Modifica il rendimento in base alla varietà
                            modificatore_varieta = {
                                'San Marzano': 1.1,
                                'Fiaschetto': 0.95,
                                'Regina': 1.05,
                                'Ciliegino': 1.2,
                                'Datterino': 1.15
                            }[varieta]
                            
                            # Calcola l'avanzamento nel ciclo di crescita (0-1)
                            if fase == "Crescita":
                                progress = (mese - 4) * 30 + giorno
                                progress = progress / 60  # normalizzato su 2 mesi
                                produzione_giornaliera = 0  # crescita, nessuna produzione
                                efficienza_utilizzo_acqua = 0.7 + 0.2 * fattore_ambientale  # l/kg
                            elif fase == "Maturazione":
                                progress = 1.0
                                produzione_giornaliera = 0  # maturazione, nessuna produzione
                                efficienza_utilizzo_acqua = 0.8 + 0.2 * fattore_ambientale  # l/kg
                            else:  # Raccolta
                                progress = 1.0
                                # La produzione dipende dal fattore ambientale, dalla varietà e dall'area
                                produzione_base = (self.parametri['produzione_media'] / 60) * ettari  # quintali per giorno
                                produzione_giornaliera = produzione_base * fattore_ambientale * modificatore_varieta
                                efficienza_utilizzo_acqua = 0.9 + 0.1 * fattore_ambientale  # l/kg
                            
                            # Calcolo dei costi giornalieri
                            costo_giornaliero = (self.parametri['costo_per_ettaro'] / 180) * ettari  # costi distribuiti su 6 mesi
                            
                            # Calcolo dei ricavi (solo nella fase di raccolta)
                            ricavi_giornalieri = 0
                            if fase == "Raccolta":
                                # Prezzo variabile in base alla varietà e qualità (determinata dal fattore ambientale)
                                prezzo_quintale = self.parametri['prezzo_medio_quintale'] * modificatore_varieta * (0.8 + 0.4 * fattore_ambientale)
                                ricavi_giornalieri = produzione_giornaliera * prezzo_quintale
                            
                            # Calcola efficienza fertilizzante (kg/ha)
                            efficienza_fertilizzante = 12 - 4 * fattore_ambientale  # condizioni migliori = meno fertilizzante
                            
                            # Aggiunta alla lista di dati
                            dati_simulati.append({
                                'Data': f"{anno}-{mese:02d}-{giorno:02d}",
                                'Anno': anno,
                                'Mese': mese,
                                'Giorno': giorno,
                                'Ettari': ettari,
                                'Varieta': varieta,
                                'Fase': fase,
                                'Temperatura': round(temperatura, 1),
                                'Umidita': round(umidita, 1),
                                'Precipitazioni': round(precipitazioni, 1),
                                'Fattore_Ambientale': round(fattore_ambientale, 2),
                                'Produzione_Quintali': round(produzione_giornaliera, 2),
                                'Costi_Euro': round(costo_giornaliero, 2),
                                'Ricavi_Euro': round(ricavi_giornalieri, 2),
                                'Efficienza_Fertilizzante': round(efficienza_fertilizzante, 2),
                                'Efficienza_Acqua': round(efficienza_utilizzo_acqua, 2),
                                'Progress': progress
                            })
        
        # Converti in DataFrame
        return pd.DataFrame(dati_simulati)

# Crea l'app Dash
app = Dash(__name__, suppress_callback_exceptions=True)

# Crea un'istanza del simulatore
simulatore = SimulatoreProduzionePuglia()

# Genera dati iniziali di default
df_simulazione = simulatore.genera_dati(anni=3, ettari=10)

# Aggiungi una nuova pagina per visualizzare il DataFrame
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Layout principale
main_layout = html.Div([
    # Header with gradient background
    html.Div([
        html.H1("Dashboard Produzione Pomodori in Puglia",
                style={
                    'textAlign': 'center',
                    'color': 'white',
                    'margin': '0',
                    'padding': '20px',
                    'backgroundColor': '#2C3E50',
                    'borderRadius': '0 0 10px 10px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                })
    ], style={
        'marginBottom': '30px',
        'background': 'linear-gradient(135deg, #1a5276 0%, #27ae60 100%)'
    }),
    

    html.Div([
        html.Div([
            html.Div([
                html.H3("Parametri Simulazione",
                        style={
                            'marginBottom': '20px',
                            'color': '#2C3E50',
                            'borderBottom': '2px solid #27ae60',
                            'paddingBottom': '10px'
                        }),
                    html.Label("Seleziona Anno:"),
                    dcc.Dropdown(
                        id='dropdown-anno',
                        options=[{'label': str(anno), 'value': anno} for anno in df_simulazione['Anno'].unique()],
                        value=df_simulazione['Anno'].max(),
                        clearable=False,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                    
                    html.Label("Seleziona Varietà:"),
                    dcc.Dropdown(
                        id='dropdown-varieta',
                        options=[{'label': varieta, 'value': varieta} for varieta in df_simulazione['Varieta'].unique()],
                        value=df_simulazione['Varieta'].unique()[0],
                        clearable=False,
                        style={'marginBottom': '20px', 'width': '100%'}
                    ),
                    
                    html.Label("Numero di Anni:"),
                    dcc.Slider(
                        id='slider-anni',
                        min=1,
                        max=5,
                        value=3,
                        marks={i: f'{i}' for i in range(1, 6)},
                        step=1
                    ),
                    html.Label("Lavorazione del terreno (€):"),
                    dcc.Input(
                        id='input-lavorazione-terreno',
                        type='number',
                        value=2000,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                    html.Label("Acquisto piantine (€):"),
                    dcc.Input(
                        id='input-acquisto-piantine',
                        type='number',
                        value=1500,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                    html.Label("Impianto di irrigazione (€):"),
                    dcc.Input(
                        id='input-impianto-irrigazione',
                        type='number',
                        value=1000,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                    html.Label("Fertilizzazione (€):"),
                    dcc.Input(
                        id='input-fertilizzazione',
                        type='number',
                        value=1200,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                    html.Label("Trattamenti fitosanitari (€):"),
                    dcc.Input(
                        id='input-trattamenti-fitosanitari',
                        type='number',
                        value=800,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                    html.Label("Gestione della chioma (€):"),
                    dcc.Input(
                        id='input-gestione-chioma',
                        type='number',
                        value=1000,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                    html.Label("Irrigazione e altre operazioni colturali (€):"),
                    dcc.Input(
                        id='input-irrigazione-altre',
                        type='number',
                        value=500,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                    html.Label("Prezzo medio di vendita per quintale (€):"),
                    dcc.Input(
                        id='input-prezzo-quintale',
                        type='number',
                        value=45,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                    html.Button('Genera Nuovi Dati', id='btn-genera-dati',
                                    style={'marginTop': '20px', 'backgroundColor': '#27AE60', 'color': 'white',
                                            'border': 'none', 'padding': '10px 20px', 'borderRadius': '5px'}),
                    html.Div([
                        html.P(
                            "Modificando i parametri sopra, come i costi dettagliati, "
                            "la simulazione aggiornerà i dati per riflettere i nuovi valori. Questo influenzerà i costi, "
                            "i ricavi e il profitto totale, visibili nei grafici e negli indicatori di performance.",
                            style={'marginTop': '20px', 'fontSize': '14px', 'color': '#7F8C8D'}
                        )
                    ])
                ], style={
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'padding': '25px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'height': '100%',
                    'overflowY': 'auto'
                })
            ], style={'width': '25%', 'marginRight': '20px'}),
            
            html.Div([
                # Indicatori di performance
                html.Div([
                    html.H3("Indicatori di Performance",
                            style={
                                'textAlign': 'center',
                                'color': '#2C3E50',
                                'marginBottom': '15px',
                                'borderBottom': '2px solid #27ae60',
                                'paddingBottom': '10px'
                            }),
                    html.Div(id='indicatori-performance',
                                    style={
                                        'display': 'flex',
                                        'justifyContent': 'space-around',
                                        'padding': '10px'
                                    })
                ], style={
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'padding': '20px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '20px'
                }),
                
                # Tabs
                html.Div([
                    dcc.Tabs([
                        dcc.Tab(label='Produzione', children=[dcc.Graph(id='grafico-produzione')],
                                        style={'padding': '15px'},
                                        selected_style={'padding': '15px', 'borderTop': '2px solid #27ae60'}),
                        dcc.Tab(label='Condizioni Ambientali', children=[dcc.Graph(id='grafico-ambientale')],
                                        style={'padding': '15px'},
                                        selected_style={'padding': '15px', 'borderTop': '2px solid #27ae60'}),
                        dcc.Tab(label='Analisi Finanziaria', children=[dcc.Graph(id='grafico-finanziario')],
                                        style={'padding': '15px'},
                                        selected_style={'padding': '15px', 'borderTop': '2px solid #27ae60'})
                    ], style={
                        'backgroundColor': 'white',
                        'borderRadius': '10px',
                        'padding': '10px'
                    })
                ], style={
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '20px'
                }),
                
                # Bottom
                html.Div([
                    html.Div([
                        html.H3("Confronto tra Varietà",
                                        style={
                                            'textAlign': 'center',
                                            'color': '#2C3E50',
                                            'borderBottom': '2px solid #27ae60',
                                            'paddingBottom': '10px'
                                        }),
                        dcc.Graph(id='grafico-confronto-varieta')
                    ], style={
                        'backgroundColor': 'white',
                        'borderRadius': '10px',
                        'padding': '20px',
                        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                        'width': '48%'
                    }),
                    
                    html.Div([
                        html.H3("Efficienza Risorse",
                                        style={
                                            'textAlign': 'center',
                                            'color': '#2C3E50',
                                            'borderBottom': '2px solid #27ae60',
                                            'paddingBottom': '10px'
                                        }),
                        dcc.Graph(id='grafico-efficienza')
                    ], style={
                        'backgroundColor': 'white',
                        'borderRadius': '10px',
                        'padding': '20px',
                        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                        'width': '48%'
                    })
                ], style={
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'marginBottom': '20px'
                }),
                
                # Real-time data section
                html.Div([
                    html.H3("Dati in Tempo Reale",
                            style={
                                'textAlign': 'center',
                                'color': '#2C3E50',
                                'borderBottom': '2px solid #27ae60',
                                'paddingBottom': '10px'
                            }),
                    dash_table.DataTable(
                        id='live-data-table',
                        columns=[
                            {'name': 'Data', 'id': 'Data'},
                            {'name': 'Varietà', 'id': 'Varieta'},
                            {'name': 'Fase', 'id': 'Fase'},
                            {'name': 'Temperatura', 'id': 'Temperatura'},
                            {'name': 'Produzione (q)', 'id': 'Produzione_Quintali'},
                            {'name': 'Costi (€)', 'id': 'Costi_Euro'},
                            {'name': 'Ricavi (€)', 'id': 'Ricavi_Euro'},
                            {'name': 'Profitto (€)', 'id': 'Profitto'}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold',
                            'color': '#2C3E50'
                        },
                        page_size=10,
                        sort_action='native',
                        filter_action='native'
                    )
                ], style={
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'padding': '20px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '20px'
                }),
                # Pulsanti per esportare i dati
                html.Div([
                    html.H3("Esporta Dati",
                            style={
                                'textAlign': 'center',
                                'color': '#2C3E50',
                                'borderBottom': '2px solid #27ae60',
                                'paddingBottom': '10px'
                            }),
                    html.Div([
                        html.Button("Esporta in CSV", id='export-csv', n_clicks=0, style={'marginRight': '10px'}),
                        html.Button("Esporta in JSON", id='export-json', n_clicks=0)
                    ], style={'textAlign': 'center', 'marginBottom': '20px'})
                ], style={
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'padding': '20px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '20px'
                }),
                dcc.Download(id="download-dataframe")
            ], style={'width': '75%'})
        ], style={'display': 'flex', 'gap': '20px'})
    ], style={
        'fontFamily': 'Helvetica, Arial, sans-serif',
        'backgroundColor': '#f5f6fa',
        'padding': '20px',
        'minHeight': '100vh'
    })

# Layout della pagina DataFrame
dataframe_layout = html.Div([
    html.H1("Tabella dei Dati Simulati", style={'textAlign': 'center'}),
    html.Div([
        dash_table.DataTable(
            id='data-table',
            columns=[{'name': col, 'id': col} for col in df_simulazione.columns],
            data=df_simulazione.to_dict('records'),
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'}
        )
    ], style={'marginBottom': '20px'}),
    html.Div([
        html.Button("Esporta in CSV", id='export-csv', n_clicks=0, style={'marginRight': '10px'}),
        html.Button("Esporta in JSON", id='export-json', n_clicks=0)
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    dcc.Download(id="download-dataframe")
])

# Callback per gestire la navigazione tra le pagine
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/dataframe':
        return dataframe_layout
    else:
        return main_layout

# Callback per esportare il DataFrame in CSV o JSON
@app.callback(
    Output("download-dataframe", "data"),
    [Input("export-csv", "n_clicks"),
     Input("export-json", "n_clicks")]
)
def export_dataframe(n_clicks_csv, n_clicks_json):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "export-csv":
        return dcc.send_data_frame(df_simulazione.to_csv, "dati_simulati.csv", index=False)
    elif button_id == "export-json":
        return dcc.send_data_frame(df_simulazione.to_json, "dati_simulati.json", orient="records")

# Callback per generare nuovi dati aggiornato
@app.callback(
    [Output('dropdown-anno', 'options'),
     Output('dropdown-anno', 'value'),
     Output('dropdown-varieta', 'options'),
     Output('dropdown-varieta', 'value'),
     Output('live-data-table', 'data')],
    Input('btn-genera-dati', 'n_clicks'),
    [State('slider-anni', 'value'),
     State('input-lavorazione-terreno', 'value'),
     State('input-acquisto-piantine', 'value'),
     State('input-impianto-irrigazione', 'value'),
     State('input-fertilizzazione', 'value'),
     State('input-trattamenti-fitosanitari', 'value'),
     State('input-gestione-chioma', 'value'),
     State('input-irrigazione-altre', 'value'),
     State('input-prezzo-quintale', 'value')]
)
def genera_nuovi_dati(n_clicks, anni, lavorazione_terreno, acquisto_piantine,
                        impianto_irrigazione, fertilizzazione, trattamenti_fitosanitari,
                        gestione_chioma, irrigazione_altre, prezzo_quintale):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    # Calcola il costo totale per ettaro
    costo_per_ettaro = (
        lavorazione_terreno +
        acquisto_piantine +
        impianto_irrigazione +
        fertilizzazione +
        trattamenti_fitosanitari +
        gestione_chioma +
        irrigazione_altre
    )
    
    # Aggiorna i parametri del simulatore
    simulatore.parametri['costo_per_ettaro'] = costo_per_ettaro
    simulatore.parametri['prezzo_medio_quintale'] = prezzo_quintale
    
    global df_simulazione
    df_simulazione = simulatore.genera_dati(anni=anni, ettari=10)  # Ettari fissi per singola azienda
    
    # Prepara i dati per la tabella
    df_table = df_simulazione.copy()
    df_table['Profitto'] = df_table['Ricavi_Euro'] - df_table['Costi_Euro']
    
    anni_options = [{'label': str(anno), 'value': anno} for anno in df_simulazione['Anno'].unique()]
    anno_value = df_simulazione['Anno'].max()
    
    varieta_options = [{'label': varieta, 'value': varieta} for varieta in df_simulazione['Varieta'].unique()]
    varieta_value = df_simulazione['Varieta'].unique()[0]
    
    return anni_options, anno_value, varieta_options, varieta_value, df_table.to_dict('records')

# Callback per gli indicatori di performance
@app.callback(
    Output('indicatori-performance', 'children'),
    Input('dropdown-anno', 'value'),
    Input('dropdown-varieta', 'value')
)
def aggiorna_indicatori(anno, varieta):
    df_filtrato = df_simulazione[
        (df_simulazione['Anno'] == anno) &
        (df_simulazione['Varieta'] == varieta)
    ]
    
    # Calcolo indicatori di performance
    produzione_totale = df_filtrato['Produzione_Quintali'].sum()
    ricavi_totali = df_filtrato['Ricavi_Euro'].sum()
    costi_totali = df_filtrato['Costi_Euro'].sum()
    profitto = ricavi_totali - costi_totali
    
    if costi_totali > 0:
        roi = (profitto / costi_totali) * 100
    else:
        roi = 0
        
    efficienza_media_acqua = df_filtrato['Efficienza_Acqua'].mean()
    
    indicatori = [
        html.Div([
            html.H4(f"{produzione_totale:.1f} q", style={'margin': '0', 'textAlign': 'center', 'color': '#2980B9'}),
            html.P("Produzione Totale", style={'margin': '0', 'textAlign': 'center'})
        ]),
        html.Div([
            html.H4(f"€ {ricavi_totali:.0f}", style={'margin': '0', 'textAlign': 'center', 'color':'#27AE60'}),
            html.P("Ricavi", style={'margin': '0', 'textAlign': 'center'})
        ]),
        html.Div([
            html.H4(f"{roi:.1f}%", style={'margin': '0', 'textAlign': 'center',
                                                'color': '#E74C3C' if roi < 0 else '#27AE60'}),
            html.P("ROI", style={'margin': '0', 'textAlign': 'center'})
        ]),
        html.Div([
            html.H4(f"{efficienza_media_acqua:.2f} l/kg", style={'margin': '0', 'textAlign': 'center', 'color': '#2980B9'}),
            html.P("Efficienza Acqua", style={'margin': '0', 'textAlign': 'center'})
        ])
    ]
    
    return indicatori

# Callback per il grafico produzione
@app.callback(
    Output('grafico-produzione', 'figure'),
    Input('dropdown-anno', 'value'),
    Input('dropdown-varieta', 'value')
)
def aggiorna_grafico_produzione(anno, varieta):
    df_filtrato = df_simulazione[
        (df_simulazione['Anno'] == anno) &
        (df_simulazione['Varieta'] == varieta)
    ]
    
    # Converti la colonna Data in datetime e aggrega per mese
    df_filtrato['Data'] = pd.to_datetime(df_filtrato['Data'])
    df_mensile = df_filtrato.groupby(pd.Grouper(key='Data', freq='M')).agg({
        'Produzione_Quintali': 'sum',
        'Fase': 'last'  # prende l'ultima fase del mese
    }).reset_index()
    
    # Aggiungi annotazioni per le fasi
    fasi_unique = df_mensile['Fase'].unique()
    colors = {'Crescita': 'green', 'Maturazione': 'orange', 'Raccolta': 'red'}
    
    fig = px.bar(
        df_mensile,
        x='Data',
        y='Produzione_Quintali',
        title=f'Produzione Mensile ({varieta}) - {anno}',
        labels={'Produzione_Quintali': 'Produzione (quintali)', 'Data': 'Mese'},
        color='Fase',
        color_discrete_map=colors
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        xaxis=dict(tickformat='%b'),
        legend_title_text='Fase',
        height=400
    )
    
    return fig

# Callback per il grafico ambientale
@app.callback(
    Output('grafico-ambientale', 'figure'),
    Input('dropdown-anno', 'value'),
    Input('dropdown-varieta', 'value')
)
def aggiorna_grafico_ambientale(anno, varieta):
    df_filtrato = df_simulazione[
        (df_simulazione['Anno'] == anno) &
        (df_simulazione['Varieta'] == varieta)
    ]
    
    df_filtrato['Data'] = pd.to_datetime(df_filtrato['Data'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_filtrato['Data'],
        y=df_filtrato['Temperatura'],
        name='Temperatura (°C)',
        line=dict(color='red')
    ))
    
    fig.add_trace(go.Scatter(
        x=df_filtrato['Data'],
        y=df_filtrato['Umidita'],
        name='Umidità (%)',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Bar(
        x=df_filtrato['Data'],
        y=df_filtrato['Precipitazioni'],
        name='Precipitazioni (mm)',
        marker_color='skyblue'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_filtrato['Data'],
        y=df_filtrato['Fattore_Ambientale'] * 100,  # Moltiplica per 100 per visualizzarlo meglio
        name='Indice Ambientale (%)',
        line=dict(color='green', dash='dash')
    ))
    
    fig.update_layout(
        title=f'Condizioni Ambientali ({varieta}) - {anno}',
        xaxis_title='Data',
        yaxis_title='Valori',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='white',
        height=400
    )
    
    return fig

# Callback per il grafico finanziario
@app.callback(
    Output('grafico-finanziario', 'figure'),
    Input('dropdown-anno', 'value'),
    Input('dropdown-varieta', 'value')
)
def aggiorna_grafico_finanziario(anno, varieta):
    df_filtrato = df_simulazione[
        (df_simulazione['Anno'] == anno) &
        (df_simulazione['Varieta'] == varieta)
    ]
    
    df_filtrato['Data'] = pd.to_datetime(df_filtrato['Data'])
    df_filtrato['Profitto_Euro'] = df_filtrato['Ricavi_Euro'] - df_filtrato['Costi_Euro']
    
    # Aggregazione mensile
    df_mensile = df_filtrato.groupby(pd.Grouper(key='Data', freq='M')).agg({
        'Costi_Euro': 'sum',
        'Ricavi_Euro': 'sum',
        'Profitto_Euro': 'sum'
    }).reset_index()
    
    # Cumulativo per profitto (per vedere l'andamento annuale)
    df_mensile['Profitto_Cumulativo'] = df_mensile['Profitto_Euro'].cumsum()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_mensile['Data'],
        y=df_mensile['Costi_Euro'],
        name='Costi (€)',
        marker_color='red'
    ))
    
    fig.add_trace(go.Bar(
        x=df_mensile['Data'],
        y=df_mensile['Ricavi_Euro'],
        name='Ricavi (€)',
        marker_color='green'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_mensile['Data'],
        y=df_mensile['Profitto_Cumulativo'],
        name='Profitto Cumulativo (€)',
        line=dict(color='blue', width=3)
    ))
    
    fig.update_layout(
        title=f'Analisi Finanziaria ({varieta}) - {anno}',
        xaxis_title='Mese',
        yaxis_title='Euro (€)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='white',
        barmode='group',
        height=400
    )
    
    return fig

# Callback per il grafico di confronto tra varietà
@app.callback(
    Output('grafico-confronto-varieta', 'figure'),
    Input('dropdown-anno', 'value')
)
def aggiorna_confronto_varieta(anno):
    df_filtrato = df_simulazione[
        (df_simulazione['Anno'] == anno)
    ]
    
    # Raggruppa per varietà
    df_varieta = df_filtrato.groupby('Varieta').agg({
        'Produzione_Quintali': 'sum',
        'Ricavi_Euro': 'sum',
        'Costi_Euro': 'sum',
        'Ettari': 'mean'  # prende il valore medio per varietà
    }).reset_index()
    
    # Calcola metriche aggiuntive
    df_varieta['Profitto_Euro'] = df_varieta['Ricavi_Euro'] - df_varieta['Costi_Euro']
    df_varieta['Rendimento_per_Ettaro'] = df_varieta['Produzione_Quintali'] / df_varieta['Ettari']
    
    fig = px.scatter(
        df_varieta,
        x='Rendimento_per_Ettaro',
        y='Profitto_Euro',
        size='Ettari',
        color='Varieta',
        hover_name='Varieta',
        text='Varieta',
        title=f'Confronto Varietà - {anno}',
        labels={
            'Rendimento_per_Ettaro': 'Rendimento (q/ha)',
            'Profitto_Euro': 'Profitto (€)',
            'Ettari': 'Dimensione (ha)'
        }
    )
    
    fig.update_traces(textposition='top center')
    
    fig.update_layout(
        plot_bgcolor='white',
        height=400
    )
    
    return fig

# Callback per il grafico di efficienza
@app.callback(
    Output('grafico-efficienza', 'figure'),
    Input('dropdown-anno', 'value')
)
def aggiorna_grafico_efficienza(anno):
    df_filtrato = df_simulazione[
        (df_simulazione['Anno'] == anno)
    ]
    
    # Raggruppa per varietà
    df_varieta = df_filtrato.groupby('Varieta').agg({
        'Efficienza_Acqua': 'mean',
        'Efficienza_Fertilizzante': 'mean',
        'Produzione_Quintali': 'sum'
    }).reset_index()
    
    # Crea un grafico a radar
    categories = df_varieta['Varieta'].tolist()
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=df_varieta['Efficienza_Acqua'],
        theta=categories,
        fill='toself',
        name='Efficienza Acqua (l/kg)'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=[10 - val for val in df_varieta['Efficienza_Fertilizzante']],  # Inverti il valore per rappresentare l'efficienza
        theta=categories,
        fill='toself',
        name='Efficienza Fertilizzante'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=df_varieta['Produzione_Quintali'] / df_varieta['Produzione_Quintali'].max(),  # Normalizza
        theta=categories,
        fill='toself',
        name='Produzione Relativa'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1.2]  # Normalizzato
            )
        ),
        title=f'Efficienza Risorse per Varietà - {anno}',
        showlegend=True,
        height=400
    )
    
    return fig

# Esecuzione dell'app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050, debug=True)
