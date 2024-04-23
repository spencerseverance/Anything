# -*- python -*-
#
#  This file is part of the cnolab package
#
#  Copyright (c) 2011-2012 - EBI - EMBL
#
#  File author(s): Thomas Cokelaer (cokelaer@ebi.ac.uk)
#
#  Distributed under the GPL License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  ModelData website: http://www.ebi.ac.uk/~cokelaer/cnolab
#
##############################################################################
# $Id: package.py 14 2013-02-05 11:20:26Z cokelaer $
"""Utilities for cnolab.wrapper

:author: Thomas Cokelaer <cokelaer@ebi.ac.uk>
:license: Copyright (c) 2012. GPL

"""
__author__ = """\n""".join(['Thomas Cokelaer <cokelaer@ebi.ac.uk'])
__all__ = ['RPackage', 'biocLite', 'install_packages', "RPackageManager"]

import os
import rpy2
from rpy2 import robjects
from rpy2.robjects import rinterface
from rpy2.robjects.packages import importr
from distutils.version import StrictVersion
 
from error import Rwarning, RRuntimeError
from easydev import Logging

from rtools.tools import rcode




def install_packages(query, dependencies=False, verbose=True,
    repos=None):
    """Install a R package

    :param str query: It can be a valid URL to a R package (tar ball), a CRAN
        package, a path to a R package (tar ball), or simply the directory 
        containing a R package source.
    :param bool dependencies:
    :param repos: if provided, install_packages automatically select the
        provided repositories otherwise a popup window will ask you to select a repo

    ::

        >>> rtools.install_packages("path_to_a_valid_Rpackage.tar.gz")
        >>> rtools.install_packages("http://URL_to_a_valid_Rpackage.tar.gz")
        >>> rtools.install_packages("hash") # a CRAN package
        >>> rtools.install_packages("path to a valid R package directory")


    """
    import tempfile
    import urllib2
    import os.path

    filename = None

    # Is it a local file?
    if os.path.exists(query):
        filename = query[:]
    else:
        try:
           # is it a valid URL ? If so, it should be a kind of source package
            data = urllib2.urlopen(query)
        except:
            print("RTOOLS warning: URL provided does not seem to exist %s. Trying from CRAN" % query)
            code = """install.packages("%s", dependencies=%s """ % \
                (query, _BoolConvertor(dependencies))
 
            if repos:
                code += """ , repos="%s") """ % repos
            else:
                code += ")"
            print(code)
            rcode(code)
            return

        # If valid URL, let us download the data in a temp file
        # get new temp filename
        handle = tempfile.NamedTemporaryFile()

        # and save the downloaded data into it before installation 
        ff = open(handle.name, "w")
        ff.write(data.read())
        ff.close()
        filename = ff.name[:]

    if verbose == True:
        print("Installing %s from %s" % (query, filename))
    code = """install.packages("%s", dependencies=%s """ % \
        (filename, _BoolConvertor(dependencies))
    if repos != None:
        code += """ , repos="%s") """ % repos
    else:
        code += """ , repos=NULL) """
    print code
    rcode(code)



def _BoolConvertor(arg):
    if arg == True:
        return "TRUE"
    elif arg == False:
        return "FALSE"
    else:
        raise ValueError


def biocLite(package=None, suppressUpdates=True):
    """Install a bioconductor package

    This function does not work like the R function. Only a few options are
    implmented so far. However, you can use rcode function directly if needed.

    :param str package: name of the bioconductor package to install. If None, no
        package is installed but installed packages are updated.
    :param bool suppressUpdates: updates the dependencies if needed (default is
        False)

    :return: True if update is required or the required package is installed and
        could be imported. False otherwise.

    ::

        >>> from rcode import biocLite
        >>> biocLite("CellNOptR")

    """
    from tools import rcode
    rcode("""source("http://bioconductor.org/biocLite.R");""") 

    # without a package, biocLite performs an update of the installed packages
    if package == None:
        rcode("""biocLite(suppressUpdates=%s) """ % (
            _BoolConvertor(suppressUpdates)))
    else:
        # if not found, no error is returned...
        rcode("""biocLite("%s", suppressUpdates=%s) """ % (
            package,
            _BoolConvertor(suppressUpdates)
        ))
        # ...so we need to check if it is installed
        try:
            importr(package)
        except Exception, e:
            return False
    return True



class RPackage(object):
    """simple class to import a R package as an object

    ::

        from rtools.package import RPackage
        r = RPackage("CellNOptR")
        r.version
        r.package

    # no error returned but only info and error based on logging module.
    """
    def __init__(self, name, require="0.0", install=False, verbose=False):
        """.. rubric:: Constructor

        :param str name: name of a R package installed on your system
        :param str require: the minimal version required. Use valid string
            format such as "1.0.0" or "1.0" 

        The required package is loaded in the constructor. If not found in your
        system, and if install is set to True, it will try to install it from
        bioconductor web site. If not found, nothing happens but the
        :attr:`package` is None. If you want to install a package from source,
        use the install_packages function. 
        """
        self.name = name
        self.package = None     # the R object linking to the R package
        self.require = require  # the required version
        self.requirement = None # is the required version found ?
        self.installed = None   # is it installed
        self.logging = Logging("INFO")
        if verbose == True:
             self.logging.level = "INFO"
        else:
            self.logging.level = "WARNING"

        self._load()

    def _load(self):
        """Load the package.

        If it cannot, an error message is returned.

        If you want to install it, use :class:`RPackageManager`

        """
        Rwarning(False)
        try:
            self.installed = True
            package = importr(self.name)
            if StrictVersion(self.version) >= StrictVersion(self.require):
                self.package = package
                self.logging.info("R package %s loaded." % self.name)
                self.requirement = True
            else:
                Rwarning(True)
                self.logging.warning("Found %s (version %s) but version %s required." % (self.name, self.version, self.require))
                self.requirement = False
        except RRuntimeError:
            self.installed = False
            self.logging.error("Package %s not installed. Install it from R or with rtools.package.RPackageManager" % self.name)
        Rwarning(True)

    def _get_version(self):
        v = robjects.r("""packageVersion("%s")""" % (self.name))[0]
        v = [str(x) for x in v]
        return ".".join(v)
    version = property(_get_version)


    def __str__(self):
        txt = self.name + ": " + self.version
        return txt




class RPackageManager(object):
    """Implements a R package manager from Python


    So far you can install a package (from source, or CRAN, or biocLite)

    ::

        pm = PackageManager()
        [(x, pm.installed[x][2]) for x in pm.installed.keys()]

    """

    cran_repos = "http://cran.univ-lyon1.fr/"
    def __init__(self):

        self.logging = Logging("INFO")
        self._packages = None
        #self.cran_repos = "http://cran.univ-lyon1.fr/"

    def _get_installed(self):
        # we do not buffer because packages may be removed manually or from R of
        # using remove_packages method, ....
        installed, _a = self.packageStatus(verbose=False)
        return installed
    installed = property(_get_installed, "returns list of packages installed (R object)")

    def _get_available(self):
        # we do not buffer because packages may be removed manually or from R of
        # using remove_packages method, ....
        _i, available = self.packageStatus(verbose=False)
        return available
    available = property(_get_available, "returns list of packages available (R object)")

    def getOption(self, repos):

        #getOption("repos")
        raise NotImplementedError
        # works in R not in rpy2
        #rcodertools.rcode("""getOption("defaultPackages")""")

    def __getitem__(self, pkg):
        packages = self.installed['Package']
        if pkg in packages:
            #index = packages.index(pkg)
            p = RPackage(pkg)
            return p
        else:
            return None

    def _get_packages(self):
        # do not buffer since it may change in many places
        self._packages = self.installed['Package']
        return self._packages
    packages = property(_get_packages)

    def install_packages(self, packageName, dependencies=True, repos=None,
        type=None):
        """Installs one or more CRAN packages"""

        if repos == None:
            repos = self.cran_repos
        # if this is a source file we want to reset the repo
        if type == "source":
            repos = None
        if isinstance(packageName, str):
            if packageName not in self.installed['Package']:
                install_packages(packageName, dependencies=dependencies,
                    repos=repos)
        elif isinstance(packageName, list):
            for pkg in packageName:
                if pkg not in self.installed['Package']:
                    install_packages(pkg, dependencies=dependencies,
                        repos=repos)

    def biocLite(self, packageName=None,suppressUpdates=True):
        """Installs one or more biocLite packages


        :param packageName: a package name (string) that will be installed from 
            BioConductor. Several package names can be provided as a list. If
            packageName is set to None, all packages already installed will be
            updated.

        """
        if isinstance(packageName, str):
            if packageName not in self.installed['Package']:
                biocLite(packageName, suppressUpdates)
        elif isinstance(packageName, list):
            for pkg in packageName:
                if pkg not in self.installed['Package']:
                    biocLite(pkg, suppressUpdates)
        elif packageName == None:
            if packageName not in self.installed['Package']:
                 biocLite(None, suppressUpdates)

    def _isLocal(self, pkg):
        if os.path.exists(pkg):
            return True
        else:
            return False

    def packageStatus(self,
        repos=None,
        verbose=True):
        """Returns the output of packageStatus R function call

        :param str repos: a character vector of URLs describing the 
            location of R package repositories on the Internet or on the 
            local machine.

        :return: an R object res[0] and ares[1] gives exhaustive information
            about the installed.packages

        """
        if repos:
            code = """packageStatus(repositories="%s")""" % (repos)
        else:
            code = """packageStatus(repositories="%s")""" %\
                (self.cran_repos+"/src/contrib")
        res = rcode("%s" % code)
        if verbose:
            print(res)

        inst = {}
        for name in res[0].names:
            inst[name] = res[0].rx2(name)

        available = {}
        for name in res[1].names:
            available[name] = res[1].rx2(name)

        return inst, available

    def remove_packages(self, packageName):
        code = """remove.packages("%s")"""
        if isinstance(packageName, str):
            if packageName in self.installed['Package']:
                rcode(code % packageName)
            else:
                self.logging.warning("Package not found. Nothing to remove")
        elif isinstance(packageName, list):
            for pkg in packageName:
                if packageName in self.installed['Package']:
                    rcode(code % pkg)
                else:
                    self.logging.warning("Package not found. Nothing to remove")

    def require(self, pkg, version):
        """Check if a package with given version is available"""

        if pkg not in self.packages:
            self.logging.info("Package %s not installed" % pkg)
            return False
        currentVersion = self.packageVersion(pkg)
        if StrictVersion(currentVersion) >= StrictVersion(version):
            return True
        else:
            return False

    def packageVersion(self, pkg):
        v = rcode("""packageVersion("%s")""" % (pkg))[0]
        v = [str(x) for x in v]
        return ".".join(v)

    def install(self, pkg, require=None):
        """install a package automatically scanning CRAN and biocLite repos


        """
        if self._isLocal(pkg):
            # if a local file, we do not want to jump to biocLite or CRAN. Let
            # us install it directly. We cannot check version yet so we will
            # overwrite what is already installed
            self.logging.warning("Installing from source")
            self.install_packages(pkg, repos=None, type="source")
            return 

        if pkg in self.installed['Package']:
            currentVersion = self.packageVersion(pkg)
            if require == None:
                self.logging.info("%s already installed with version %s" % \
                    (pkg, currentVersion))
                return
            # nothing to do except the required version
            if StrictVersion(currentVersion) >= StrictVersion(require):
                self.logging.info("%s already installed with required version %s" \
                    % (pkg, currentVersion))
            else:
                # Try updating
                self.install_packages(pkg, repos=self.cran_repos)
                if require == None:
                    return
                currentVersion = self.packageVersion(pkg)
                if StrictVersion(currentVersion) >= StrictVersion(require):
                    self.logging.warning("%s installed but current version (%s) does not fulfill your requirement" % \
                        (pkg, currentVersion))

        elif pkg in self.available['Package']:
            self.install_packages(pkg, repos=self.cran_repos)
        else:
            # maybe a biocLite package:
            # require is ignored. The latest will be installed
            self.biocLite(pkg)
            if require == None:
                return
            currentVersion = self.packageVersion(pkg)
            if StrictVersion(currentVersion) >= StrictVersion(require):
                self.logging.warning("%s installed but version is %s too small (even after update)" % \
                    (pkg, currentVersion, require))









