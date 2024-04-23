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
# $Id: tools.py 14 2013-02-05 11:20:26Z cokelaer $
"""Utilities for cnolab.wrapper

:author: Thomas Cokelaer <cokelaer@ebi.ac.uk>
:licence: copyright (2012). GPL


"""
__author__ = """\n""".join(['Thomas Cokelaer <cokelaer@ebi.ac.uk'])

__all__ = ['Rnames2attributes',  'buildDocString', "RManualToDocString",  
     "RConvertor", "convertor", "rcode"]

import os
import rpy2
from rpy2 import robjects
from rpy2.robjects import rinterface
from rpy2.robjects.packages import importr
from rpy2.robjects import r

from error import Rwarning, RRuntimeError


def rcode(code):
    """A simple alias to the :func:`rpy2.robject.r` function.

    ::

        res = rcode("list(a=c(1,2), b=2)")

    """
    from rpy2.robjects import r
    res = r(code)
    return res

 
# decorator with no arguments for a function with arguments
def Rnames2attributes(f):
    """Decorator used to create attributes for each variable in a R structure

    The RPY2 package allows to call R function in Python. For instance in the
    case of the base package, you can compute the mean of a vector.

        >>> from rtools import RPackage, convertor
        >>> base = RPackage("base").package
        >>> m =  float(base.mean(convertor([1,2,3])))
        2.0

    In more complex example, list are returned. For instance in CellNOptR package, 
    the function readMIDAS returns a list. The  **names** attribute is useful
    to access the output of CNOR.readMIDAS function:

    .. doctest::
        :options: +SKIP

        >>> m.names #doctest: +SKIP
        <StrVector - Python:0x339c680 / R:0x34113a8>
        ['dataMatrix', 'TRcol', 'DAcol', 'DVcol']

    Then, knowing the name of a variable, you can access any field using this command:

    .. doctest::
        :options: +SKIP

        >>> m.rx2('DAcol') #doctest: +SKIP
        <FloatVector - Python:0x339c128 / R:0x7fab5c721518>
        [5.000000, 6.000000, 7.000000, ..., 9.000000, 10.000000, 11.000000]

    This is not very convenient. This decorator wraps a R function so that the
    variables in **names** can be accessible directly as READ ONLY attributes:

    .. doctest::
        :options: +SKIP

        >>> @Rnames2attributes   #doctest: +SKIP
        >>> def readMIDAS(file):  #doctest: +SKIP
        ...     return CNOR.readMIDAS(file)  #doctest: +SKIP
        >>> m = readMIDAS(file)   #doctest: +SKIP
        >>> m.DAcol #doctest: +SKIP
        <FloatVector - Python:0x339c128 / R:0x7fab5c721518>
        [5.000000, 6.000000, 7.000000, ..., 9.000000, 10.000000, 11.000000]


    .. warning:: this is not recursive. So only the first level is accessible with
        attributes.
    """
    def wrap(*args, **kargs):
        res = f(*args, **kargs)
        res = setAttributes(res)
        #try:
        #    for name in res.names:
        #        setattr(res, name, res.rx2(name))
        #except:
        #    # for the case where nothing is returned
        #    pass
        return res
    wrap.__name__ = f.__name__
    return wrap



def setAttributes(res):
    """A recursive function to set the attributes of a ListVector R object


    a Robject that belong to the ListVector class can name its field. Each field
    can be itself a ListVector. For example::

        >>> listVector = rtools.rcode("m = list(a=1, b=list(c=1, d=2))")

    You can now access to the field a as follows::

        listVector.rx2('a')

    and to *c*::

        listVector.rx2('b').rx2('c')

    This function build READ ONLY attributes recursively::

        listVector2 = setAttributes(listVector)  
        listVector2.b.c
        listVector2.a

    It works by looking at listVector.names to find the field.

    In principle, simply checking that names is NULL should suffice to stop the
    recursion, however, rpy2 seems buggy: for instance if a field is a matrix,
    the names returned is actually a combination of colnames and rownames. Hence raising a
    message error since we expect NULL (as in a pure R session).

    If names is not NULL, it should be a list of names so it should be a
    StrVector R object. so, the fix is to check if the names is NULL or its type
    is different from StrVector.

    """
    #print( "Entering setAttributs %s" % res.names)
    #print("----------------------")
    import rpy2.robjects

    # if the object is NULL/None, just return it
    if res == rpy2.rinterface.NULL or res == None:
        return res
    # if it is a class, don't do anything, just return it
    elif type(res)==rpy2.robjects.methods.RS4:
        # do not deal with RS4 although, we could parse them with S4Class ?
        return res
    # if it has no name in it, there will be no more recursion, so return it
    #elif 'name' not in dir(res):
    #    return res 
    # if names if defined but null, return it
    elif res.names == rpy2.rinterface.NULL:
        # if null, nothing to be done anymore
        return res
    # if it has names, it should be a StrVector otherwise, we dont know what to
    # do with it
    elif type(res.names) != rpy2.robjects.vectors.StrVector:
        # sometimes, names is not NULL (altough it is in a pure R session)
        # so, let us check that names is not a vector or empty vector (if not NULL) 
        return res
    # it should be a non empty list
    elif len(res.names) and res.names[0] == '':
        return res
    # if we finally enter here, we have a list of names to go through.
    else:
        for name in res.names:
            #print("dealing with %s" % name)
            setattr(res, name, setAttributes(res.rx2(name)))
    return res




class RManualToDocString(object):
    """Reads R manual and convert to Sphinx doc string.


    >>> d = RManualToDocString("base", "abbreviate")
    >>> d.get_docstring()

    """
    #: List of valid known arguments from Rdoc
    registered_sections = [
        'title', 'name', 'alias', 'description', 'usage',
        'arguments', 'details', 'value', 'author', 'note','section',
        'references', 'seealso', 'examples', 'keyword']

    def __init__(self, package, funcname):
        #print("Processing %s %s" % (package, funcname))
        from rpy2 import robjects
        from rpy2.robjects.help import HelpNotFoundError
        self.name = funcname
        self.package = package
        try:
            Rwarning(False)
            self.base = robjects.help.Package(package)
            self.doc = self.base.fetch(self.name)
            Rwarning(True)
        except HelpNotFoundError:
            self.doc = "Help not found for %s " % funcname
        except RRuntimeError:
            self.doc = "package %s not loaded"  % package

    def _get_section(self, section):
        if section not in RManualToDocString.registered_sections:
            print("section (%s) not known in %s. Skip it. Fix\
                RManualToDocString class please.\n" % (self.name, section))
        self._temp = []
        self._walk(self.doc.sections[section], section)
        return self._temp

    def _walk(self, tree, section=None):
        if not isinstance(tree, str):
            for elt in tree:
                self._walk(elt, section=section)
        else:
            if section=="examples":
                # remove spaces and indent with 4 spaces
                self._temp.append(tree.strip("\n"))
                self._temp = [x.strip(' ') for x in self._temp]
                self._temp = ["    "+x for x in self._temp if len(x)]
            elif section=="arguments":
                self._temp.append(tree)
            else:
                self._temp.append(tree.strip("\n"))

    def _get_sections(self):
        return self.doc.sections.keys()
    sections = property(_get_sections, doc="property containing all sections found in the Rdoc")

    def get_docstring(self):
        """Call process method for each section and build the entire docstring"""
        if self.doc == "":
            return ""
        docs = ""
        for sec in self.sections:
            docs += self.process(sec)
        return docs

    def _get_arguments(self):
        """Return the list of arguments of the function by parsing the Rdoc

        The order may not be the same as in the content of the arguments section
        since we use the usage section here to extract the list of arguments."""
        # for sanity check, the name provided should be found again in the name
        # section.
        name = self._get_section('name')[0]
        assert name == self.name

        # From the usage section, we can get the list of arguments.
        arguments = self.process("usage").split(self.name)[1]

        # we get rid of spaces and remove the brackets
        arguments = arguments.strip("\n").strip()
        L = len(arguments)
        arguments = arguments[1:L-1]

        # fiunally, we split the arguments
        arguments = arguments.split(",")
        arguments = [arg.strip() for arg in arguments]
        # and select only the argument name (not its default value)
        arguments = [arg.split('=')[0] for arg in arguments]
        # Now we have all the arguments, we l
        return arguments


    def process(self, section):
        """Convert R section into proper Sphinx section

        >>> sections = d.sections
        >>> d.process(sections[0])
        >>> # equivalent to
        >>> d.process("title")

        This is where most of the processing of the Rdoc to sphinx docstring
        is done.


        """
        data = self._get_section(section)
        data = [x.strip("\n") for x in data] # get rid of \n characters


        output = "\n:%s: " % section.capitalize()
        if section == 'title':
            output = ""
            data = [x.strip("\n") for x in data]
            for x in data:
                output += x
        elif section == 'alias':
            output =""
        elif section == 'examples':
            output = "Example:"
            output += "\n\n.. code-block:: r\n\n"
            data = "\n".join(data)
            output += data
        elif section == "arguments":
            output = "" # no need for a :Arguments: that is taken care of by :param:
            try:
                arguments = self._get_arguments()
                data.reverse()
                while data:
                    x = data.pop()
                    x = x.strip()
                    if len(x) != 0:
                        if x in arguments:
                            output += "\n:param %s: " % x
                        else:
                            output += x +" "
            except:
                output += "Could not parse the arguments section. Copy and paste it."
                for x in data:
                    output += x + "\n"
        elif section == "seealso":
            output = "\n.. seealso:: "
            data = [x for x in data if len(x)]
            newdata = []
            for x in data:
                x = x.split(',')
                if len(x) == 1:
                    newdata.append(x[0])
                else:
                    for y in x:
                        newdata.append(y.strip())
            data= newdata
            data = [x.strip(',').strip(' ') for x in data if len(x)]
            output += ", ".join([":func:`"+x+"`" for x in data if len(x)])
            #output = output.replace("makeCNOlist", "makeCNOlist")
            #output = output.replace("plotCNOlist", "plotCNOlist")
            output +="\n"
        elif section=="name":
            output=""
        else:
            for x in data:
                output += str(x)+" "
        output += "\n"
        return output


def buildDocString(base, name):
    """scan manual from a R function and transform it into a docstring.


    .. seealso:: :class:`rtools.rools.RManualToDocString`

    """
    try:
        d = RManualToDocString(base, name)
        output = d.get_docstring()
    except:
        d = RManualToDocString(base,  name)
        output = d.doc
    return output



class RConvertor(object):
    """The RConverter ease the conversion of python objects into 
    R objects.

    r = Convertor()
    r.convert(None)
    r.convert([1,2,3])

    See :meth:`convert` for details
    """
    def __init__(self): 
        pass
 
    def convert(self, data, forcetype=None):
        """convert simple python object to R object

        :param data: the data to convert
        :param forcetype: if data is a list, by default, the conversion is made
            according to the type of the first element of the list. You can
            force the type to be different with this argument (e.g.,
            forcetype=str)

        * if data is None, return a R object NULL
        * if data is a list or a tuple:
            * if type of first element is integer, returns a IntVector
            * if type of first element is float, returns a FloatVector
            * if type of first element is str, returns a StrVector
            * if type of first element is complex, returns a ComplexVector
            * if type of first element is bool, returns a BoolVector
        * else return the data itself (assume it is already a R object)


    
        """
        if data == None:
            return robjects.NULL

        elif isinstance(data, dict):
            newd = {}
            for k, v in data.iteritems():
                rc = RConvertor()
                newd[k] = rc.convert(v)
            return rpy2.robjects.ListVector(newd)

        elif isinstance(data, list) or isinstance(data, tuple):
            t = type(data[0])
            if forcetype != None:
                t = forcetype

            if t == int:
                return robjects.IntVector(data)
            elif t == float:
                return robjects.FloatVector(data)
            elif t == str:
                return robjects.StrVector(data)
            elif t == complex:
                return robjects.ComplexVector([x+0.j for x in data])
            elif t == bool:
                return robjects.BoolVector(data)
            else:
                raise NotImplementedError 
        else:
            # all case where it is already a R objects
            return data


#: alias to the method convert of RConvertor class
convertor = RConvertor().convert




#rpy2.robjects.array
#rpy2.robjects.NA_Complex
#rpy2.robjects.Array
#rpy2.robjects.NA_Integer
#rpy2.robjects.NA_Logical
#rpy2.robjects.DataFrame                    
#rpy2.robjects.Matrix 
#rpy2.robjects.NA_Character                 
#rpy2.robjects.vectors
#rpy2.robjects.NA_Real
#rpy2.robjects.FactorVector       
#rpy2.robjects.ListVector   
#rpy2.robjects.Vector

