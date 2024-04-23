__all__ = ["S4Class"]
#from rpy2.robjects.packages import importr
#from rpy2.robjects.methods import RS4, RS4Auto_Type


class S4Class(object):
    """S4class wrapper


    ::

        robject = rcode('setClass("Person", representation(name = "character", age="numeric")); 
            hadley <- new("Person", name = "Hadley", age = 31)')
        pobject = S4Class(robject)
        pobject.age == 31 # True
        pobject.name

    """
    def __init__(self, robject):
        """


        :param robject: a R S4 object

        """
        self.robject = robject
        self.methods = list(robject.slotnames())

        for m in self.methods:
            data = robject.do_slot(m)
            self.__setattr__(m, data)

