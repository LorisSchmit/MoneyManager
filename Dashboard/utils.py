# -*- coding: utf-8 -*-
"""
Created in 05/2024

@author: loris
"""

import sys
import json
import re
import os
import datetime
import webbrowser
import time
import pandas as pd
import sqlite3
import numpy as np
import ast

def deduct_payback(transact,df):
    amount = transact.amount
    amount_payback = 0
    for idx in transact.pb_assign:       
        if idx > 0:
            amount_payback = df[df.id == idx].amount.squeeze()
            if amount_payback <= - amount:
                amount += amount_payback
                amount_payback = 0
            else:
                amount_payback += amount
                amount = 0
        elif idx == 0:
            amount = 0
                
    transact.amount = amount
    transact["payback_rest"] = amount_payback
    return transact

def deduct_payback_rest(transact,payback_rest):
    if payback_rest > 0:
        if payback_rest < - transact.amount:
            transact.amount += payback_rest
            payback_rest = 0
        else:
            payback_rest += transact.amount
            transact.amount = 0
            
        transact.payback_rest = payback_rest
    return transact,payback_rest
    
def distribute_payback_rest(df):
    df_payback_rest = df[(df["payback_rest"]>0)]
    for id_pb,transact_pb in df_payback_rest.iterrows():
        df_same_tag = df[(df.tag == transact_pb.tag) & (df.sub_tag == transact_pb.sub_tag) & (df.id != transact_pb.id)]
        df_same_tag = df_same_tag.iloc[(df_same_tag.date-transact_pb.date).abs().argsort()]
        payback_rest = transact_pb.payback_rest
        for id_iter,transact_iter in df_same_tag.iterrows():
            if payback_rest > 0:
                if payback_rest < - transact_iter.amount:
                    df.at[id_iter, 'amount'] += payback_rest
                    payback_rest = 0
                    break
                else:
                    payback_rest += transact_iter.amount
                    df.at[id_iter, 'amount'] = 0
                
            df.at[id_iter, 'payback_rest'] = payback_rest

    return df

def initialize_df(path,starting_balance):
    """ tbd """
    def cumsum_with_start(group, start_value):
            return group.cumsum() + start_value
    con = sqlite3.connect(path)
    df = pd.read_sql_query("SELECT * from transacts", con)
    df["date"] = pd.to_datetime(df["date"], unit='s',utc=True)
    df["date"] = df["date"].dt.tz_convert('Europe/Berlin')
    df = df.sort_values(by="date")
    df["month-year"] = df["date"].apply(lambda date: "{} {}".format(date.month_name(),date.year))
    df["year"] = df["date"].apply(lambda date: "{}".format(date.year))
    df["pb_assign"] = df["pb_assign"].apply(lambda pb_assign: ast.literal_eval(pb_assign))
    
    df["payback_rest"] = 0
    df[df["pb_assign"].str.len()>0] = df[df["pb_assign"].str.len()>0].apply(lambda transact: deduct_payback(transact,df),axis=1)
    df_clean = df.copy(deep=True)
    df = distribute_payback_rest(df)
   
    df_clean = df_clean.sort_values("date")
    df_clean['account_balance'] = df_clean.groupby('account')['amount'].apply(lambda group: cumsum_with_start(group, starting_balance[group.name]))

    con.close()
    return df,df_clean

def initialize_starting_balances(path):
    with open(path, "r", encoding="utf-8") as json_file:
        account_data = json.load(json_file)
    account_data = account_data["accounts"]
    starting_balance = {account["name"]:list(account["balance_base"].values())[0] for account in account_data}
    return starting_balance





