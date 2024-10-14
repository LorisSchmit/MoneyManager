from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
import dash
import locale
# Set the locale to French (France)
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

def plotTreemap(expense_transacts):
    spent = expense_transacts["amount"].sum()

    parents = [""]
    labels = [" "]
    values = [0]
    ids = ["all"]

    expenses_by_tags = expense_transacts.groupby(["recipient","tag","sub_tag"]).sum()
    expenses_labels = list(expenses_by_tags.index.get_level_values(0))
    expenses_ids = list("t_"+expenses_by_tags.index.get_level_values(1)+"_st_"+expenses_by_tags.index.get_level_values(2)+"_id_"+expenses_by_tags.index.get_level_values(0))
    parents_expenses = list("t_"+expenses_by_tags.index.get_level_values(1)+"_st_"+expenses_by_tags.index.get_level_values(2))
    parents_expenses = [(parent[:-4] if parent[-4:] == "_st_" else parent ) for parent in parents_expenses]

    tags_grouped = dict(expense_transacts.groupby(["tag","sub_tag"])["amount"].sum())
    tags_struct = {}
    for (tag,sub_tag),amount in tags_grouped.items():
        tags_struct[tag] = {}
        
    for (tag,sub_tag),amount in tags_grouped.items():
        tags_struct[tag][sub_tag] = amount

    for tag,sub_tags in tags_struct.items():
        total = sum([-round(value,2) for sub_tag,value in sub_tags.items()])
        parents.append("all")
        t_id = "t_"+tag
        ids.append(t_id )
        if parents_expenses.count(t_id) > 1:
            label = tag + "&nbsp;&nbsp;"+ str(round(total / -spent * 100)) +"%<br>"+ str(round(total, 2)) + " €"
            labels.append(label)
        else:
            labels.append(tag)
        values.append(0)

        for sub_tag,value in sub_tags.items():
            if sub_tag != "":
                st_id = t_id +"_st_"+sub_tag
                if parents_expenses.count(st_id) > 1:
                    label = sub_tag + "&nbsp;&nbsp;"+ str(round(-value / -spent * 100)) +"%<br>"+ str(round(-value, 2)) + " €"
                    labels.append(label)
                else:
                    labels.append(sub_tag)
                parents.append(t_id)
                values.append(0)
                ids.append(st_id)
                

    labels.extend(expenses_labels)
    values.extend(list(-expenses_by_tags["amount"].values))
    parents.extend(parents_expenses)
    ids.extend(expenses_ids)
        

    fig = go.Figure(go.Treemap(
        ids = ids,
        labels=labels,
        parents=parents,
        values=values,
        branchvalues='remainder'
    ))
    #width = 1100
    #height = 500
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))#,width=width, height=height)#,uniformtext=dict(minsize = 5, mode ='show'))

    fig.data[0].texttemplate = "%{label} <br>%{value} €<br>%{percentEntry} "

    return fig
        
def register_callbacks(dash_app):
    @dash_app.app.callback(
            [Output('spent-label-value', 'children'),
            Output('income-label-value', 'children'),
            Output('payback-label-value', 'children'),
            Output('balance-label-value', 'children'),
            Output('going-in-label-value', 'children'),
            Output('going-out-label-value', 'children'),
            Output('balance-total-label-value', 'children'),
            ],
            [Input('month-year-select-dropdown','value'),
            Input('state-value', 'data')]
        )
    def showStats(selected_month_year,month_year_selected):
        if month_year_selected == "year":
            transacts = dash_app.df[dash_app.df["year"] == selected_month_year]
            transacts_clean = dash_app.df_clean[dash_app.df_clean["year"] == selected_month_year]
            income = round(transacts[(transacts["amount"]>0 ) & (transacts["tag"]!= "Kapitaltransfer") & (transacts["tag"]!= "Rückzahlung")]["amount"].sum(),2)
        else:
            transacts = dash_app.df[dash_app.df["month-year"] == selected_month_year]
            transacts_clean = dash_app.df_clean[dash_app.df_clean["month-year"] == selected_month_year]
            year = selected_month_year[-4:]
            income_transacts = dash_app.df[dash_app.df["year"] == year]
            income = round(income_transacts[(income_transacts["amount"]>0 ) & (income_transacts["tag"]!= "Kapitaltransfer") & (income_transacts["tag"]!= "Rückzahlung")]["amount"].sum()/len(income_transacts["month-year"].unique()),2)
        spent = round(transacts[((transacts["amount"]<0 ) ) & (transacts["tag"]!= "Kapitaltransfer")]["amount"].sum(),2)
        payback_transacts = transacts[(transacts["tag"] == "Rückzahlung") & (transacts["pb_assign"].str.len()==1)]
        payback_transacts = payback_transacts[payback_transacts['pb_assign'].apply(lambda x: x == [-1])]
        payback = round(payback_transacts["amount"].sum(),2)
        balance = round(income+spent+payback,2)

        going_out = transacts[(transacts["amount"]<0)]["amount"].sum()
        going_in = transacts[(transacts["amount"]>0)]["amount"].sum()
        balance_total = going_out+going_in

        spent = locale.currency(-spent, symbol=True, grouping=True).replace("Eu","€")
        income = locale.currency(income, symbol=True, grouping=True).replace("Eu","€")
        payback = locale.currency(payback, symbol=True, grouping=True).replace("Eu","€")
        balance_frmt = ("-" if balance < 0 else "")+locale.currency(balance, symbol=True, grouping=True).replace("Eu","€").replace("-","")

        going_out = locale.currency(-going_out, symbol=True, grouping=True).replace("Eu","€")
        going_in = locale.currency(going_in, symbol=True, grouping=True).replace("Eu","€")
        
        balance_total_frmt = ("-" if balance_total < 0 and month_year_selected == "year" else "")+(locale.currency(balance_total, symbol=True, grouping=True).replace("Eu","€").replace("-","") if month_year_selected == "year" else "- €")
        
        return spent, income, payback, balance_frmt, going_in, going_out, balance_total_frmt
    @dash_app.app.callback(
            Output('treemap-plot', 'figure'),
            [Input('month-year-select-dropdown','value'),
            Input('state-value', 'data')]
        )
    def plotTreemapExpenses(selected_month_year,month_year_selected):
        if month_year_selected == "year":
            transacts = dash_app.df[dash_app.df["year"] == selected_month_year]
        else:
            transacts = dash_app.df[dash_app.df["month-year"] == selected_month_year]
        expense_transacts = transacts[(transacts.tag != "Kapitaltransfer") & (transacts.amount < 0)]
        fig = plotTreemap(expense_transacts)
        return fig
    
    @dash_app.app.callback(
            Output('treemap-income-plot', 'figure'),
            [Input('month-year-select-dropdown','value'),
            Input('state-value', 'data')]
        )
    def plotTreemapExpenses(selected_month_year,month_year_selected):
        if month_year_selected == "year":
            transacts = dash_app.df[dash_app.df["year"] == selected_month_year]
        else:
            transacts = dash_app.df[dash_app.df["month-year"] == selected_month_year]
        expense_transacts = transacts[(transacts.tag != "Kapitaltransfer") & (transacts.amount > 0)]
        expense_transacts.amount *= -1
        fig = plotTreemap(expense_transacts)
        return fig



    @dash_app.app.callback(
        [Output('show-year-btn', 'style'),
         Output('show-month-btn', 'style'),
         Output("month-year-label","children"),
         Output('month-year-select-dropdown', 'options'),
         Output('state-value', 'data')],
        [Input('show-year-btn', 'n_clicks'),
         Input('show-month-btn', 'n_clicks')]
    )
    def toggle_buttons(n_clicks_1, n_clicks_2):
        if n_clicks_1 > 0 or n_clicks_2 > 0:
            # Get the context of the callback to see which input triggered it
            ctx = dash.callback_context

            # Default styles
            button_1_style = {'backgroundColor': 'white', 'color': 'black'}
            button_2_style = {'backgroundColor': 'white', 'color': 'black'}
            label = ""
            if ctx.triggered:
                button_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if button_id == 'show-year-btn':
                    button_1_style = {'backgroundColor': 'orange', 'color': 'white'}
                    label = "Select year: "
                    month_year_selected = "year"
                    options = dash_app.df["year"].unique()
                elif button_id == 'show-month-btn':
                    button_2_style = {'backgroundColor': 'orange', 'color': 'white'}
                    label = "Select month: "
                    month_year_selected = "month"
                    options = dash_app.df["month-year"].unique()

            return button_1_style, button_2_style, label, options, month_year_selected
        else:
            raise PreventUpdate 
        

    @dash_app.app.callback(
        Output('account-balance-plot', 'figure'),
        [Input('month-year-select-dropdown','value'),
        Input('state-value', 'data')]
    )
    def update_account_balance_plot(selected_month_year,month_year_selected):
        fig = go.Figure()
        if month_year_selected == "year":
            transacts = dash_app.df_clean[dash_app.df_clean["year"] == selected_month_year]
        else:
            transacts = dash_app.df_clean[dash_app.df_clean["month-year"] == selected_month_year]
        for account, group in transacts.groupby('account'):
            fig.add_trace(go.Scatter(
                x=group.date,
                y=group['account_balance'],
                mode='lines',
                line_shape='hv',  # horizontal-vertical step line
                name=f'{account}',
                marker=dict(size=10),
            ))

        fig.update_layout(
            xaxis_title='Zeit',
            yaxis_title='Kontostand',
            #legend_title='Konto',
            template='simple_white',
            showlegend=False
        )

        return fig

