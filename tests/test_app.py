import unittest
import pandas as pd
import numpy as np  
from app import (
    SimulatoreProduzionePuglia,
    aggiorna_grafico_produzione,
    aggiorna_grafico_ambientale,
    aggiorna_grafico_finanziario,
    aggiorna_confronto_varieta,
    aggiorna_grafico_efficienza,
    aggiorna_indicatori,
    genera_nuovi_dati
)


class TestSimulatoreProduzionePuglia(unittest.TestCase):
    def setUp(self):
        """Set up the simulator instance for testing."""
        self.simulatore = SimulatoreProduzionePuglia()
        self.df_simulazione = self.simulatore.genera_dati(anni=1, ettari=10)

    def test_genera_dati(self):
        """Test that the simulator generates a DataFrame with the correct structure."""
        self.assertIsInstance(self.df_simulazione, pd.DataFrame)
        self.assertGreater(len(self.df_simulazione), 0)
        expected_columns = [
            'Data', 'Anno', 'Mese', 'Giorno', 'Ettari', 'Varieta', 'Fase',
            'Temperatura', 'Umidita', 'Precipitazioni', 'Fattore_Ambientale',
            'Produzione_Quintali', 'Costi_Euro', 'Ricavi_Euro',
            'Efficienza_Fertilizzante', 'Efficienza_Acqua', 'Progress'
        ]
        self.assertListEqual(list(self.df_simulazione.columns), expected_columns)

    def test_calcola_fattore_ambientale(self):
        """Test the calculation of the environmental factor."""
        temp = 25  
        umidita = 60  
        precipitazioni = 30  
        fattore = self.simulatore._calcola_fattore_ambientale(temp, umidita, precipitazioni)
        self.assertGreaterEqual(fattore, 0)
        self.assertLessEqual(fattore, 1)


class TestCallbacks(unittest.TestCase):
    def setUp(self):
        """Set up test data for callbacks."""
        self.simulatore = SimulatoreProduzionePuglia()
        self.df_simulazione = self.simulatore.genera_dati(anni=1, ettari=10)

    def test_aggiorna_grafico_produzione(self):
        """Test the production graph callback."""
        anno = self.df_simulazione.loc[self.df_simulazione.index[0], 'Anno']
        varieta = self.df_simulazione.loc[self.df_simulazione.index[0], 'Varieta']
        fig = aggiorna_grafico_produzione(anno, varieta)


        from plotly.graph_objects import Figure
        self.assertIsInstance(fig, Figure, "La funzione non ha restituito un oggetto di tipo plotly.graph_objects.Figure.")


        fig_dict = fig.to_dict()
        self.assertIsInstance(fig_dict, dict, "La figura non può essere convertita in un dizionario.")
        self.assertIn('data', fig_dict, "Il dizionario della figura non contiene la chiave 'data'.")
        self.assertIn('layout', fig_dict, "Il dizionario della figura non contiene la chiave 'layout'.")

    def test_aggiorna_grafico_ambientale(self):
        """Test the environmental graph callback."""
        anno = self.df_simulazione['Anno'].iloc[0]
        varieta = self.df_simulazione['Varieta'].iloc[0]
        fig = aggiorna_grafico_ambientale(anno, varieta)


        from plotly.graph_objects import Figure
        self.assertIsInstance(fig, Figure, "La funzione non ha restituito un oggetto di tipo plotly.graph_objects.Figure.")


        fig_dict = fig.to_dict()
        self.assertIsInstance(fig_dict, dict, "La figura non può essere convertita in un dizionario.")
        self.assertIn('data', fig_dict, "Il dizionario della figura non contiene la chiave 'data'.")
        self.assertIn('layout', fig_dict, "Il dizionario della figura non contiene la chiave 'layout'.")

    def test_aggiorna_grafico_finanziario(self):
        """Test the financial graph callback."""
        anno = self.df_simulazione['Anno'].iloc[0]
        varieta = self.df_simulazione['Varieta'].iloc[0]
        fig = aggiorna_grafico_finanziario(anno, varieta)


        from plotly.graph_objects import Figure
        self.assertIsInstance(fig, Figure, "La funzione non ha restituito un oggetto di tipo plotly.graph_objects.Figure.")


        fig_dict = fig.to_dict()
        self.assertIsInstance(fig_dict, dict, "La figura non può essere convertita in un dizionario.")
        self.assertIn('data', fig_dict, "Il dizionario della figura non contiene la chiave 'data'.")
        self.assertIn('layout', fig_dict, "Il dizionario della figura non contiene la chiave 'layout'.")

    def test_aggiorna_confronto_varieta(self):
        """Test the variety comparison graph callback."""
        anno = self.df_simulazione['Anno'].iloc[0]
        fig = aggiorna_confronto_varieta(anno)


        from plotly.graph_objects import Figure
        self.assertIsInstance(fig, Figure, "La funzione non ha restituito un oggetto di tipo plotly.graph_objects.Figure.")


        fig_dict = fig.to_dict()
        self.assertIsInstance(fig_dict, dict, "La figura non può essere convertita in un dizionario.")
        self.assertIn('data', fig_dict, "Il dizionario della figura non contiene la chiave 'data'.")
        self.assertIn('layout', fig_dict, "Il dizionario della figura non contiene la chiave 'layout'.")

    def test_aggiorna_grafico_efficienza(self):
        """Test the efficiency graph callback."""
        anno = self.df_simulazione['Anno'].iloc[0]
        fig = aggiorna_grafico_efficienza(anno)


        from plotly.graph_objects import Figure
        self.assertIsInstance(fig, Figure, "La funzione non ha restituito un oggetto di tipo plotly.graph_objects.Figure.")


        fig_dict = fig.to_dict()
        self.assertIsInstance(fig_dict, dict, "La figura non può essere convertita in un dizionario.")
        self.assertIn('data', fig_dict, "Il dizionario della figura non contiene la chiave 'data'.")
        self.assertIn('layout', fig_dict, "Il dizionario della figura non contiene la chiave 'layout'.")

    def test_aggiorna_indicatori(self):
        """Test the performance indicators callback."""
        anno = self.df_simulazione['Anno'].iloc[0]
        varieta = self.df_simulazione['Varieta'].iloc[0]
        indicatori = aggiorna_indicatori(anno, varieta)
        self.assertIsInstance(indicatori, list)
        self.assertGreater(len(indicatori), 0)

    def test_genera_nuovi_dati(self):
        """Test the callback for generating new data."""
        n_clicks = 1
        anni = 2
        lavorazione_terreno = 1000
        acquisto_piantine = 800
        impianto_irrigazione = 500
        fertilizzazione = 600
        trattamenti_fitosanitari = 400
        gestione_chioma = 700
        irrigazione_altre = 300
        prezzo_quintale = 50

        output = genera_nuovi_dati(
            n_clicks, anni, lavorazione_terreno, acquisto_piantine,
            impianto_irrigazione, fertilizzazione, trattamenti_fitosanitari,
            gestione_chioma, irrigazione_altre, prezzo_quintale
        )
        anni_options, anno_value, varieta_options, varieta_value, live_data = output

        self.assertIsInstance(anni_options, list)
        self.assertTrue(
            isinstance(anno_value, (int, np.integer)),
            f"anno_value è di tipo {type(anno_value)}, atteso int o np.integer"
        )
        self.assertIsInstance(varieta_options, list)
        self.assertIsInstance(varieta_value, str)
        self.assertIsInstance(live_data, list)
        self.assertGreater(len(live_data), 0)


if __name__ == '__main__':
    unittest.main()