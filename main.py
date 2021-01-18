from importer import *
from database import *
from database_api import *


def main():
    transacts = getAllTransacts()
    monthly_transacts = getMonthlyTransacts(transacts,2,2019)
    for action in monthly_transacts:
        print(action.__dict__)


if __name__ == '__main__':
    main()