# ViewCutter
# 画像をドラッグして長方形が一個描けてその範囲をOCRしてクリップボードにコピー
import glob
import os
import time
import json
import datetime

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
from kivy.graphics import Rectangle, Line, BindTexture, Color, InstructionGroup
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty,ListProperty
from PIL import Image as PILImage 
from kivy.clock import Clock

from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path

try:
    resource_add_path("IPAexfont00301")
    LabelBase.register(DEFAULT_FONT, "ipaexg.ttf")
except Exception as e:
    print(e)
    pass

IndexFile ='_index.json'
ButtonMenuHeight=76

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
        try:
            MyApp.title = "{}/{} - {}".format(self.cno+1, len(self.plist), self.plist[self.cno])
            return self.plist[self.cno]
        except:
            return ""

    def setpos( self, no ):
        self.cno = no
        try:
            return self.plist[self.cno]
        except:
            return ""

    def getpos( self ):
        return self.cno
    
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
        self.bias = ButtonMenuHeight
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
        self.image = None
        self.ImageSrc = None
        self.imageRect = None
        self.areaRect = None
        self.ratio = 1
        self.areas = []
        self.PanelH = 76

    def resetRatio(self):
        if( self.imageWidget.size[0] < self.imageWidget.size[1] ):
            self.ratio = self.imageWidget.size[0]/self.imageOrgSize[0]
            self.imageRect.size=(self.imageWidget.size[0], (self.ratio)*self.imageOrgSize[1])
        else:
            self.ratio = self.imageWidget.size[1]/self.imageOrgSize[1]
            self.imageRect.size=((self.ratio)*self.imageOrgSize[0], self.imageWidget.size[1] )

    def setSize( self, size ):
        if( self.imageRect == None ):
            return
        if( self.areaRect!=None):
            rect = self.areaRect.getRealRect()
        self.imageWidget.size_hint=(None, None)
        self.imageWidget.size = size

        #self.resetRatio()
        self.setRatio()
        
        if( self.areaRect!=None):
            self.areaRect.setRatioBias(self.ratio, 76)
            self.areaRect.setRealRect(rect)

        for a in self.areas:
            rect = a.getRealRect()
            a.setRealRect(rect)


    def setRect( self, rect ):
        if( self.areaRect == None ):
            self.areaRect = AreaRect(self.imageWidget.canvas)
        self.areaRect.setRect(rect)
        self.areaRect.setRatioBias(self.ratio, 76)
        pass

    def addRealRect( self, rect ):
        area = AreaRect(self.imageWidget.canvas)
        arect = (rect[0]*self.ratio,(self.imageOrgSize[1]-rect[1]-256)*self.ratio+76,rect[2]*self.ratio,rect[3]*self.ratio)
        area.setRect(arect)
        self.areas.append(area)

    def clearRect( self ):
        self.imageWidget.canvas.clear()
        self.imageRect = None
        self.areaRect = None
        
#        self.setImageSrc(self.ImageSrc)
        pass
    
    def setImage(self, im ):
        self.image = im
        if( im != None ):
            self.imageOrgSize = self.image.size
    
    def setRatio(self):
        if( self.image == None ):
            return
        imageX = self.image.size[0]
        imageY = self.image.size[1]
        #viewX = self.imageWidget.size[0]
        #viewY = self.imageWidget.size[1]
        viewX = Window.size[0]
        viewY = Window.size[1] - self.PanelH
        
        orgasp = imageX / imageY
        wgtasp = viewX / viewY

        if( orgasp < wgtasp ):
            self.ratio = viewY / imageY
        else:
            self.ratio = viewX / imageX

        print("self.ratio", self.ratio)

    def show(self):
        if( self.image == None ):
            return
        print( "show", self.image )
        self.setRatio()

        texture = Texture.create(size=self.image.size)
        buff = self.image.tobytes()
        texture.blit_buffer(buff)
        texture.flip_vertical()

        self.imageWidget.canvas.clear()
        with self.imageWidget.canvas:
            Rectangle(pos=(0, 0), size=self.imageWidget.size)
            Rectangle(texture=texture ,pos=(0, self.PanelH), size=(self.image.size[0]*self.ratio, self.image.size[1]*self.ratio))

class AreaViewWidget( Widget ):
    viewer_box = ObjectProperty(None)
    slider_box = ObjectProperty(None)
    button_box = ObjectProperty(None)
    pageslider = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AreaViewWidget, self).__init__(**kwargs)
        MyApp.book.setdir('.')
        self.ivm = ImageBoard( self.viewer_box )
        self.image = None
        self.touch_down_pos = (0,0)
        self.setview(MyApp.book.current())
        self.rect = None
        Window.bind(on_dropfile=self._on_file_drop)
        Window.bind(on_resize=self._on_resize)
        self.initSlider()
        self.ontouchdown = False

    def initSlider(self):
        self.pageslider.max=MyApp.book.length()-1
        self.pageslider.min=0
        self.pageslider.value = int(MyApp.book.getpos())
        print("initSlider",self.pageslider.max,self.pageslider.min, self.pageslider.value)
        pass

    def setLayout(self, width, height):
        print("setLayout", width, height)
        self.ivm.setSize((width,height-ButtonMenuHeight))
        self.slider_box.size_hint=(None, None)
        self.slider_box.size = (width,26)
        self.button_box.size_hint=(None, None)
        self.button_box.size = (width,50)
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
        print("* backbtnClicked")
        self.setview(MyApp.book.before() )
        self.setLayout( Window.size[0], Window.size[1] )
    
    def forwardbtnClicked(self):
        print("* forwardbtnClicked")
        self.setview(MyApp.book.next())
        self.setLayout( Window.size[0], Window.size[1] )
    
    def delbtnClicked(self):
        self.setview(MyApp.book.setpos(0))
        for f in MyApp.book.getlist():
            self.ivm.cutImage()
            MyApp.book.next()
    
    def savebtnClicked(self):
        self.ivm.cutImage()
        
    def setview(self, fpath):
        print("setview",fpath)
        self.setImageSrc(fpath)
        self.fpath = fpath
        
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

        self.setImageSrc( MyApp.book.current() )
        
        self.initSlider()
#        print("addFile", MyApp.book.length(),MyApp.book.getpos())
#        self.ivm.setImageSrc(MyApp.book.current())
#        self.setLayout(Window.size[0],Window.size[1])

    def setImageSrc( self, src ):
        print( "setImageSrc", src )
        if( self.readImage( src ) ):
            self.vmode='color'
            self.ivm.setImage(self.image)
            self.ivm.show()
            self.setLayout(Window.size[0],Window.size[1])


    def readImage(self, file_path):
        print("readImage", file_path)
        try:
            self.fname = file_path
            if( self.image!=None):
                self.image.close()
                self.image = None
                
            # ps = self.fname.split('.')

            self.vmode = "pic"
            self.makeImage( self.vmode )
        except Exception as e:
            self.image = None
            self.ivm.setImage(None)
            print("readImage error", file_path, e)
            return False
        return True

    def makeImage(self, vmode):
        print("makeImage ",vmode)
        if( self.vmode=='color' ):
            topo = himawari.normalize( self.fv )*self.ralv
            self.image = himawari.colorize(topo, himawari.mkRadPointTbl())
        elif( self.vmode=='bw0' ):
            topo = himawari.normalize( self.fv )
            topo = ((1-topo)*255).astype(np.uint8)
            self.image = PILImage.fromarray(topo).convert("RGB")
        elif( self.vmode=='bw1' ):
            topo = himawari.normalize( self.fv )
            topo = ((topo)*255).astype(np.uint8)
            self.image = PILImage.fromarray(topo).convert("RGB")
        elif( self.vmode=='seikai' ):
            tmpim = PILImage.open(self.fname)
            topo = np.asarray(tmpim)
            self.image = himawari.colorize(topo, himawari.mkRadPointTbl2())
            tmpim.close()
        else:
            print("self.fname", self.fname)
            tmpim = PILImage.open(self.fname)
            self.image = tmpim.convert("RGB")
            print(self.image)
            tmpim.close()
        pass

    def _on_resize(self, window, a, b):
        print("on_resize", a, b)
        self.setLayout( a, b )

    def onImageTouch(self,event):
        self.touch_down_pos = event[1].pos
        self.ivm.clearRect()

    def onImageMove(self,event):
        if( self.touch_down_pos[1] < ButtonMenuHeight ):
            return
        touchpos = event[1].pos
        self.ivm.setRect((self.touch_down_pos[0] ,self.touch_down_pos[1],
                touchpos[0] - self.touch_down_pos[0], touchpos[1] - self.touch_down_pos[1]))

    def onImageUp(self,event):
        pass

    def slider_on_touch_up(self):
        print("->* slider_on_touch_up", self.pageslider.value)
        if( self.ontouchdown == True):
            MyApp.book.setpos(int(self.pageslider.value))
            self.setview(MyApp.book.current())
            self.pageslider.value = int(MyApp.book.getpos())
            print("<-* slider_on_touch_up", self.pageslider.value)
        self.ontouchdown = False
        pass

    def slider_on_touch_down(self):
        print("slider_on_touch_down", self.pageslider.value)
        self.ontouchdown = True
        pass


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

