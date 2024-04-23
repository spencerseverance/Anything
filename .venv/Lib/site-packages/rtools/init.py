

# check that rpy2 is available
try:
    import rpy2
except ImportError:
    raise ("make sure that rpy2 is installed on your system of fix the PYTHONPATH")




try:
    import rpy2.robjects
except Exception:
    raise Exception

