
import numpy
import scipy.optimize

# from http://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.lstsq.html
def lsqfit(x, y):
    x = np.array(x)
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y)[0]
    fity = m*x + c
    return fity

def slope_intercept(u, v):
    u = numpy.array(u)
    v = numpy.array(v)
    n = len(u)
    assert len(v) == n
    I = numpy.identity(n)
    A = numpy.zeros((2*n, n+2))
    n1 = numpy.ones(n)
    A[0:n, n+1] = n1
    A[n:2*n, n+1] = - n1
    A[0:n, n] = u
    A[n:2*n, n] = - u
    A[0:n, 0:n] = - I
    A[n:2*n, 0:n] = - I
    b = numpy.ones(2*n)
    b[0:n] = v
    b[n:2*n] = - v
    c = numpy.ones(n + 2)
    c[n] = c[n+1] = 0
    bounds = [(None, None)] * len(c)
    r = scipy.optimize.linprog(c, A, b, bounds=bounds)
    result = {}
    result["r"] = r
    x = result["x"] = r.x
    result["slope"] = x[n]
    result["intercept"] = x[n+1]
    return result

def interpolate(u, v):
    r = slope_intercept(u, v)
    m = r["slope"]
    c = r["intercept"]
    return m * u + c

def test0():
    import pprint
    check = slope_intercept( (1, 0), (0, 1) )
    pprint.pprint(check)
    print "slope should be -1", check["slope"]
    print "intercept should be 1", check["intercept"]

if __name__ == "__main__":
    test0()

