# -*- coding: utf-8 -*-
"""
Created in 05/2024

@author: loris
"""

import argparse
import os
import json
import webbrowser
import sys

import utils
from app import MyDashApp

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Dashboard for Activity Analytics",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)




    webbrowser.open("http://127.0.0.1:8050/")

    MyDashApp("/Users/loris/Documents/MoneyManager/db_private.db", "/Users/loris/src/Python/MoneyManager/accounts.json").run()
