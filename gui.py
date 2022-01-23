import tkinter as tk

from import_automation import activateImport
from Month import executeCreateSingleMonth,executeAssignPayback

def on_entry_click(event):
    """function that gets called whenever month_text_field.is clicked"""
    if event.widget.get() == 'Month' or 'Year':
       event.widget.delete(0, "end") # delete all the text in the entry
       event.widget.insert(0, '') #Insert blank for user input
       event.widget.config(fg = 'black')
def on_focusout(event):
    if event.widget.get() == '':
        if event.widget == app.month_text_field:
            event.widget.insert(0, 'Month')
        if event.widget == app.year_text_field:
            event.widget.insert(0, 'Year')
        event.widget.config(fg = 'grey')

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        import_activation_btn = tk.Button(text="Activate Import",command=lambda: activateImport())
        import_activation_btn.grid(column=0,row=0,columnspan = 3, pady = 10)

        self.month_text_field = tk.Entry()
        self.month_text_field.insert(0, 'Month')
        self.month_text_field.bind('<FocusIn>', on_entry_click)
        self.month_text_field.bind('<FocusOut>', on_focusout)
        self.month_text_field.config(fg='grey')
        self.month_text_field.grid(column=0,row=1,padx=10, pady = 10)


        self.year_text_field = tk.Entry()
        self.year_text_field.insert(0, 'Year')
        self.year_text_field.bind('<FocusIn>', on_entry_click)
        self.year_text_field.bind('<FocusOut>', on_focusout)
        self.year_text_field.config(fg='grey')
        self.year_text_field.grid(column=1, row=1, padx=10,pady=10)

        create_month_button = tk.Button(text="Create Balance Sheet",command=lambda: executeCreateSingleMonth(int(self.month_text_field.get()),int(self.year_text_field.get())))
        create_month_button.grid(column=2, row=1,padx=10, pady=10)
        assign_pb_button = tk.Button(text="Assign Payback",command=lambda: executeAssignPayback(int(self.month_text_field.get()),int(self.year_text_field.get())))
        assign_pb_button.grid(column=3, row=1, padx=10, pady=10)


def launchGUI():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()


if __name__ == '__main__':
    launchGUI()