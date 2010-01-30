import gtk, pygtk, gobject, urllib
import os

class FontMonk:
    # This list is taken from the FontForge man page.
    font_exts = {
                 "bdf": "Glyph Bitmap Dist.",
                 "bin": "Mac Resource",
                 "otf": "OpenType",
                 "sfd": "Spline Font DB",
                 "pfa": "PS ASCII",
                 "pfb": "PS binary",
                 "svg": "SVG fonts",
                 "pk": "TeX bitmap",
                 "ttf": "TrueType",
                 "ttc": "TrueType",
                 "pcf": "X11 bitmap"
                 }
    
    def g(self, id):
        return self.b.get_object(id)
        
    def __init__(self):
        self.b = gtk.Builder()
        self.b.add_from_file('ui.glade')
        self.w = self.g('mainwin')
        
        # Set up DND
        self.dndsetup()
        
        # Set up chooser
        self.chooseboxsetup()
        
        self.b.connect_signals(self)
        self.w.show_all()
        
    def dndsetup(self):
        self.treeview = self.g('mainview')
        # Model: Stock icon (shown), label (marked up, shown), path (not shown)
        self.treeview.set_model(gtk.ListStore(str, str, str))
        x = gtk.CellRendererText()
        x.markup = True
        self.treeview.append_column(gtk.TreeViewColumn('Icon', gtk.CellRendererPixbuf(), stock_id=0))        
        self.treeview.append_column(gtk.TreeViewColumn('URL', x, markup=1))
                
        self.treeview.enable_model_drag_dest([
                                                    ('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),
                                                    ('text/plain', 0, 1),
                                                    ('TEXT', 0, 2),
                                                    ('STRING', 0, 3),
                                             ],
                                             gtk.gdk.ACTION_DEFAULT)
        
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        self.treeview.connect("drag_data_received", self.drag_data_received_data)
        
    def chooseboxsetup(self):
        self.ch = self.g('choosebox')
        # Model: Label (shown), extension (not shown)
        model = gtk.ListStore(str, str)
        self.ch.set_model(model)
        self.cell = gtk.CellRendererText()
        self.ch.pack_start(self.cell, True)
        self.ch.add_attribute(self.cell, 'text', 0)
        fx = self.font_exts.items()
        fx.sort()
        for k, v in fx:
            model.append([("Output %s (%s)" % (v, k)), k]) 
        
    # Callback handlers 
    
    def quit(self, widget):
        gtk.main_quit()
    
    def del_button_clicked_cb(self, widget):
        sel = self.treeview.get_selection()
        selection = self.treeview.get_selection()
        model, selected = selection.get_selected_rows()
        iters = [model.get_iter(path) for path in selected]
        for iter in iters:
            model.remove(iter)
        
    def drag_data_received_data(self, treeview, context, x, y, selection,
                                info, etime):
        model = treeview.get_model()
        data = str(selection.data)
        files = data.splitlines()
        for file in files:
            path = str(urllib.unquote(file)).replace('file://', '')
            fname = path.split(os.sep)[-1]
            fext = fname.split('.')[-1]
            if not os.path.isfile(path):
                print data, "couldn't be turned into a path."
                context.finish(True, True, etime)
                continue
            
            if not str(fext).lower() in self.font_exts:
                print fname, "didn't match a font extension."
                context.finish(True, True, etime)
                continue
        
            label =  "%s <span color='gray'>%s</span>" % (path.split(os.sep)[-1], self.font_exts[str(fext).lower()])
            model.append([gtk.STOCK_FILE, label, path])
        return
    
def main():
    fmgui = FontMonk()
    gtk.main()

if __name__ == "__main__": 
    main()