import matplotlib.pyplot as plt
from createBalanceSheets import prepare4Saving
import numpy as np

def getAllTags(years):
    expense_tag_per_year = {}
    for year in years:
        print("Processing year ",year.year_no)
        expense_tag_per_year[year.year_no] = {}
        for tag, subtags in year.tagStruct.items():
            total = 0
            for subtag, value in subtags.items():
                total -= value
            expense_tag_per_year[year.year_no][tag] = round(total, 2)
    all_tags = {}
    for tags in expense_tag_per_year.values():
        for tag, value in tags.items():
            if tag not in all_tags:
                all_tags[tag] = 0
            else:
                all_tags[tag] += value
    all_tags = dict(sorted(all_tags.items(), key=lambda x: x[1], reverse=True))

    return all_tags


def plotComparisonBarChart(expense_tag_per_year, all_tags):
    fig = plt.figure(figsize=(16, 12))
    ax = plt.gca()
    base_colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF',
                   '#FECB52']
    colors = []
    alphas = np.linspace(1, 0.35,
                         len(all_tags.keys()) // len(base_colors) + 1 * (len(all_tags.keys()) % len(base_colors) > 0))
    for i in range(0, len(all_tags.keys()) // len(base_colors)):
        for h in base_colors:
            colors.append([int(h[1:3], 16) / 255.0, int(h[3:5], 16) / 255.0, int(h[5:7], 16) / 255.0, alphas[i]])
    for j in range(0, len(all_tags.keys()) % len(base_colors)):
        colors.append([int(h[1:3], 16) / 255.0, int(h[3:5], 16) / 255.0, int(h[5:7], 16) / 255.0, alphas[i + 1]])

    colormap = {tag: color for tag, color in zip(all_tags.keys(), colors)}
    patches = {}
    for year, tags in expense_tag_per_year.items():
        tags_sorted = {k: v for k, v in sorted(tags.items(), key=lambda item: item[1], reverse=False)}
        bottom = 0
        patches[year] = {}
        for tag, value in list(tags_sorted.items()):
            patch = ax.bar(str(year), value, bottom=bottom, label=tag, color=colormap[tag])
            child = patch.get_children()[0]
            patches[year][tag] = child
            (x1, y1) = child.get_xy()
            width1 = child.get_width()
            height1 = child.get_height()
            if value > 300:
                x_text = 0.05 * width1 + x1
                y_text = 0.4 * height1 + y1
                ax.text(x_text, y_text, tag, color="white")
            if year > min(expense_tag_per_year.keys()):
                prev_child = patches[year - 1][tag]
                (x0, y0) = prev_child.get_xy()
                width0 = prev_child.get_width()
                height0 = prev_child.get_height()
                coord = [[x0 + width0, y0], [x1, y1], [x1, y1 + height1], [x0 + width0, y0 + height0]]
                coord.append(coord[0])
                xs, ys = zip(*coord)
                ax.fill(xs, ys, color=colormap[tag],linewidth=0.0)
            bottom += value
    #plt.yticks([])
    ax.tick_params(axis='x', which='major', labelsize=20)
    ax.tick_params(axis='x', which='both', bottom=True,
                    top=False, labelbottom=True)
    ax.tick_params(axis='y', which='both', right=False,
                    left=False, labelleft=False)
    for pos in ['right', 'top', 'left','bottom']:
        plt.gca().spines[pos].set_visible(False)

    file_name = "ExpenseComparison" + str(year)
    graph_path = prepare4Saving(file_name, vector=True)
    fig.savefig(graph_path, bbox_inches="tight", dpi='figure')

def getExpensesPerTagOverTheYears(years,all_tags):
    expense_tag_per_year_completed = {}
    for tag in all_tags.keys():
        for year in years:
            expense_tag_per_year_completed[year.year_no] = {}
            for tag in all_tags.keys():
                expense_tag_per_year_completed[year.year_no][tag] = 0
            for tag, subtags in year.tagStruct.items():
                total = 0
                for subtag, value in subtags.items():
                    total -= value
                expense_tag_per_year_completed[year.year_no][tag] = round(total, 2)
    return expense_tag_per_year_completed


def getMonthsYears(years):
    months_years = []
    for year in years:
        months = []
        for i in range(1, 13):
            month = Month(i, year.year_no)
            if len(month.monthly_transacts) > 0:
                months.append(month)
        months_years.append(months)

if __name__ == '__main__':
    computeBalances()
    year_22 = Year(2022)
    plotComparisonBarChartForYears(year_22,year_to_stop=2019)
    #years = [year_19,year_20,year_21,year_22]
    #all_tags = getAllTags(years)
    #expense_tag_per_year_completed = getExpensesPerTagOverTheYears(all_tags)
    #plotComparisonBarChart(expense_tag_per_year_completed,all_tags)

