import gtk, pygtk, gobject, urllib, os, subprocess, re
gobject.threads_init()

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
        
        self.ph = self.g('prog_header')
        self.ps = self.g('prog_subhead')
        self.pl = self.g('prog_line')
        self.pb = self.g('progress')
        
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
        # TODO: Could be prettier.
        i = 0
        for k, v in fx:
            model.append([("Output %s (%s)" % (v, k)), k])
            if (k == 'ttf'):
                j = i
            i += 1
        self.ch.set_active(j)
        
    def makescript(self):
        # Thanks to Thomas Maier for the 'quick and dirty hack'
        model = self.treeview.get_model()
        self.count = len(model)
        self.t = self.ch.get_model().get_value(self.ch.get_active_iter(), 1)
        iter = model.get_iter_root()
        s = ""
        while iter:
            v = model.get_value(iter, 2)
            s += 'Print("Opening %s");Open("%s");Print("Saving %s.%s");Generate("%s.%s");' % (v, v, v, self.t, v, self.t) 
            iter = model.iter_next(iter)
        self.runscript(s)        
        
    def runscript(self, s):
        self.ph.set_markup('<b><big>Converting <span>%s</span> files...</big></b>' % self.count)
        self.ps.set_markup('FontMonk is now converting your fonts into <span>%s</span>.' % self.t.upper())
        p = subprocess.Popen('fontforge -lang=ff -c \'%s\' &' % s, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_id = gobject.io_add_watch(p.stdout, gobject.IO_IN, self.gotline)
        hup_id = gobject.io_add_watch(p.stdout, gobject.IO_HUP, self.hup)
        
    def gotline(self, file, dunno):
        newdata = file.read().split('\n')
        if (newdata[-2]):
            self.pl.set_text(str(newdata[-2]))
        if (newdata[-1]):
            self.pl.set_text(str(newdata[-1]))
        self.pb.pulse()
        return False
    
    def hup(self, file, dunno):
        self.pl.hide()
        self.ps.set_text("Conversion finished.")
        self.pb.set_fraction(1)
        return False
        
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
            
    def add_button_clicked_cb(self, widget):
        diag = gtk.FileChooserDialog('Add a font file', None, gtk.FILE_CHOOSER_ACTION_OPEN,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        diag.set_default_response(gtk.RESPONSE_OK)        
        response = diag.run()
        if response == gtk.RESPONSE_OK:
            self.addpath(diag.get_filename())
        diag.destroy()
    
    def exec_button_clicked_cb(self, widget):
        self.pw = self.b.get_object('progresswin')
        self.w.hide()
        self.pw.show_all()
        self.makescript()
    
    def closebutton_clicked_cb(self, widget):
        self.pw.hide()
        self.w.show()
    
    def addpath(self, path):
        model = self.treeview.get_model()
        fname = path.split(os.sep)[-1]
        fext = fname.split('.')[-1]        
        if not os.path.isfile(path):
            print data, "couldn't be turned into a path."
            return
        
        if not str(fext).lower() in self.font_exts:
            print fname, "didn't match a font extension."
            return
        
        label =  "%s <span color='gray'>%s</span>" % (path.split(os.sep)[-1], self.font_exts[str(fext).lower()])
        model.append([gtk.STOCK_FILE, label, path])

        
    def drag_data_received_data(self, treeview, context, x, y, selection,
                                info, etime):
        model = treeview.get_model()
        data = str(selection.data)
        files = data.splitlines()
        for file in files:
            path = str(urllib.unquote(file)).replace('file://', '')
            self.addpath(path)
        return
    
def main():
    fmgui = FontMonk()
    gtk.main()

if __name__ == "__main__": 
    main()