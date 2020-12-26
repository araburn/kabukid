import SBI_reader
import tkinter


import os
import tkinter as tk
import tkinter.filedialog

class File_Picker:
    def __init__(self,master,text="button"):
        self.button = tk.Button(master, text=text, font=('', 20),
                                width=24, height=1, bg='#999999', activebackground="#aaaaaa")
        self.button.bind('<ButtonPress>', self.pick)
        self.button.pack()
        
        self.file_name = tk.StringVar()
        self.file_name.set('未選択')
        label = tk.Label(textvariable=self.file_name, font=('', 12))
        label.pack()

    @property
    def filename(self):
        return self.file_name.get()

    def pick(self, event):        
        fTyp = [("", "*")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        file_name = tk.filedialog.askopenfilename(filetypes=fTyp, initialdir=iDir)
        if len(file_name) == 0:
            self.pick_cancelled()
        else:
            self.picked(file_name)

    def pick_cancelled(self):
        self.file_name.set('選択をキャンセルしました')
    
    def picked(self,filename):
        self.file_name.set(filename)
        self.picked_callback()

    def picked_callback(self):
        ds = SBI_reader.Deals(self.filename)
        ds.assign()
        path = ds.output()
        tk.messagebox.showinfo('保存先', path)

        pass



class Application(tkinter.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets(master)

    def create_widgets(self,master):
        main_frame = tk.Frame(master=master)
        self.fb = File_Picker(main_frame,text="ファイル選択")
        main_frame.pack()
        self.main_frame = main_frame


        self.quit = tkinter.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy)
        self.quit.pack(side="bottom")


root = tkinter.Tk()
app = Application(master=root)
app.mainloop()