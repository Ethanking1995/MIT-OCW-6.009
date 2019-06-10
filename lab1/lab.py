#!/usr/bin/env python3

import sys
import math
import base64
import tkinter

from io import BytesIO
from PIL import Image as PILImage

## NO ADDITIONAL IMPORTS ALLOWED!

class Image:
    def __init__(self, width, height, pixels):
        self.width = width
        self.height = height
        self.pixels = pixels

    def get_pixel(self, x, y):
        if x >=0 and x<self.width and y>=0 and y < self.height:
            
            index=self.width*y+x
            return self.pixels[index]

        if x < 0 and y < 0:
            return self.get_pixel(0,0)
        if x>= self.width and y >= self.height:
            return self.get_pixel(self.width-1,self.height-1)
        if x<0 and y>=self.height:
            return self.get_pixel(0,self.height-1)
        if y<0 and x >=self.width:
            return self.get_pixel(self.width-1,0)
        if x<0:
            return self.get_pixel(0,y)
        if y<0:
            return self.get_pixel(x,0)
        if x >= self.width:
            return self.get_pixel(self.width-1,y)
        if y>= self.height:
            return self.get_pixel(x,self.height-1)

    def set_pixel(self, x, y, c):
        pixel=y*self.width+x
        self.pixels[pixel]=c


    def apply_per_pixel(self, func):
        result = Image.new(self.width, self.height)
        for x in range(self.width):
            for y in range(self.height):
                color = self.get_pixel(x, y)
                newcolor = func(color)
                result.set_pixel(x, y, newcolor)
        return result
    def pixel_clipper(self):
        '''helper function that ensures each pixel in the list of pixels is an integer
        and in the valid range (between 0 & 255)'''
        for i in range(len(self.pixels)):
            self.pixels[i]=int(round(self.pixels[i]))
            if self.pixels[i] < 0:
                self.pixels[i]=0
            elif self.pixels[i]>255:
                self.pixels[i]=255
    def inverted(self):
        return self.apply_per_pixel(lambda c: 255-c)

    def correlate(self,kernel):
        '''kernel a list of n lists, each inner list with length n
        each list in the kernel represents a row. EX: the 4th list in kernel
        is a list of elements in the 4th row of kernel''' 
        result=Image.new(self.width,self.height)
        for x in range(result.width):
            for y in range(result.height):
                cor=0
                for kernx in range(len(kernel)):
                        for kerny in range(len(kernel[kernx])):
                                pixel=self.get_pixel(x-len(kernel)//2+kerny,y-len(kernel)//2+kernx)
                                val=pixel*kernel[kernx][kerny]
                                cor+=val
                
                result.set_pixel(x,y,cor)
        return result
    def CreateBlurKernel(self,n):
        '''accepts a parameter n and returns a kernel of length n with 
        sum of all values in the kernel equalling 1. n**2 values in 
        kernel so each value is 1/n**2'''
        x=n**2
        kernel=[]
        for i in range(n):
            l=[]
            for y in range(n):
                l.append(1/x)
            kernel.append(l)
        return kernel



    def blurred(self, n):
        kernel=self.CreateBlurKernel(n)
        blur= self.correlate(kernel)
        blur.pixel_clipper()
        return blur

    def sharpened(self, n):
        kernel=self.CreateBlurKernel(n)
        new_img=Image(self.width,self.height,[2*x for x in self.pixels])
        blur_image=self.correlate(kernel)
        pixels=[]
        for i in range(len(self.pixels)):
            pix=new_img.pixels[i]-blur_image.pixels[i]
            pixels.append(pix)
        result=Image(self.width,self.height,pixels)
        result.pixel_clipper()
        return result

    def edges(self):
        Kx=[[-1,0,1],[-2,0,2],[-1,0,1]]
        Ky=[[-1,-2,-1],[0,0,0],[1,2,1]]
        Ox=self.correlate(Kx)
        Oy=self.correlate(Ky)
        result=Image.new(Ox.width,Ox.height)
        for i in range(len(Ox.pixels)):
            val=(Ox.pixels[i]**2+Oy.pixels[i]**2)**.5
            result.pixels[i]=val
        result.pixel_clipper()
        return result
    def normalize(self):
        r=max(self.pixels)-min(self.pixels)
        #normalize to 0,1
        for x in self.width:
            for y in self.height:
                self.set_pixel(x,y,(self.get_pixel(x,y)-min(self.pixels))/r)
        #scale normalization to [0,255]
        r=255
        for x in self.width:
            for y in self.height:
                self.set_pixel(x,y,self.get_pixel(x,y)*r)
        self.pixel_clipper()


    # Below this point are utilities for loading, saving, and displaying
    # images, as well as for testing.

    def __eq__(self, other):
        return all(getattr(self, i) == getattr(other, i)
                   for i in ('height', 'width', 'pixels'))

    def __repr__(self):
        return "Image(%s, %s, %s)" % (self.width, self.height, self.pixels)

    @classmethod
    def load(cls, fname):
        """
        Loads an image from the given file and returns an instance of this
        class representing that image.  This also performs conversion to
        grayscale.

        Invoked as, for example:
           i = Image.load('test_images/cat.png')
        """
        with open(fname, 'rb') as img_handle:
            img = PILImage.open(img_handle)
            img_data = img.getdata()
            if img.mode.startswith('RGB'):
                pixels = [round(.299*p[0] + .587*p[1] + .114*p[2]) for p in img_data]
            elif img.mode == 'LA':
                pixels = [p[0] for p in img_data]
            elif img.mode == 'L':
                pixels = list(img_data)
            else:
                raise ValueError('Unsupported image mode: %r' % img.mode)
            w, h = img.size
            return cls(w, h, pixels)

    @classmethod
    def new(cls, width, height):
        """
        Creates a new blank image (all 0's) of the given height and width.

        Invoked as, for example:
            i = Image.new(640, 480)
        """
        return cls(width, height, [0 for i in range(width*height)])

    def save(self, fname, mode='PNG'):
        """
        Saves the given image to disk or to a file-like object.  If fname is
        given as a string, the file type will be inferred from the given name.
        If fname is given as a file-like object, the file type will be
        determined by the 'mode' parameter.
        """
        out = PILImage.new(mode='L', size=(self.width, self.height))
        out.putdata(self.pixels)
        if isinstance(fname, str):
            out.save(fname)
        else:
            out.save(fname, mode)
        out.close()

    def gif_data(self):
        """
        Returns a base 64 encoded string containing the given image as a GIF
        image.

        Utility function to make show_image a little cleaner.
        """
        buff = BytesIO()
        self.save(buff, mode='GIF')
        return base64.b64encode(buff.getvalue())

    def show(self):
        """
        Shows the given image in a new Tk window.
        """
        global WINDOWS_OPENED
        if tk_root is None:
            # if tk hasn't been properly initialized, don't try to do anything.
            return
        WINDOWS_OPENED = True
        toplevel = tkinter.Toplevel()
        # highlightthickness=0 is a hack to prevent the window's own resizing
        # from triggering another resize event (infinite resize loop).  see
        # https://stackoverflow.com/questions/22838255/tkinter-canvas-resizing-automatically
        canvas = tkinter.Canvas(toplevel, height=self.height,
                                width=self.width, highlightthickness=0)
        canvas.pack()
        canvas.img = tkinter.PhotoImage(data=self.gif_data())
        canvas.create_image(0, 0, image=canvas.img, anchor=tkinter.NW)
        def on_resize(event):
            # handle resizing the image when the window is resized
            # the procedure is:
            #  * convert to a PIL image
            #  * resize that image
            #  * grab the base64-encoded GIF data from the resized image
            #  * put that in a tkinter label
            #  * show that image on the canvas
            new_img = PILImage.new(mode='L', size=(self.width, self.height))
            new_img.putdata(self.pixels)
            new_img = new_img.resize((event.width, event.height), PILImage.NEAREST)
            buff = BytesIO()
            new_img.save(buff, 'GIF')
            canvas.img = tkinter.PhotoImage(data=base64.b64encode(buff.getvalue()))
            canvas.configure(height=event.height, width=event.width)
            canvas.create_image(0, 0, image=canvas.img, anchor=tkinter.NW)
        # finally, bind that function so that it is called when the window is
        # resized.
        canvas.bind('<Configure>', on_resize)
        toplevel.bind('<Configure>', lambda e: canvas.configure(height=e.height, width=e.width))

        # when the window is closed, the program should stop
        toplevel.protocol('WM_DELETE_WINDOW', tk_root.destroy)


try:
    tk_root = tkinter.Tk()
    tk_root.withdraw()
    tcl = tkinter.Tcl()
    def reafter():
        tcl.after(500,reafter)
    tcl.after(500,reafter)
except:
    tk_root = None
WINDOWS_OPENED = False

if __name__ == '__main__':
    # code in this block will only be run when you explicitly run your script,
    # and not when the tests are being run.  this is a good place for
    # generating images, etc.
    x=Image.load('test_images/bluegill.png')
    x=x.inverted()
    x.save('newbluegill.png')
    x.show()
    minimum=image.pixels[image.pixels.index(min(image.pixels))]






    # the following code will cause windows from Image.show to be displayed
    # properly, whether we're running interactively or not:
    if WINDOWS_OPENED and not sys.flags.interactive:
        tk_root.mainloop()
