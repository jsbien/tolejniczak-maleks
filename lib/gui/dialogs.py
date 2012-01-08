# encoding=UTF-8
# Copyright © 2008, 2009 Jakub Wilk <jwilk@jwilk.net>
# Copyright © 2010, 2011 Tomasz Olejniczak <tomek.87k@poczta.onet.pl>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import wx
from maleks.i18n import _

class CloneDialog(wx.Dialog):

    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        panel = wx.Panel(self)
        sizer = wx.FlexGridSizer(4, 2)
        sizer.AddGrowableCol(1, 1)
        self.__original = wx.TextCtrl(panel, wx.ID_ANY)
        self.__ficheActual = wx.TextCtrl(panel, wx.ID_ANY)
        self.__cloneActual = wx.TextCtrl(panel, wx.ID_ANY)
        sizer.Add(wx.StaticText(panel, label=_("Original entry")), 0)
        sizer.Add(self.__original, 1, wx.EXPAND)
        sizer.Add(wx.StaticText(panel, label=_("Actual entry of original fiche")), 0)
        sizer.Add(self.__ficheActual, 1, wx.EXPAND)
        sizer.Add(wx.StaticText(panel, label=_("Actual entry of clone")), 0)
        sizer.Add(self.__cloneActual, 1, wx.EXPAND)
        self.__OKButton = wx.Button(panel, label=_("OK"))
        self.__cancelButton = wx.Button(panel, label=_("Cancel"))
        sizer.Add(self.__OKButton)
        sizer.Add(self.__cancelButton)
        panel.SetSizerAndFit(sizer)
        self.__OKButton.Bind(wx.EVT_BUTTON, self.__onOK)
        self.__cancelButton.Bind(wx.EVT_BUTTON, self.__onCancel)

   # def ShowModal(self):
   #     wx.Dialog.ShowModal(self)
   #     self.__

    def setEntry(self, original, actual):
        self.__original.SetValue(original)
        self.__ficheActual.SetValue(actual)
        self.__cloneActual.SetValue(actual)
        if self.__original.GetValue() == "":
            self.__original.SetFocus()
        else:
            self.__cloneActual.SetFocus()

    def __onOK(self, event):
        self.EndModal(wx.ID_OK)
    
    def __onCancel(self, event):
        self.EndModal(wx.ID_CANCEL)
    
    def GetValue(self):
        return (self.__original.GetValue(), self.__ficheActual.GetValue(), self.__cloneActual.GetValue())

class ProgressDialog(wx.ProgressDialog):

    def __init__(self, title, message, maximum = 100, parent = None, style = wx.PD_AUTO_HIDE | wx.PD_APP_MODAL):
        wx.ProgressDialog.__init__(self, title, message, maximum, parent, style)
        self.__max = maximum
        self.__n = 0

    try:
        wx.ProgressDialog.Pulse
    except AttributeError:
        def Pulse(self):
            self.__n = (self.__n + 1) % self.__max
            self.Update(self.__n)

try:
    NumberEntryDialog = wx.NumberEntryDialog
except AttributeError:
    class NumberEntryDialog(wx.SingleChoiceDialog):
        def __init__(self, parent, message, prompt, caption, value, min, max, pos = wx.DefaultPosition):
            wx.SingleChoiceDialog.__init__(self, parent = parent, message = message, caption = caption, choices = map(str, xrange(min, max + 1)), pos = pos)
            self.SetSelection(value - min)

        def GetValue(self):
            return int(wx.SingleChoiceDialog.GetStringSelection(self))

__all__ = 'ProgressDialog', 'NumberEntryDialog', 'CloneDialog'

# vim:ts=4 sw=4 et
