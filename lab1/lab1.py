Skip to content
 
Search or jump to…

Pull requests
Issues
Marketplace
Explore
 
@Ethanking1995 
0
0 0 guo-ou/MIT-6.009
 Code  Issues 1  Pull requests 0  Projects 0  Wiki  Security  Insights
MIT-6.009/lab1/lab.py
@guo-ou guo-ou la:w
f724b4c on Oct 5, 2018
346 lines (303 sloc)  12.7 KB
    
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
        if x < 0:
            x = 0
        if x >= self.height:
            x = self.height - 1
        if y < 0:
            y = 0
        if y >= self.width:
            y = self.width - 1
        return self.pixels[self.width*x+y]
    
    def set_pixel(self, x, y, c):
        i = (self.width*x)+y
        if c < 0:
            c = 0
        elif c > 255:
            c = 255
        self.pixels[i] = c

    def apply_per_pixel(self, func):
        result = Image.new(self.width, self.height)
        for x in range(result.height):
            for y in range(result.width):
                color = self.get_pixel(x, y)
                newcolor = func(color)
                result.set_pixel(x, y, newcolor)
        return result

    def inverted(self):
        return self.apply_per_pixel(lambda c: 255-c)
    
    def get_color(self, x, y, kernel):
        color = 0;
        for i in range(kernel.height):
            for j in range(kernel.width):
                color += self.get_pixel(x-int(kernel.width/2)+i,
                                        y-int(kernel.height/2)+j)*kernel.get_pixel(i, j)
        return color
        
    def apply_kernel(self, kernel):
        result = Image.new(self.width, self.height)
        for x in range(result.height):
            for y in range(result.width):
                newcolor = int(round(self.get_color(x, y, kernel)))
                result.set_pixel(x, y, newcolor)
        return result

    def blurred(self, n):
        return self.apply_kernel(kernel_n(n))

    def sharpened(self, n):
        kernel = kernel_n(n)
        result = Image.new(self.width, self.height)
        for x in range(result.height):
            for y in range(result.width):
                newcolor = int(round((2*self.get_pixel(x, y)) -
                                     self.get_color(x, y, kernel)))
                result.set_pixel(x, y, newcolor)
        return result

    def edges(self):
        result = Image.new(self.width, self.height)
        for x in range(result.height):
            for y in range(result.width):
                newcolor = int(round(math.sqrt(math.pow(self.get_color(x, y, kernel_x),2)+
                                               math.pow(self.get_color(x, y, kernel_y),2))))
                result.set_pixel(x, y, newcolor)
        return result
    
    # Below this point are utilities for loading, saving, and displaying
    # images, as well as for testing.

    def __eq__(self, other):
        return all(getattr(self, i) == getattr(other, i)
                   for i in ('height', 'width', 'pixels'))

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

##for fname in ('mushroom', 'twocats', 'chess'):
##    inpfile = ('test_images'+'\\'+'%s.png' % fname)
##    expfile = ('test_results'+'\\'+'%s_invert.png' % fname)
##    result = Image.load(inpfile).inverted()
##    expected = Image.load(expfile)
##    print(result == expected)

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
    pass

    # the following code will cause windows from Image.show to be displayed
    # properly, whether we're running interactively or not:
    if WINDOWS_OPENED and not sys.flags.interactive:
        tk_root.mainloop()
##
##kernel_id = Image(3,3,[0, 0, 0,
##                       0, 1, 0,
##                       0, 0, 0])
##kernel_tra = Image(5,5,[0, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0,
##                        1, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0])
##
##kernel_ave = Image(3,3,[0, 0.2, 0,
##                       0.2, 0.2, 0.2,
##                       0, 0.2, 0])
## 
##kernel_pig = Image(5,5,[0, 0, 0, 0, 0, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0, 0, 0, 0, 0,
##                        1, 0, 0, 0, 0, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0, 0, 0, 0, 0,
##                        0, 0, 0, 0, 0, 0, 0, 0, 0])

kernel_x = Image(3,3,[-1, 0, 1,
                      -2, 0, 2,
                      -1, 0, 1])

kernel_y = Image(3,3,[-1, -2, -1,
                       0, 0, 0,
                       1, 2, 1])

import random

def kernel_n(n):
    k = 1/(n*n)
    return Image(n, n, [k for i in range(n*n)])

def find_min_energy_column(image):
    edge = image.edges()
    column = [0 for i in range(edge.width)]
    for y in range(edge.width):
        color = 0
        for x in range(edge.height):
            color += edge.get_pixel(x, y)
        column[y] = color+random.random()
    return column

def remove_column(image, col):
    result = Image.new(image.width-len(col), image.height)
    for x in range(image.height):
        count = 0
        for y in range(image.width):
            if y not in col:
                newcolor = image.get_pixel(x, y)
                result.set_pixel(x, count, newcolor)
                count += 1
    return result

def retarget(image, n):
    lowenergy = find_min_energy_column(image)
    col = [0 for i in range(n)]
    sortedlow = sorted(lowenergy)
    for i in range(n):
        col[i] = lowenergy.index(sortedlow[i])
    return remove_column(image, set(col))

def find_min_path(image):
    edge = image.edges()
    for x in range(edge.height-1):
        for y in range(edge.width):
            if y == 0:
                edge.pixels[(edge.width*(x+1))+y] += min(edge.get_pixel(x,y),
                                                         edge.get_pixel(x,y+1))+random.random()
            elif y == edge.width-1:
                edge.pixels[(edge.width*(x+1))+y] += min(edge.get_pixel(x,y-1),
                                                         edge.get_pixel(x,y))+random.random()
            else:
                edge.pixels[(edge.width*(x+1))+y] += min(edge.get_pixel(x,y-1),
                                                         edge.get_pixel(x,y),
                                                         edge.get_pixel(x,y+1))+random.random()
    for y in range(edge.width):
        edge.pixels[y] = edge.get_pixel(0,y)+random.random()
    return edge

def find_min_seam(energymap):
    path = [0 for i in range(energymap.height)]
    path[0] = energymap.pixels.index(min(energymap.pixels[energymap.width*
                                                        (energymap.height-1):]))%energymap.width
    #energymap.pixels[energymap.width*(energymap.height-1) + path[0]] = float('inf')
    for i in range(energymap.height-1):
        path[i+1] = energymap.pixels.index(min(energymap.get_pixel(energymap.height-(i+2),path[i]),
                                                energymap.get_pixel(energymap.height-(i+2),path[i]+1),
                                                energymap.get_pixel(energymap.height-(i+2),path[i]-1)))%energymap.width
        #energymap.pixels[energymap.width*(energymap.height-(i+2)) + path[i+1]] = float('inf')
    path.reverse()
    return path

def remove_path(image, path):
    result = Image.new(image.width-1, image.height)
    for x in range(image.height):
        count = 0
        for y in range(image.width):
            if y != path[x]:
                newcolor = image.get_pixel(x, y)
                result.set_pixel(x, count, newcolor)
                count += 1
    return result

def seam_carving(image, n):
    for i in range(n):
        image = remove_path(image,find_min_seam(find_min_path(image)))
    return image

i=Image.load('test_images\\twocats.png')
m=seam_carving(i,150)

##[255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 102, 255, 255, 255, 98, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
## 386, 452, 510, 400, 510, 295, 510, 510, 510, 510, 265, 357, 357, 357, 510, 162, 353, 311, 255, 255, 338, 450, 510, 366, 510, 372, 333, 510, 510, 510,
## 485, 641, 421, 655, 374, 550, 426, 765, 765, 520, 520, 520, 612, 452, 417, 417, 215, 346, 348, 350, 461, 593, 567, 621, 456, 422, 333, 588, 765, 765,
## 692, 676, 676, 589, 629, 509, 526, 629, 623, 751, 775, 775, 615, 451, 672, 389, 296, 470, 601, 603, 458, 716, 822, 711, 422, 333, 333, 521, 703, 1020,
## 912, 875, 804, 844, 764, 700, 764, 781, 878, 774, 1006, 870, 648, 706, 644, 551, 551, 551, 508, 713, 713, 652, 966, 677, 588, 588, 588, 529, 776, 958]


© 2019 GitHub, Inc.
Terms
Privacy
Security
Status
Help
Contact GitHub
Pricing
API
Training
Blog
About
