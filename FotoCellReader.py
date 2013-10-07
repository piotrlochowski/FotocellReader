#!/usr/bin/env python
import base64
import json
import urllib2

import wx
import serial
import threading

#----------------------------------------------------------------------
# Create an own event type, so that GUI updates can be delegated
# this is required as on some platforms only the main thread can
# access the GUI without crashing. wxMutexGuiEnter/wxMutexGuiLeave
# could be used too, but an event is more elegant.

SERIALRX = wx.NewEventType()
# bind to serial data receive events
EVT_SERIALRX = wx.PyEventBinder(SERIALRX, 0)


class SerialRxEvent(wx.PyCommandEvent):
    eventType = SERIALRX

    def __init__(self, windowID, driver, time):
        wx.PyCommandEvent.__init__(self, self.eventType, windowID)
        self.data = "Kierowca nr %d, uzyskal czas: %s\n" % (driver, time)
        self.driver = driver
        self.time = time

    def Clone(self):
        self.__class__(self.GetId(), self.data)

#----------------------------------------------------------------------

ID_CLEAR = wx.NewId()
ID_SAVEAS = wx.NewId()
ID_SETTINGS = wx.NewId()
ID_TERM = wx.NewId()
ID_EXIT = wx.NewId()

NEWLINE_CR = 0
NEWLINE_LF = 1
NEWLINE_CRLF = 2


class TerminalSetup:
    """Placeholder for various terminal settings. Used to pass the
       options to the TerminalSettingsDialog."""

    def __init__(self):
        self.echo = False
        self.unprintable = False
        self.newline = NEWLINE_CRLF


SHOW_BAUDRATE = 1 << 0
SHOW_FORMAT = 1 << 1
SHOW_FLOW = 1 << 2
SHOW_TIMEOUT = 1 << 3
SHOW_ALL = SHOW_BAUDRATE | SHOW_FORMAT | SHOW_FLOW | SHOW_TIMEOUT


class SerialConfigDialog(wx.Dialog):
    """Serial Port confiuration dialog, to be used with pyserial 2.0+
       When instantiating a class of this dialog, then the "serial" keyword
       argument is mandatory. It is a reference to a serial.Serial instance.
       the optional "show" keyword argument can be used to show/hide different
       settings. The default is SHOW_ALL which coresponds to 
       SHOW_BAUDRATE|SHOW_FORMAT|SHOW_FLOW|SHOW_TIMEOUT. All constants can be
       found in ths module (not the class)."""

    def __init__(self, *args, **kwds):
        #grab the serial keyword and remove it from the dict
        self.serial = kwds['serial']
        del kwds['serial']
        self.show = SHOW_ALL
        if kwds.has_key('show'):
            self.show = kwds['show']
            del kwds['show']
            # begin wxGlade: SerialConfigDialog.__init__
        # end wxGlade
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_2 = wx.StaticText(self, -1, "Port")
        self.combo_box_port = wx.ComboBox(self, -1, choices=["dummy1", "dummy2", "dummy3", "dummy4", "dummy5"],
                                          style=wx.CB_DROPDOWN)
        if self.show & SHOW_BAUDRATE:
            self.label_1 = wx.StaticText(self, -1, "Baudrate")
            self.choice_baudrate = wx.Choice(self, -1, choices=["choice 1"])
        if self.show & SHOW_FORMAT:
            self.label_3 = wx.StaticText(self, -1, "Data Bits")
            self.choice_databits = wx.Choice(self, -1, choices=["choice 1"])
            self.label_4 = wx.StaticText(self, -1, "Stop Bits")
            self.choice_stopbits = wx.Choice(self, -1, choices=["choice 1"])
            self.label_5 = wx.StaticText(self, -1, "Parity")
            self.choice_parity = wx.Choice(self, -1, choices=["choice 1"])
        if self.show & SHOW_TIMEOUT:
            self.checkbox_timeout = wx.CheckBox(self, -1, "Use Timeout")
            self.text_ctrl_timeout = wx.TextCtrl(self, -1, "")
            self.label_6 = wx.StaticText(self, -1, "seconds")
        if self.show & SHOW_FLOW:
            self.checkbox_rtscts = wx.CheckBox(self, -1, "RTS/CTS")
            self.checkbox_xonxoff = wx.CheckBox(self, -1, "Xon/Xoff")
        self.button_ok = wx.Button(self, -1, "OK")
        self.button_cancel = wx.Button(self, -1, "Cancel")

        self.__set_properties()
        self.__do_layout()
        #fill in ports and select current setting
        index = 0
        self.combo_box_port.Clear()
        for n in range(4):
            portname = serial.device(n)
            self.combo_box_port.Append(portname)
            if self.serial.portstr == portname:
                index = n
        if self.serial.portstr is not None:
            self.combo_box_port.SetValue(str(self.serial.portstr))
        else:
            self.combo_box_port.SetSelection(index)
        if self.show & SHOW_BAUDRATE:
            #fill in badrates and select current setting
            self.choice_baudrate.Clear()
            for n, baudrate in enumerate(self.serial.BAUDRATES):
                self.choice_baudrate.Append(str(baudrate))
                if self.serial.baudrate == baudrate:
                    index = n
            self.choice_baudrate.SetSelection(index)
        if self.show & SHOW_FORMAT:
            #fill in databits and select current setting
            self.choice_databits.Clear()
            for n, bytesize in enumerate(self.serial.BYTESIZES):
                self.choice_databits.Append(str(bytesize))
                if self.serial.bytesize == bytesize:
                    index = n
            self.choice_databits.SetSelection(index)
            #fill in stopbits and select current setting
            self.choice_stopbits.Clear()
            for n, stopbits in enumerate(self.serial.STOPBITS):
                self.choice_stopbits.Append(str(stopbits))
                if self.serial.stopbits == stopbits:
                    index = n
            self.choice_stopbits.SetSelection(index)
            #fill in parities and select current setting
            self.choice_parity.Clear()
            for n, parity in enumerate(self.serial.PARITIES):
                self.choice_parity.Append(str(serial.PARITY_NAMES[parity]))
                if self.serial.parity == parity:
                    index = n
            self.choice_parity.SetSelection(index)
        if self.show & SHOW_TIMEOUT:
            #set the timeout mode and value
            if self.serial.timeout is None:
                self.checkbox_timeout.SetValue(False)
                self.text_ctrl_timeout.Enable(False)
            else:
                self.checkbox_timeout.SetValue(True)
                self.text_ctrl_timeout.Enable(True)
                self.text_ctrl_timeout.SetValue(str(self.serial.timeout))
        if self.show & SHOW_FLOW:
            #set the rtscts mode
            self.checkbox_rtscts.SetValue(self.serial.rtscts)
            #set the rtscts mode
            self.checkbox_xonxoff.SetValue(self.serial.xonxoff)
            #attach the event handlers
        self.__attach_events()

    def __set_properties(self):
        # begin wxGlade: SerialConfigDialog.__set_properties
        # end wxGlade
        self.SetTitle("Serial Port Configuration")
        if self.show & SHOW_TIMEOUT:
            self.text_ctrl_timeout.Enable(0)
        self.button_ok.SetDefault()

    def __do_layout(self):
        # begin wxGlade: SerialConfigDialog.__do_layout
        # end wxGlade
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_basics = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Basics"), wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5.Add(self.label_2, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_5.Add(self.combo_box_port, 1, 0, 0)
        sizer_basics.Add(sizer_5, 0, wx.RIGHT | wx.EXPAND, 0)
        if self.show & SHOW_BAUDRATE:
            sizer_baudrate = wx.BoxSizer(wx.HORIZONTAL)
            sizer_baudrate.Add(self.label_1, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_baudrate.Add(self.choice_baudrate, 1, wx.ALIGN_RIGHT, 0)
            sizer_basics.Add(sizer_baudrate, 0, wx.EXPAND, 0)
        sizer_2.Add(sizer_basics, 0, wx.EXPAND, 0)
        if self.show & SHOW_FORMAT:
            sizer_8 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_format = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Data Format"), wx.VERTICAL)
            sizer_6.Add(self.label_3, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_6.Add(self.choice_databits, 1, wx.ALIGN_RIGHT, 0)
            sizer_format.Add(sizer_6, 0, wx.EXPAND, 0)
            sizer_7.Add(self.label_4, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_7.Add(self.choice_stopbits, 1, wx.ALIGN_RIGHT, 0)
            sizer_format.Add(sizer_7, 0, wx.EXPAND, 0)
            sizer_8.Add(self.label_5, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_8.Add(self.choice_parity, 1, wx.ALIGN_RIGHT, 0)
            sizer_format.Add(sizer_8, 0, wx.EXPAND, 0)
            sizer_2.Add(sizer_format, 0, wx.EXPAND, 0)
        if self.show & SHOW_TIMEOUT:
            sizer_timeout = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Timeout"), wx.HORIZONTAL)
            sizer_timeout.Add(self.checkbox_timeout, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_timeout.Add(self.text_ctrl_timeout, 0, 0, 0)
            sizer_timeout.Add(self.label_6, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_2.Add(sizer_timeout, 0, 0, 0)
        if self.show & SHOW_FLOW:
            sizer_flow = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Flow Control"), wx.HORIZONTAL)
            sizer_flow.Add(self.checkbox_rtscts, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_flow.Add(self.checkbox_xonxoff, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_flow.Add((10, 10), 1, wx.EXPAND, 0)
            sizer_2.Add(sizer_flow, 0, wx.EXPAND, 0)
        sizer_3.Add(self.button_ok, 0, 0, 0)
        sizer_3.Add(self.button_cancel, 0, 0, 0)
        sizer_2.Add(sizer_3, 0, wx.ALL | wx.ALIGN_RIGHT, 4)
        self.SetAutoLayout(1)
        self.SetSizer(sizer_2)
        sizer_2.Fit(self)
        sizer_2.SetSizeHints(self)
        self.Layout()

    def __attach_events(self):
        wx.EVT_BUTTON(self, self.button_ok.GetId(), self.OnOK)
        wx.EVT_BUTTON(self, self.button_cancel.GetId(), self.OnCancel)
        if self.show & SHOW_TIMEOUT:
            wx.EVT_CHECKBOX(self, self.checkbox_timeout.GetId(), self.OnTimeout)

    def OnOK(self, events):
        success = True
        self.serial.port = str(self.combo_box_port.GetValue())
        if self.show & SHOW_BAUDRATE:
            self.serial.baudrate = self.serial.BAUDRATES[self.choice_baudrate.GetSelection()]
        if self.show & SHOW_FORMAT:
            self.serial.bytesize = self.serial.BYTESIZES[self.choice_databits.GetSelection()]
            self.serial.stopbits = self.serial.STOPBITS[self.choice_stopbits.GetSelection()]
            self.serial.parity = self.serial.PARITIES[self.choice_parity.GetSelection()]
        if self.show & SHOW_FLOW:
            self.serial.rtscts = self.checkbox_rtscts.GetValue()
            self.serial.xonxoff = self.checkbox_xonxoff.GetValue()
        if self.show & SHOW_TIMEOUT:
            if self.checkbox_timeout.GetValue():
                try:
                    self.serial.timeout = float(self.text_ctrl_timeout.GetValue())
                except ValueError:
                    dlg = wx.MessageDialog(self, 'Timeout must be a numeric value',
                                           'Value Error', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    success = False
            else:
                self.serial.timeout = None
        if success:
            self.EndModal(wx.ID_OK)

    def OnCancel(self, events):
        self.EndModal(wx.ID_CANCEL)

    def OnTimeout(self, events):
        if self.checkbox_timeout.GetValue():
            self.text_ctrl_timeout.Enable(True)
        else:
            self.text_ctrl_timeout.Enable(False)

# end of class SerialConfigDialog


class TerminalFrame(wx.Frame):
    """Simple terminal program for wxPython"""

    def __init__(self, parent, title):

        self.serial = serial.Serial()
        self.serial.timeout = 0.5   #make sure that the alive event can be checked from time to time
        self.settings = TerminalSetup() #placeholder for the settings
        self.thread = None
        self.alive = threading.Event()

        wx.Frame.__init__(self, parent, title='Aktualne przejazdy', size=(1024, 786))

        #Status bar
        self.CreateStatusBar()

        #Menu
        fileMenu = wx.Menu()

        # wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
        self.menuFileAbout = fileMenu.Append(wx.ID_ABOUT, "&O programie", "Written by GaZiK")
        self.menuFileExit = fileMenu.Append(wx.ID_EXIT, "&Wyjscie", "Wylacz program")

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&Plik") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        self.text_ctrl_output = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY)



        ##############


        """# Menu Bar
        self.frame_terminal_menubar = wx.MenuBar()
        self.SetMenuBar(self.frame_terminal_menubar)
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(ID_CLEAR, "&Clear", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(ID_SAVEAS, "&Save Text As...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(ID_SETTINGS, "&Port Settings...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(ID_TERM, "&Terminal Settings...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(ID_EXIT, "&Exit", "", wx.ITEM_NORMAL)
        self.frame_terminal_menubar.Append(wxglade_tmp_menu, "&File")
        # Menu Bar end"""

        self.__set_properties()
        self.__do_layout()

        self.text_ctrl_output.WriteText('Wyniki:\n')

        # end wxGlade
        self.__attach_events()          #register events
        self.OnPortSettings(None)       #call setup dialog on startup, opens port
        if not self.alive.isSet():
            self.Close()

    def StartThread(self):
        """Start the receiver thread"""
        self.thread = threading.Thread(target=self.ComPortThread)
        self.thread.setDaemon(1)
        self.alive.set()
        self.thread.start()

    def StopThread(self):
        """Stop the receiver thread, wait util it's finished."""
        if self.thread is not None:
            self.alive.clear()          #clear alive event for thread
            self.thread.join()          #wait until thread has finished
            self.thread = None

    def __set_properties(self):
        # begin wxGlade: TerminalFrame.__set_properties
        self.SetTitle("Czytnik przejazdow")
        self.SetSize((800, 600))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: TerminalFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.text_ctrl_output, 1, wx.EXPAND, 0)
        #sizer_1.Add(self.text_ctrl_output, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        self.SetAutoLayout(1)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def __attach_events(self):
    #Set event
        self.Bind(wx.EVT_MENU, self.onAbout, self.menuFileAbout)
        self.Bind(wx.EVT_MENU, self.onExit, self.menuFileExit)

        #register events at the controls
        """self.Bind(wx.EVT_MENU, self.OnClear, id = ID_CLEAR)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, id = ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnExit, id = ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnPortSettings, id = ID_SETTINGS)
        self.Bind(wx.EVT_MENU, self.OnTermSettings, id = ID_TERM)"""
        self.text_ctrl_output.Bind(wx.EVT_CHAR, self.OnKey)
        self.Bind(EVT_SERIALRX, self.OnSerialRead)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def onExit(self, event):
        """Menu point Exit"""
        self.Close()

    def OnClose(self, event):
        """Called on application shutdown."""
        self.StopThread()               #stop reader thread
        self.serial.close()             #cleanup
        self.Destroy()                  #close windows, exit app

    def OnSaveAs(self, event):
        """Save contents of output window."""
        filename = None
        dlg = wx.FileDialog(None, "Save Text As...", ".", "", "Text File|*.txt|All Files|*", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        dlg.Destroy()

        if filename is not None:
            f = file(filename, 'w')
            text = self.text_ctrl_output.GetValue()
            if type(text) == unicode:
                text = text.encode("latin1")    #hm, is that a good asumption?
            f.write(text)
            f.close()

    def OnClear(self, event):
        """Clear contents of output window."""
        self.text_ctrl_output.Clear()

    def OnPortSettings(self, event=None):
        """Show the portsettings dialog. The reader thread is stopped for the
           settings change."""
        if event is not None:           #will be none when called on startup
            self.StopThread()
            self.serial.close()
        ok = False
        while not ok:
            dialog_serial_cfg = SerialConfigDialog(None, -1, "",
                                                   show=SHOW_BAUDRATE | SHOW_FORMAT | SHOW_FLOW,
                                                   serial=self.serial
            )
            result = dialog_serial_cfg.ShowModal()
            dialog_serial_cfg.Destroy()
            #open port if not called on startup, open it on startup and OK too
            if result == wx.ID_OK or event is not None:
                try:
                    self.serial.open()
                except serial.SerialException, e:
                    dlg = wx.MessageDialog(None, str(e), "Serial Port Error", wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                else:
                    self.StartThread()
                    self.SetTitle("Serial Terminal on %s [%s, %s%s%s%s%s]" % (
                        self.serial.portstr,
                        self.serial.baudrate,
                        self.serial.bytesize,
                        self.serial.parity,
                        self.serial.stopbits,
                        self.serial.rtscts and ' RTS/CTS' or '',
                        self.serial.xonxoff and ' Xon/Xoff' or '',
                    )
                    )
                    ok = True
            else:
                #on startup, dialog aborted
                self.alive.clear()
                ok = True

    def OnTermSettings(self, event):
        """Menu point Terminal Settings. Show the settings dialog
           with the current terminal settings"""
        dialog = TerminalSettingsDialog(None, -1, "", settings=self.settings)
        result = dialog.ShowModal()
        dialog.Destroy()

    def OnKey(self, event):
        """Key event handler. if the key is in the ASCII range, write it to the serial port.
           Newline handling and local echo is also done here."""
        code = event.GetKeyCode()
        if code < 256:                          #is it printable?
            if code == 13:                      #is it a newline? (check for CR which is the RETURN key)
                if self.settings.echo:          #do echo if needed
                    self.text_ctrl_output.AppendText('\n')
                if self.settings.newline == NEWLINE_CR:
                    self.serial.write('\r')     #send CR
                elif self.settings.newline == NEWLINE_LF:
                    self.serial.write('\n')     #send LF
                elif self.settings.newline == NEWLINE_CRLF:
                    self.serial.write('\r\n')   #send CR+LF
            else:
                char = chr(code)
                if self.settings.echo:          #do echo if needed
                    self.text_ctrl_output.WriteText(char)
                self.serial.write(char)         #send the charcater
        else:
            print
            "Extra Key:", code

    def OnSerialRead(self, event):
        """Handle input from the serial port."""
        text = event.data
        self.text_ctrl_output.WriteText(text)
        self.sendLapTime(event.time)


    def readNumber(self):
        return self.translate(self.serial.read(1))

    def sendLapTime(self, time):
        url = "http://localhost:8000/py/api/v1/lap/?format=json"
        data = {"lap_nr": 1, "penalty": "11:08:26", "penalty_value": "22", "time": time, "trial_result": "/py/api/v1/trial_result/1/"}

        auth = 'Basic %s' % base64.encodestring('%s:%s' % ('piziem', 'pass4pizi'))[:-1]

        req = urllib2.Request(url, json.dumps(data), {'content-type': 'application/json', 'Authorization': auth})
        response_stream = urllib2.urlopen(req)
        response = response_stream.read()

    def ComPortThread(self):
        """Thread that handles the incomming traffic. Does the basic input
           transformation (newlines) and generates an SerialRxEvent"""
        while self.alive.isSet():               #loop while alive event is true
            text = self.translate(self.serial.read(1))          #read one, with timout
            #print "command ",text
            if text == 0:                            #check if not timeout
                driver = self.readNumber()
                time = "%02d:%02d:%02d" % (self.readNumber(), self.readNumber(), self.readNumber())
                event = SerialRxEvent(self.GetId(), driver, time)
                self.GetEventHandler().AddPendingEvent(event)

    def onAbout(self, event):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self, "To czytnik fotokomorki", "O czytniku slow kilka", wx.OK)
        dlg.ShowModal() # Show it
        dlg.Destroy() # finally destroy it when finished.

    def translate(self, x):
        #print "mam", x
        if len(x) > 0:
            if x.count('\\x') > 0:
                replace(x, '\\X' '0x')
                #    result.append(int(x, 16))
                #print "oddaje", x
                return int(x, 16)
            else:
                #result.append(ord(x))
                #print "oddaje", ord(x)
                return (ord(x))

# end of class TerminalFrame

class MyApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        frame_terminal = TerminalFrame(None, "Czytnik")
        self.SetTopWindow(frame_terminal)
        frame_terminal.Show(1)
        return 1

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
