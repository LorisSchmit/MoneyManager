# -*- coding: utf-8 -*-
"""
Created in 06/2024

@author: loris
"""

import datetime
import pandas as pd


import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import sys
from pathlib import Path


import utils
import callbacks


class MyDashApp:
    """ tbd """
    def __init__(self, path_to_df, path_to_accounts):
        """ tbd """
        self.starting_balances = utils.initialize_starting_balances(path_to_accounts)
        self.df,self.df_clean = utils.initialize_df(path_to_df,self.starting_balances)
        
        self.color_palette = px.colors.qualitative.Plotly

        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.layout = self.create_layout()


        callbacks.register_callbacks(self)

    def create_layout(self):
        """ tbd """
        layout =  dbc.Container([
            # Header bar
            self.create_navbar(),


            # first row - Month stats
            self.display_stats(),


            ],fluid=True,  className="body")

        return layout

    def create_navbar(self):
        """ tbd """

        navbar = dbc.Navbar(
                dbc.Container([
                    dbc.Col(
                        html.A(dbc.Row(dbc.Col(
                            html.H1(children="MoneyManager Dashboard", className="header-title")
                            , width='auto'), align="left", className="g-0 m-0 p-0"))
                        )
                ]), color="dark", dark=True, sticky='top', className="g-0 p-1 m-0"
            )

        return navbar

    def create_canvas(self):
        """ tbd """

        canvas = dbc.Row([
                dbc.Offcanvas([
                    dbc.Row(

                    ),
                    dbc.Row(

                    ),
                    dbc.Row(html.Span(id="pull-date-output", style={"verticalAlign": "middle"})),
                    ], id="offcanvas",
                    title="Set Filters",
                    placement='bottom',
                    is_open=False,
                ),
            ])

        return canvas

    def create_card(self, card_id, title,style={}):
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5(title, id=f"{card_id}-title"),
                    html.H3("100", id=f"{card_id}-value")
                ]
            ),style=style
        )

    def display_stats(self):
        """ tbd """

        row = dbc.Row([
                dbc.Col([
                    dbc.Col([
                        dbc.Button("Jahr", id="show-year-btn",
                                    n_clicks=0, outline=True,style= {'backgroundColor': 'orange', 'color': 'white'}, className="me-1"),
                        dbc.Button("Monat", id="show-month-btn",
                                    n_clicks=0, outline=True,style={'backgroundColor': 'white', 'color': 'black'}, className="me-1"),
                        html.Span("Select year: ",id="month-year-label"),
                        dcc.Dropdown(self.df["year"].unique(), '2024', id='month-year-select-dropdown',searchable=False,style={'width': '150px', 'display': 'inline-block', 'verticalAlign': 'middle'} ),
                        dcc.Store(id='state-value',data="year")
                    ], className="fw-bold m-3",width="auto"),
                    
                    dbc.Row([
                        dbc.Col([self.create_card("spent-label", "Ausgaben")],width="auto",className="fw-bold m-3"),
                        dbc.Col([self.create_card("income-label", "Einnahmen")],width="auto",className="fw-bold m-3"),
                        dbc.Col([self.create_card("payback-label", "Rückzahlung")],width="auto",className="fw-bold m-3"),
                        dbc.Col([self.create_card("going-in-label", "Auf Konten eingegangen")],width="auto",className="fw-bold m-3"),
                        dbc.Col([self.create_card("going-out-label", "Von Konten abgegangen")],width="auto",className="fw-bold m-3"),
                        dbc.Col(dbc.Row([self.create_card("balance-label", "Bilanz",style={"width":"50%"}),
                                         self.create_card("balance-total-label", "Bilanz",style={"width":"50%"})]),width="auto",className="fw-bold m-3"),
                    ],style={"display": "block", "font-size":"3vh"}),
                ],width="auto",className='bg-white g-0 m-1 rounded-3'),
                dbc.Col([ 
                        dcc.Graph(id='treemap-plot',style={'width': '90vh', 'height': '90vh'},className="fw m-3"),
                ],width="auto",className='bg-white g-0 m-1 rounded-3'),
                dbc.Col([ 
                        dcc.Graph(id='treemap-income-plot',style={'width': '57vh', 'height': '47vh'},className="fw m-3"),
                        dcc.Graph(id='account-balance-plot',className="fw m-3"),
                ],width="auto",className='bg-white g-0 m-1 rounded-3'),

            ],style={"height": "90vh"},className="g-0 p-0 m-0")

        return row





    def run(self):
        """ tbd """
        self.app.run_server(debug=True, port=8050, use_reloader=False)

# for testing
# if __name__ == '__main__':
#     app = MyDashApp("./data/strava_activities.csv")
#     app.run()
