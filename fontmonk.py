import gtk, pygtk, gobject

class FontMonk:
    def g(self, id):
        return self.b.get_object(id)
        
    def __init__(self):
        self.b = gtk.Builder()
        self.b.add_from_file('ui.glade')
        self.w = self.g('mainwin')
        self.w.show_all()
        
def main():
    fmgui = FontMonk()
    gtk.main()

if __name__ == "__main__": 
    main()