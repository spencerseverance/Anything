# -*- python -*-
#
#  Copyright (c) 2011-2012 - EBI - EMBL
#
#  File author(s): Thomas Cokelaer <cokelaer@ebi.ac.uk>
#
#  Distributed under the GPLv3 License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  RTools website: http://www.ebi.ac.uk/~cokelaer/rtools
#
##############################################################################
"""matplotlib colormap builder from R colormaps


:author: Thomas Cokelaer <cokelaer@ebi.ac.uk>
:copyright: Copyright (c) 2012. GPL
"""

from pylab import *

from tools import rcode


__all__ = ["RColorMap"]


class RColorMap(object):
    """Build a colormap from a R colormap that is compatible with matplotlib

    .. plot::
        :include-source:

        # first build the colormap
        from rtools import RColorMap
        rmap = RColorMap("heat")
        cmap = rmap.colormap()

        # use it within matplotlib
        try:
            import numpy as np
            import pylab as plt
            A = np.array(range(100))
            A.shape = (10,10)
            plt.pcolor(A,cmap=cmap, vmin=0, vmax=100)
            plt.colorbar()
        except:
            pass

    """
    def __init__(self, name, inverse=True):
        """constructor


        :param str name: valid R colormap (e.g., heat)
        :param bool inverse: inverse the colormap colors

        .. note:: Internally, the number of color used in the R colorbar is 1000, which
            may be changed with the :attr:`rN` attribute. The number of color used
            by matplotlib to perform the linear  interpolation is set to 11 with the
            attribute :attr:`n`. There is no need t change these 2 attributes in
            most cases.


        """

        self._name = name
        self.rN = 1000   # number of colors to retrieve from R colors
        self.n = 11     # number of colors to really use
        self.inverse = inverse
        self._xvalues = None
        self._colors = None

    def _get_name(self):
        return self._name
    name = property(_get_name, "return the name of the colormap")

    def _get_x(self):
        return linspace(0, self.rN-1, self.n)
    xvalues = property(_get_x, doc="return the indices of the colors.")

    def _get_rgb(self):
        if self._colors == None:
            self._colors = self._getRGBColors()
        return self._colors
    rgb = property(_get_rgb, doc="return the RGB color in hexadecimal")

    def _get_r(self):
        return [x[0:2] for x in self.rgb]
    r = property(_get_r, doc="return the red componennt in hexadecimal")

    def _get_g(self):
        return [x[2:4] for x in self.rgb]
    g = property(_get_g, doc="return the green componennt in hexadecimal")

    def _get_b(self):
        return [x[4:6] for x in self.rgb]
    b = property(_get_b, doc="return the blue componennt in hexadecimal")

    def _getRGBColors(self):

        params = {'N':self.rN, 'n':self.n, 'name':self.name} 
        code = """
        colors = %(name)s.colors(%(N)s)
        r = c(seq(from=1,to=%(N)s, length.out=%(n)s))
        colors[r]
        """ % params
        try:
            res = rcode(code) 
        except:
            print("Could not find the %s color" % self.name)

        # colors returned by R stqrts with # character and all ends with FF
        # All we need is the 6 characters corresponding to the RGB color coded with hexadecimal 
        res = [x[1:7] for x in res]   
        if self.inverse:
            res = res[::-1]
        return res

    def hex2dec(self, data):
        """convert integer (data) into hexadecimal."""
        return int(data,16)*1.0/255

    def colormap(self, N=256):
        """Return the colormap with N values.


        :param int N: number of colors in the final colormap (default is 256)

        """
        rcol = []
        bcol = []
        gcol = []
        for x, r, g, b in zip(self.xvalues, self.r, self.g, self.b):
            rcol.append((x/float(self.rN-1), self.hex2dec(r), self.hex2dec(r)))
            gcol.append((x/float(self.rN-1), self.hex2dec(g), self.hex2dec(g)))
            bcol.append((x/float(self.rN-1), self.hex2dec(b), self.hex2dec(b)))
        rcol = tuple(rcol)
        bcol = tuple(bcol)
        gcol = tuple(gcol)

        colors = {'red':rcol, 'green':gcol, 'blue':bcol}
        #print colors
        f = matplotlib.colors.LinearSegmentedColormap
        m = f('my_color_map', colors, N)
        return m


