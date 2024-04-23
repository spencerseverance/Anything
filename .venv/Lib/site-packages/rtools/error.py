# -*- python -*-
#
#  This file is part of the rtools package
#
#  Copyright (c) 2011-2012 - EBI - EMBL
#
#  File author(s): Thomas Cokelaer (cokelaer@ebi.ac.uk)
#
#  Distributed under the GPL License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  RTools website: http://www.ebi.ac.uk/~cokelaer/rtools
#
##############################################################################
# $Id: error.py 2 2013-01-25 13:25:10Z cokelaer $
"""Module that provides easy access to error and warning messages returned by R

:author: Thomas Cokelaer <cokelaer@ebi.ac.uk>
:copyright: Copyright (c) 2012. GPL

"""
__author__ = """\n""".join(['Thomas Cokelaer <cokelaer@ebi.ac.uk'])

__all__ = ["Rwarning", "RRuntimeError"]

import rpy2.robjects
from rpy2.robjects import r

#: alias to the R main exception
RRuntimeError = rpy2.robjects.rinterface.RRuntimeError

 
def Rwarning(state=True):
    """Set R warning on/off"""

    if state==True:
        r("options(warn = (-1))")
        r("options(show.error.messages=TRUE)")
    else:
        r("options(warn = (-1))")
        r("options(show.error.messages=FALSE)")



# does not seem to work
#def Recho(state=True):
#    """Set R echo on/off"""
#    if state==True:
#        r("options(echo=TRUE)")
#    else:
#        r("options(echo=FALSE)")



