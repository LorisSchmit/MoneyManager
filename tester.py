from Year import Year
import numpy as np
def main():
    year = Year(2023,pre_year=False,projection=False)
    in_advances_total = 0
    for tag_value in year.in_advances.values():
        for subtag_value in tag_value.values():
            in_advances_total += subtag_value
    print(in_advances_total)
    print()


if __name__ == '__main__':
    main()