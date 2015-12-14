
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
    """
    1d version of l1_fit
    """
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

def l1_fit(U, v, penalty=None, tolerance=None, callback=None):
    """
    Find a least absolute error solution (m, k) to U * m + k =approx= v 
    """
    U = numpy.array(U)
    v = numpy.array(v)
    # n is the number of samples
    n = len(v)
    s = U.shape
    assert len(s) == 2
    assert s[0] == n
    # d is the number of dimensions
    d = s[1]
    I = numpy.identity(n)
    n1 = numpy.ones((n,1))
    A = numpy.vstack([
            numpy.hstack([-I, U, n1]),
            numpy.hstack([-I, -U, -n1])
        ])
    c = numpy.hstack([numpy.ones(n), numpy.zeros(d+1)])
    b = numpy.hstack([v, -v])
    bounds = [(0, None)] * n + [(None, None)] * (d+1)
    if penalty is not None and penalty>0:
        (old_c, old_A, old_b, old_bounds) = (c, A, b, bounds)
        zdn =numpy.zeros((d,n))
        Id = numpy.identity(d)
        zd = numpy.zeros((d, 1))
        pos_constraints = numpy.hstack([zdn, Id, zd, -Id])
        neg_constraints = numpy.hstack([zdn, -Id, zd, -Id])
        A = numpy.vstack([
                numpy.hstack([old_A, numpy.zeros((2*n, d))]),
                numpy.vstack([
                    pos_constraints,
                    neg_constraints
                    ])
            ])
        c = numpy.hstack([old_c, numpy.ones(d) * penalty])
        b = numpy.hstack([old_b, numpy.zeros(2*d)])
        bounds = old_bounds + [ (0,None) ] * d
    if tolerance is not None and tolerance > 0:
        (rows, cols) = A.shape
        extrarows = rows - 2*n
        extrazeros = numpy.zeros((extrarows, n))
        old_A = A
        old_bounds = bounds
        old_c = c
        #print "A, c, bounds", A.shape, len(c), len(bounds)
        c = numpy.hstack([old_c, numpy.zeros(n)])
        A = numpy.hstack([old_A, numpy.vstack([I, I, extrazeros])])
        bounds = old_bounds + [(-tolerance, +tolerance)] * n
        #print "A, c, bounds", A.shape, len(c), len(bounds)
    options = {"maxiter": 10000}
    r = scipy.optimize.linprog(c, A, b, bounds=bounds, callback=callback, options=options)
    #print r.message
    x = r.x
    m = x[n:n+d]
    k = x[n+d]
    residuals = v - (numpy.dot(U, m) + k)
    result = {}
    result["U"] = U
    result["v"] = v
    result["tolerance"] = tolerance
    result["penalty"] = penalty
    result["m"] = m
    result["k"] = k
    result["r"] = r
    result["A"] = A
    result["b"] = b
    result["c"] = c
    result["bounds"] = bounds
    result["residuals"] = residuals
    return result

def testl1():
    import pprint
    p1 = numpy.array([1.0, 0, 2.0])
    p2 = numpy.array([0, 1.0, 0])
    p3 = numpy.array([5.0, 0, 1.0])
    U = [p1, p2, p3]
    v = numpy.array([-1.0, 2.0, 3.0])
    for expected_error in (0.2, 0):
        for penalty in (0, 0.001):
            print()
            print( "expected error", expected_error, "penalty", penalty)
            fit = l1_fit(U, v, expected_error=expected_error, penalty=penalty)
            pprint.pprint(fit)
            m = fit["m"]
            k = fit["k"]
            print ("v")
            print (v)
            print ("U * m + k")
            print (numpy.dot(U, m) + k)

def interpolate(u, v):
    r = slope_intercept(u, v)
    m = r["slope"]
    c = r["intercept"]
    return m * u + c

def test0():
    import pprint
    check = slope_intercept( (1, 0), (0, 1) )
    pprint.pprint(check)
    print ("slope should be -1", check["slope"])
    print ("intercept should be 1", check["intercept"])

if __name__ == "__main__":
    test0()
    testl1()

