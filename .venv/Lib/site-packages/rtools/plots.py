from tools import rcode

__all__ = ["Rplot", "python_func_example"]



class Rplot(object):
    """Plots and/or save a R plot into a file.


    This class allows to easily call a plotting function directly from R
    and/or to save the results into a file by opening and closing the requested
    device.

    ::

        from rtools import *
        rp = Rplot(show=True, output="test.png")
        rp.rcode("plot(c(1,2))")

        # The function python_func_example calls the R plot function as above
        # but embedded within a python function.
        rp = Rplot(show=True, output="test2.png")
        rp.pythoncode("python_func_example()")


    .. todo:: cleanup and make more robust.

    """
    def __init__(self, show=True, output=None, **kargs):
        """

        :param bool show:  show the plot or not (default is True)
        :param str output: filename with valid extension (png, pdf, jpg, jpeg, tiff, bmp)
        :param kargs: all valid optional parameters (e.g., width, height, quality). 
            See R documentation for exact list of arguments
    
        """
        self.show=True
        self.output = output
        self.kargs = kargs.copy()


    def _start(self):
        """open a device according to the filename extension"""
        if self.output!=None:
            filename, device = self.output.split(".")

            if device == "pdf":
                
                """   width, height, onefile, family, title, fonts, version,
             paper, encoding, bg, fg, pointsize, pagecentre, colormodel,
             useDingbats, useKerning, fillOddEven, maxRasters, compress"""
                pass
            elif device == "bmp":
                """width = 480, height = 480, units = "px", pointsize = 12,
                 bg = "white", res = NA, ...,
                 type = c("cairo", "Xlib", "quartz"), antialias)"""
                device = "png"
            elif device == "jpg" or device == "jpeg":
                """ width = 480, height = 480, units = "px", pointsize = 12,
                  quality = 75,
                  bg = "white", res = NA, ...,
                  type = c("cairo", "Xlib", "quartz"), antialias)"""
                device = "png"
            elif device=="png":
                """width = 480, height = 480, units = "px", pointsize = 12,
                  bg = "white",  res = NA, ...,
                 type = c("cairo", "cairo-png", "Xlib", "quartz"), antialias)"""
                pass
            elif device == "tiff":
                """              width = 480, height = 480, units = "px", pointsize = 12,
              compression = c("none", "rle", "lzw", "jpeg", "zip"),
              bg = "white", res = NA,  ...,
              type = c("cairo", "Xlib", "quartz"), antialias)"""
                device="png"
            else:
                raise ValueError("extension must be pdf, png, jpg, jpeg, tiff, bmp")


            code = "%s('%s'" % (device, self.output)
            if self.kargs:
                for k,v in self.kargs.iteritems():
                    code += ",%s=%s" %(k,v)
            code +=  ")"
            rcode(code)

    def _end(self):
        """close the device (saving)"""
        if self.output!=None:
            rcode("dev.off()")

    def rcode(self, code):
        """Call a pure R code using rpy2"""
        self._start()
        try:
            rcode(code)
        except e:
            print e
            pass
        finally:
            self._end()
            if self.show:
                rcode(code)

    def pythoncode(self, code, g=None, l=None):
        """Call a python code that calls R plot"""
        self._start()
        try:
            eval(code, g,l)
        except e:
            print e
            pass
        finally:
            self._end()
            if self.show:
                eval(code, g, l)




def python_func_example():
    from rtools import rcode
    rcode("plot(c(1,2))")



