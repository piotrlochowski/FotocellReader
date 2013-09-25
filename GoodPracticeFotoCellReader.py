#!/usr/bin/env python
import wx

class DemoPanel(wx.Panel):
    """This Panel hold two simple buttons, but doesn't really do anything."""
    def __init__(self, parent, *args, **kwargs):
        """Create the DemoPanel."""
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.parent = parent  # Sometimes one can use inline Comments
        
        NothingBtn = wx.Button(self, label="Do Nothing with a long label")
        NothingBtn.Bind(wx.EVT_BUTTON, self.DoNothing )

        MsgBtn = wx.Button(self, label="Send Message")
        MsgBtn.Bind(wx.EVT_BUTTON, self.OnMsgBtn )
    
        SerialTerminal = wx.TextCtrl(self, size=(800,200), style=wx.TE_MULTILINE|wx.TE_READONLY)

        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(NothingBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        Sizer.Add(MsgBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        Sizer.Add(SerialTerminal, 1, wx.ALIGN_CENTER|wx.ALL, 5)
        
        self.SetSizerAndFit(Sizer)
        SerialTerminal.WriteText('text')

    def DoNothing(self, event=None):
        """Do nothing."""
        pass

    def OnMsgBtn(self, event=None):
        """Bring up a wx.MessageDialog with a useless message."""
        dlg = wx.MessageDialog(self,
                               message='A completely useless message',
                               caption='A Message Box',
                               style=wx.OK|wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()

class ReaderFrame(wx.Frame):
    """Main Frame holding the Panel."""
    def __init__(self, *args, **kwargs):
        """Create the DemoFrame."""
        wx.Frame.__init__(self, *args, **kwargs)
        
        # Build the menu bar
        MenuBar = wx.MenuBar()

        FileMenu = wx.Menu()
        ConfigMenu = wx.Menu()

        menuFileAbout = FileMenu.Append(wx.ID_ABOUT, "&O programie", "Written by GaZiK")
        menuFileExit = FileMenu.Append(wx.ID_EXIT,"&Wyjscie","Wylacz program")
        menuConfigPort = ConfigMenu.Append(wx.ID_EDIT, "&Ustaw port", "Konfiguracja odczytu fotokomorki")
        
        self.Bind(wx.EVT_MENU, self.OnAbout, menuFileAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuFileExit)
        #self.Bind(wx.EVT_MENU, self.OnConfig, menuConfigPort)

        MenuBar.Append(FileMenu,"&Plik") # Adding the "filemenu" to the MenuBar
        #MenuBar.Append(ConfigMenu, "&Konfiguracja")
        self.SetMenuBar(MenuBar)  # Adding the MenuBar to the Frame content.

        # Add the Widget Panel
        self.Panel = DemoPanel(self)

        self.Fit()

    def OnAbout(self, event):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog( self, "To czytnik fotokomorki", "O czytniku slow kilka", wx.OK)
        dlg.ShowModal() # Show it
        dlg.Destroy() # finally destroy it when finished.
        
    def OnExit(self, event=None):
        """Exit application."""
        self.Close()

if __name__ == '__main__':
    app = wx.App()
    frame = ReaderFrame(None, title="Micro App")
    frame.Show()
    app.MainLoop()