# ViewCutter
# 画像をドラッグして長方形が一個描けてその範囲をOCRしてクリップボードにコピー
import glob
import os
import time
import json
try:
    import pyocr
    import pyocr.builders
    import pyperclip
    OCRon = True
except:
    OCRon = False
    pass
import pyautogui
import datetime
import subprocess

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Line, BindTexture, Color
from kivy.properties import ObjectProperty,ListProperty
from PIL import Image as PILImage 
from kivy.clock import Clock

from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path

resource_add_path("C:/Users/piecr/Downloads/IPAexfont00301")
LabelBase.register(DEFAULT_FONT, "ipaexg.ttf")

IndexFile ='_index.json'

class ColumnBox():
    def __init__(self, **kwargs):
        self.top = 0
        self.left = 0
        self.width = 0
        self.height = 0
        self.grav = 0
        self.nonble
        
class AnnoBox():
    def __init__(self, **kwargs):
        self.top = 0
        self.left = 0
        self.width = 0
        self.height = 0
        self.grav = 0
        self.ano = ""

class PageFile():
    def __init__(self, **kwargs):
        self.name = ""
        self.columns = []
        self.annos = []

class Book(object):
    def __init__(self, **kwargs):
        self.cno = 0
        self.plist = []
        pass
    
    def setdir( self, dpath):
        
        os.chdir(dpath)
        self.plist.clear()
        
        try:
            jf=open(IndexFile, 'r')
            job=json.load(jf)
            print(job)
            for p in job['ls']:
                self.plist.append(p['pic'])
        except:
            for p in glob.glob('*.*'):
                self.plist.append(p)

        self.cno = 0

    def setfile(self, fpath):
        try:
            self.cno = self.plist.index(fpath)
        except:
            print( "setfile ValueError", fpath )
            self.cno = 0
        pass

    def next(self):
        self.cno = self.cno + 1
        if( self.cno >= len(self.plist) ):
            self.cno = len(self.plist) - 1
        return self.current()

    def before(self):
        if( len(self.plist)==0 ):
            return ""
        self.cno = self.cno - 1
        if( self.cno < 0 ):
            self.cno = 0
        return self.current()

    def current(self):
        if( len(self.plist)==0 ):
            MyApp.title = "0/0 -"
            return ""
        MyApp.title = "{}/{} - {}".format(self.cno+1, len(self.plist), self.plist[self.cno])
        return self.plist[self.cno]

    def setno( self, no ):
        self.cno = no
        return self.plist[self.cno]
    
    def length(self):
        return len(self.plist)

    def getlist(self):
        return self.plist

 
class AreaRect(object):
    def __init__(self, canvas):
        self.Canvas = canvas
        self.Inst0 = Line(rounded_rectangle=(0,0,0,0,5), dash_length=0.5)
        self.Inst1 = Line(rounded_rectangle=(0,0,0,0,5), dash_length=0.5)
        self.Canvas.add( Color(1,0,0) )
        self.Canvas.add( self.Inst0 )
        self.Canvas.add( Color(1,1,1) )
        self.Canvas.add( self.Inst1 )
        self.InstRect = None
        self.ratio = 1
        self.bias = 76
        pass

    def setRatioBias(self, ratio, bias ):
        self.ratio = ratio
        self.bias = bias

    def setRect(self,prect):
        sx, sy, w, h = prect
        if( w < 0 ):
            sx = sx + w
            w = -w
        if( h < 0 ):
            sy = sy + h
            h = -h
        rect = sx, sy, w, h
        self.InstRect = rect
        self.Inst0.rounded_rectangle = rect+(5,)
        self.Inst1.rounded_rectangle = (rect[0]+1,rect[1]+1,rect[2]-2,rect[3]-2)+(5,)
        pass

    def getRect(self):
        return self.InstRect

    def getRealRect(self):
        return (self.InstRect[0]/self.ratio, (self.InstRect[1]-self.bias)/self.ratio, self.InstRect[2]/self.ratio, self.InstRect[3]/self.ratio)
        
    def setRealRect(self, rect):
        rect = (rect[0]*self.ratio, rect[1]*self.ratio, rect[2]*self.ratio, rect[3]*self.ratio)
        self.setRect((rect[0],rect[1]+self.bias,rect[2],rect[3]))
        pass

class ImageBoard(object):
    def __init__(self, widget):
        self.imageWidget = widget
        self.Image = None
        self.ImageSrc = None
        self.imageRect = None
        self.areaRect = None
        self.ratio = 1
        self.Areas = []

    def setImageSrc(self, src ):
        if( self.imageRect == None ):
            try:
                self.imageRect = Rectangle(source=src, size=self.imageWidget.size, pos=(0,76))
                self.imageWidget.canvas.add(self.imageRect)
            except:
                pass
        else:
            try:
                self.imageRect.source=src
            except:
                self.imageRect.source=""
                pass

        if( self.Image != None ):
            self.Image.close()
        try:
            self.Image = PILImage.open(src)
        except:
            self.ImageSrc = ""
            self.ratio = 1
            self.imageOrgSize = self.imageWidget.size
            return
        self.ImageSrc = src
        self.imageOrgSize = self.Image.size
        
        if( self.imageWidget.size[0] < self.imageWidget.size[1] ):
            self.ratio = self.imageWidget.size[0]/self.imageOrgSize[0]
        else:
            self.ratio = self.imageWidget.size[1]/self.imageOrgSize[1]
        

    def setSize( self, size ):
        if( self.imageRect == None ):
            return
        if( self.areaRect!=None):
            rect = self.areaRect.getRealRect()
        self.imageWidget.size_hint=(None, None)
        self.imageWidget.size = size
        
        if( self.imageWidget.size[0] < self.imageWidget.size[1] ):
            self.ratio = self.imageWidget.size[0]/self.imageOrgSize[0]
            self.imageRect.size=(self.imageWidget.size[0], (self.ratio)*self.imageOrgSize[1])
        else:
            self.ratio = self.imageWidget.size[1]/self.imageOrgSize[1]
            self.imageRect.size=((self.ratio)*self.imageOrgSize[0], self.imageWidget.size[1] )
            
        if( self.areaRect!=None):
            self.areaRect.setRatioBias(self.ratio, 76)
            self.areaRect.setRealRect(rect)
        pass

    def setRect( self, rect ):
        if( self.areaRect == None ):
            self.areaRect = AreaRect(self.imageWidget.canvas)
        self.areaRect.setRect(rect)
        self.areaRect.setRatioBias(self.ratio, 76)
        pass

    def clearRect( self ):
        rect = self.imageRect.size
        self.imageWidget.canvas.clear()
        self.imageRect = None
        self.areaRect = None
        
        self.setImageSrc(self.ImageSrc)
        self.imageRect.size = rect
        pass
        
    def cutImage( self ):
        if( OCRon == False ):
            print("OCR not avalavle.")
            return
        if( self.areaRect!=None):
            rect = self.areaRect.getRealRect()
            cutrect = (int(rect[0]), int(self.Image.size[1]-rect[1]-rect[3]), int(rect[0]+rect[2]), int(self.Image.size[1]-rect[1]))
            print("scaning ",cutrect)
            cropimage = self.Image.crop(cutrect)
        #    cropimage.save( "rect.jpg" )
            txt = pyocr.get_available_tools()[0].image_to_string(
                cropimage,
                lang="jpn",
                builder=pyocr.builders.TextBuilder(tesseract_layout=6)
            )
            print( txt )
            pyperclip.copy(txt)
            print( "---" )


class AreaViewWidget( Widget ):
    viewer_box = ObjectProperty(None)
    annotation_box = ObjectProperty(None)
    button_box = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AreaViewWidget, self).__init__(**kwargs)
        self.ivm = ImageBoard( self.viewer_box )
        self.image = None
        self.touch_down_pos = (0,0)
        MyApp.book.setdir('.')
        self.setview(MyApp.book.current())
        self.rect = None
        Window.bind(on_dropfile=self._on_file_drop)
        Window.bind(on_resize=self._on_resize)

    def setLayout(self, width, height):
        self.ivm.setSize((width,height-76))
        self.annotation_box.size_hint=(None, None)
        self.annotation_box.size = (width,26)
        self.button_box.size_hint=(None, None)
        self.button_box.size = (width,50)
        pass
    
    def onImageTouch(self,event):
        self.touch_down_pos = event[1].pos
        self.ivm.clearRect()

    def onImageMove(self,event):
        touchpos = event[1].pos
        self.ivm.setRect((self.touch_down_pos[0] ,self.touch_down_pos[1],
                touchpos[0] - self.touch_down_pos[0], touchpos[1] - self.touch_down_pos[1]))

    def onImageUp(self,event):
        pass

    def sendCap(self,capfile):
        try:
            subprocess.run("adb push semaphore.txt /storage/emulated/0/kivy/OsaturnSideView/", shell=True, check=True)
            subprocess.run("adb push "+capfile+" /storage/emulated/0/kivy/OsaturnSideView/ladybug.jpg", shell=True, check=True)
            subprocess.run("adb shell rm /storage/emulated/0/kivy/OsaturnSideView/semaphore.txt", shell=True, check=True)
            self.ids["info"].text = capfile
        except:
            pass

    def captureClicked(self):
        Window.hide()
        time.sleep(0.5)
        ts = datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')
        pyautogui.screenshot("CAP"+ts+".jpg")
        self.sendCap("CAP"+ts+".jpg")
        self.addFile(os.path.realpath("CAP"+ts+".jpg"))
        Window.show()
        pass
    
    def clearbtnClicked(self):
        self.ivm.clearRect()
        for inst in self.viewer_box.canvas.children:
            print(type(inst))
            if type(inst) is Rectangle:
                print( "Rectangle", inst.source, inst.pos, inst.size )
            if type(inst) is BindTexture:
                print( "BindTexture", inst.source )
            if type(inst) is Line:
                self.viewer_box.remove_widget(inst)
                print("remove_widget")
        #    for x in dir(inst):
        #        print("  ",x)
        pass

    def nobleCheckClicked(self):
        def intervalcap(dt):
            print(MyApp.book.cno *2)
            op = MyApp.book.current()
            self.setview( op )
            self.ivm.cutImage()
            return op != MyApp.book.next()

        Clock.schedule_interval( intervalcap, 2 )  

    def backbtnClicked(self):
        self.setview(MyApp.book.before() )
        self.setLayout( Window.size[0], Window.size[1] )
    
    def forwardbtnClicked(self):
        self.setview(MyApp.book.next())
        self.setLayout( Window.size[0], Window.size[1] )
    
    def delbtnClicked(self):
        self.setview(MyApp.book.setno(0))
        for f in MyApp.book.getlist():
            self.ivm.cutImage()
            MyApp.book.next()
    
    def savebtnClicked(self):
        self.ivm.cutImage()
        
    def setview(self, fpath):
        self.ivm.setImageSrc(fpath)
    
    def _on_file_drop(self, window, file_path):
        fpath=file_path.decode(encoding='utf-8')
        self.addFile(fpath)

    def addFile(self, fpath):
        if(os.path.isfile(fpath)):
            dirpath = os.path.dirname(fpath)
            MyApp.book.setdir(dirpath)
            MyApp.book.setfile(os.path.basename(fpath))
        else:
            MyApp.book.setdir(fpath)

        self.ivm.setImageSrc(MyApp.book.current())
        self.setLayout(Window.size[0],Window.size[1])
        

    def _on_resize(self, window, a, b):
        self.setLayout( a, b )

    


class AreaViewApp(App):
    
    def __init__(self, **kwargs):
        print("AreaViewApp ",App )
        super(AreaViewApp, self).__init__(**kwargs)
        self.book = Book()
        Window.size = (1200,800)
        
    def build(self):
        print("AreaViewApp build ",App )
        self.avw =AreaViewWidget()
        return self.avw
        
if __name__ =='__main__':
#   os.chdir('../xxx')
    MyApp = AreaViewApp()
    MyApp.run()

