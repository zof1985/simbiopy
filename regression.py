# REGRESSION MODULE


#! IMPORTS


from typing import Union
import numpy as np
import pandas as pd


__all__ = [
    "LinearRegression",
    "PolynomialRegression",
    "PowerRegression",
    "HyperbolicRegression",
    "ExponentialRegression",
    "EllipsisRegression",
    "CircleRegression",
]


#! CLASSES


class LinearRegression:
    """
    Obtain the regression coefficients according to the Ordinary Least
    Squares approach.

    Parameters
    ----------
    y:  (samples, dimensions) numpy array or pandas.DataFrame
        the array containing the dependent variable.

    x:  (samples, features) numpy array or pandas.DataFrame
        the array containing the indipendent variables.

    fit_intercept: bool
        Should the intercept be included in the model?
        Otherwise it will be set to zero.
    """

    def __init__(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
        fit_intercept: bool = True,
    ):
        # set the inputs
        self._set_inputs(y=y, x=x, fit_intercept=fit_intercept)

        # calculate betas
        self._calculate_betas()

        # if complex values are found raise an error
        if np.any(np.iscomplex(self.betas.values)):
            raise ValueError("Complex coefficients have been found.")

    def _simplify(
        self,
        v: Union[np.ndarray, pd.DataFrame, list, int, float],
        label: str = "",
    ):
        """
        internal method to format the entries in the constructor and call
        methods.

        Parameters
        ----------
        v: np.ndarray | pd.DataFrame | list | int | float | None
            the data to be formatter

        label: str
            in case an array is provided, the label is used to define the
            columns of the output DataFrame.

        Returns
        -------
        d: pd.DataFrame
            the data formatted as DataFrame.
        """

        def simplify_array(v: np.ndarray, l: str):
            if v.ndim == 1:
                d = np.atleast_2d(v).T
            elif v.ndim == 2:
                d = v
            else:
                raise ValueError(v)
            cols = [f"{l}{i}" for i in range(d.shape[1])]
            return pd.DataFrame(d.astype(float), columns=cols)

        if isinstance(v, pd.DataFrame):
            return v.astype(float)
        if isinstance(v, list):
            return simplify_array(np.array(v), label)
        if isinstance(v, np.ndarray):
            return simplify_array(v, label)
        if np.isreal(v):
            return simplify_array(np.array([v]), label)
        raise NotImplementedError(v)

    def _add_intercept(
        self,
        x: pd.DataFrame,
    ):
        """
        add an intercept to x.
        """
        x.insert(0, "INTERCEPT", np.tile(1, x.shape[0]))

    def _set_inputs(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
        fit_intercept: bool = True,
    ):
        """
        set the input parameters
        """
        # add the input parameters
        assert isinstance(fit_intercept, bool), ValueError(fit_intercept)
        self.fit_intercept = fit_intercept

        # correct the shape of y and x
        self.y = self._simplify(y, "Y")
        self.x = self._simplify(x, "X")
        txt = "'x' and 'y' number of rows must be identical."
        assert self.x.shape[0] == self.y.shape[0], txt

    def _calculate_betas(self):
        """
        calculate the beta coefficients.
        """

        # add the ones for the intercept
        betas = self.x.copy()
        if self.fit_intercept:
            self._add_intercept(betas)

        # get the coefficients and intercept
        pinv = np.linalg.pinv
        self.betas = (pinv((betas.T @ betas).values) @ betas.T) @ self.y
        labels = self.betas.shape[0]
        labels = [i + (0 if self.fit_intercept else 1) for i in range(labels)]
        self.betas.index = pd.Index([f"beta{i}" for i in labels])

    def __repr__(self):
        """
        representation of the object.
        """
        return str(self.betas.__repr__())

    def __str__(self):
        """
        representation of the object.
        """
        return str(self.betas.__str__())

    def __call__(
        self,
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        """
        predict the fitted Y value according to the provided x.
        Parameters
        ----------
        x: np.ndarray | pd.DataFrame
            the input data used as predictor
        Returns
        -------
        y: pd.DataFrame
            the predicted values
        """
        v = self._simplify(x, "X")
        if self.fit_intercept:
            self._add_intercept(v)
        return v.values @ self.betas

    @property
    def r_squared(self):
        """
        return the calculated R-squared for the given model.
        Returns
        -------
        r2: float
            the calculated r-squared.
        """
        z = self(self.x)
        m = pd.concat([self.y, z], axis=1)
        return m.corr("pearson").values[0, 1] ** 2


class PolynomialRegression(LinearRegression):
    """
    Obtain the regression coefficients according to the Ordinary Least
    Squares approach.

    Parameters
    ----------
    y:  (samples, dimensions) numpy array or pandas.DataFrame
        the array containing the dependent variable.

    x:  (samples, 1) numpy array or pandas.DataFrame
        the array containing the indipendent variables.

    n: int
        the order of the polynome.

    fit_intercept: bool
        Should the intercept be included in the model?
        Otherwise it will be set to zero.
    """

    def __init__(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
        n: int = 1,
        fit_intercept: bool = True,
    ):
        # set the polynomial order
        assert isinstance(n, int), ValueError(n)
        assert n > 0, "'n' must be > 0"
        self.n = n
        super().__init__(y=y, x=x, fit_intercept=fit_intercept)

    def _expand_to_n(
        self,
        df: pd.DataFrame,
    ):
        """
        expand the df values up to the n-th order.
        """
        betas = []
        for i in range(self.n):
            b_new = df.copy()
            cols = [str(j) + f"{i + 1}" for j in b_new.columns]
            b_new.columns = pd.Index(cols)
            betas += [b_new ** (i + 1)]
        return pd.concat(betas, axis=1)

    def _calculate_betas(self):
        """
        calculate the beta coefficients.
        """
        # expand x to cope with the polynomial order
        betas = self._expand_to_n(self.x)

        # add the ones for the intercept
        if self.fit_intercept:
            self._add_intercept(betas)

        # get the coefficients and intercept
        pinv = np.linalg.pinv
        self.betas = (pinv((betas.T @ betas).values) @ betas.T) @ self.y
        labels = self.betas.shape[0]
        labels = [i + (0 if self.fit_intercept else 1) for i in range(labels)]
        self.betas.index = pd.Index([f"beta{i}" for i in labels])

    def __call__(
        self,
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        """
        predict the fitted Y value according to the provided x.

        Parameters
        ----------
        x: np.ndarray | pd.DataFrame
            the input data used as predictor
        Returns
        -------
        y: pd.DataFrame
            the predicted values
        """
        v = self._expand_to_n(self._simplify(x, "X"))
        if self.fit_intercept:
            self._add_intercept(v)
        return v.values @ self.betas


class PowerRegression(LinearRegression):
    """
    Obtain the regression coefficients according to the power model:

                y = a + b_0 * x_1 ^ b_1 * ... * x_n ^ b_n

    Parameters
    ----------
    y:  (samples, dimensions) numpy array or pandas.DataFrame
        the array containing the dependent variable.

    x:  (samples, features) numpy array or pandas.DataFrame
        the array containing the indipendent variables.
    """

    def __init__(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        super().__init__(y=y, x=x, fit_intercept=True)

    def _set_inputs(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
        fit_intercept: bool = True,
    ):
        """
        set the input parameters
        """
        super()._set_inputs(y=y, x=x, fit_intercept=fit_intercept)

        # check both x and y are positive
        assert np.all(self.y.values > 0), "'y' must be positive only."
        assert np.all(self.x.values > 0), "'x' must be positive only."

    def _calculate_betas(self):
        """
        calculate the beta coefficients.
        """
        # add the ones for the intercept
        betas = self.x.applymap(np.log)
        self._add_intercept(betas)

        # get the coefficients and intercept
        logy = self.y.applymap(np.log)
        pinv = np.linalg.pinv
        self.betas = (pinv((betas.T @ betas).values) @ betas.T) @ logy
        self.betas.iloc[0] = np.e ** self.betas.iloc[0]
        labels = [i for i in range(self.betas.shape[0])]
        self.betas.index = pd.Index([f"beta{i}" for i in labels])

    def __call__(
        self,
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        """
        predict the fitted Y value according to the provided x.
        """
        v = self._simplify(x, "X")
        o = np.ones((v.shape[0], self.betas.shape[1]))
        o = pd.DataFrame(o, index=v.index, columns=self.betas.columns)
        o *= self.betas.iloc[0].values
        for i in np.arange(1, self.betas.shape[0]):
            o *= v.values ** self.betas.iloc[i].values
        return o


class HyperbolicRegression(PowerRegression):
    """
    Obtain the regression coefficients according to the (Rectangular) Least
    Squares Hyperbolic function:

                            y = a / x + b

    Parameters
    ----------

    y:  (samples, dimensions) numpy array or pandas.DataFrame
        the array containing the dependent variable.
    x:  (samples, features) numpy array or pandas.DataFrame
        the array containing the indipendent variables.
    """

    def __init__(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        super().__init__(y=y, x=x)

    def _calculate_betas(self):
        """
        calculate the beta coefficients.
        """
        betas = self.x ** (-1)
        self._add_intercept(betas)
        pinv = np.linalg.pinv
        self.betas = (pinv((betas.T @ betas).values) @ betas.T) @ self.y
        labels = [i for i in range(self.betas.shape[0])]
        self.betas.index = pd.Index([f"beta{i}" for i in labels])

    def __call__(
        self,
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        """
        predict the fitted Y value according to the provided x.
        """
        v = self._simplify(x, "X") ** (-1)
        self._add_intercept(v)
        return v.values @ self.betas


class ExponentialRegression(LinearRegression):
    """
    Obtain the regression coefficients according to the exponential function:

                            y = a * BASE ** x + b

    Parameters
    ----------
    y:  (samples, dimensions) numpy array or pandas.DataFrame
        the array containing the dependent variable.

    x:  (samples, features) numpy array or pandas.DataFrame
        the array containing the indipendent variables.

    b: float
        the base of the exponential part of the equation
    """

    def __init__(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
        b: float = np.e,
    ):
        self.base = b
        super().__init__(y=y, x=x)

    def _calculate_betas(self):
        """
        calculate the beta coefficients.
        """
        betas = self.base**self.x
        self._add_intercept(betas)
        pinv = np.linalg.pinv
        self.betas = (pinv((betas.T @ betas).values) @ betas.T) @ self.y
        labels = [i for i in range(self.betas.shape[0])]
        self.betas.index = pd.Index([f"beta{i}" for i in labels])

    def __call__(
        self,
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        """
        predict the fitted Y value according to the provided x.
        """
        v = self.base ** self._simplify(x, "X")
        self._add_intercept(v)
        return v.values @ self.betas


class _Axis(LinearRegression):
    """
    generate the axis object defining one single axis of a 2D geometric figure.

    Parameters
    ----------
    y:  (samples, dimensions) numpy array or pandas.DataFrame
        the array containing the dependent variable.

    x:  (samples, features) numpy array or pandas.DataFrame
        the array containing the indipendent variables.
    """

    _vertex: tuple[tuple[float, float], tuple[float, float]]

    def __init__(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        super().__init__(y=y, x=x, fit_intercept=True)
        txt = "Axis must be defined by 2 elements only."
        assert self.y.shape[0] == 2, txt
        assert self.x.shape[0] == 2, txt

        # set the vertex
        x = self.x.values.flatten().astype(float)
        y = self.y.values.flatten().astype(float)
        self._vertex = ((x[0], y[0]), (x[1], y[1]))

    @property
    def angle(self):
        """
        return the angle (in radians) of the axis.
        """
        return float(np.arctan(self.betas.loc["beta1"].values[0]))

    @property
    def length(self):
        """
        get the distance between the two vertex.
        """
        a, b = self._vertex
        return float(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5)

    @property
    def vertex(self):
        """
        return the vertex of the axis
        """
        return self._vertex


class EllipsisRegression(LinearRegression):
    """
    calculate the beta coefficients equivalent to the fit the coefficients
    eiv_pos,b,cnd,d,e,f, representing an ellipse described by the formula

        b_0 * x^2 + b_1 * xy + b_2 * y^2 + b_3 * x + b_4 * y + b_5 = 0

    Based on the algorithm of Halir and Flusser.

    References
    ----------
    Halir R, Flusser J. Numerically stable direct least squares fitting of
        ellipses. InProc. 6th International Conference in Central Europe on
        Computer Graphics and Visualization. WSCG 1998 (Vol. 98, pp. 125-132).
        Citeseer. https://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=DF7A4B034A45C75AFCFF861DA1D7B5CD?doi=10.1.1.1.7559&rep=rep1&type=pdf

    Parameters
    ----------
    y:  (samples, dimensions) numpy array or pandas.DataFrame
        the array containing the dependent variable.
    x:  (samples, features) numpy array or pandas.DataFrame
        the array containing the indipendent variables.
    """

    def __init__(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        super().__init__(y=y, x=x)
        assert self.x.shape[1] == 1, "x can be unidimensional only"
        assert self.y.shape[1] == 1, "y can be unidimensional only"

    def __call__(
        self,
        x: Union[np.ndarray, pd.DataFrame, list, int, float, None] = None,
        y: Union[np.ndarray, pd.DataFrame, list, int, float, None] = None,
    ):
        """
        predict the x given y or predict y given x.
        Parameters
        ----------
        x OR y: (samples, 1) numpy array or pandas.DataFrame
            the array containing the dependent variable.
        Returns
        -------
        y OR x: (samples, 2) numpy array or pandas.DataFrame
            the array containing the dependent variable.
        Note
        ----
        only x or y can be provided. None is returned if the provided value
        lies outside the ellipsis boundaries.
        """
        # check the entries
        assert x is not None or y is not None, "'x' or 'y' must be provided."
        assert x is None or y is None, "only 'x' or 'y' must be provided."
        if x is not None:
            v = self._simplify(x, "X")
            o = np.atleast_2d([self._get_roots(x=i) for i in v.values])
            cols = ["Y0", "Y1"]
        elif y is not None:
            v = self._simplify(y, "Y")
            o = np.atleast_2d([self._get_roots(y=i) for i in v.values])
            cols = ["X0", "X1"]
        else:
            raise ValueError("x or y must be not None.")
        assert v.shape[1] == 1, "Only 1D arrays can be provided."
        return pd.DataFrame(o, columns=cols, index=v.index).astype(float)

    def _calculate_betas(self):
        """
        calculate the regression coefficients.
        """
        # quadratic part of the design matrix
        xval = self.x.values.flatten()
        yval = self.y.values.flatten()
        d_1 = np.vstack([xval**2, xval * yval, yval**2]).T

        # linear part of the design matrix
        d_2 = np.vstack([xval, yval, np.ones(len(xval))]).T

        # quadratic part of the scatter matrix
        s_1 = d_1.T @ d_1

        # combined part of the scatter matrix
        s_2 = d_1.T @ d_2

        # linear part of the scatter matrix
        s_3 = d_2.T @ d_2

        # reduced scatter matrix
        cnd = np.array(((0, 0, 2), (0, -1, 0), (2, 0, 0)), dtype=float)
        trc = -np.linalg.inv(s_3) @ s_2.T
        mat = np.linalg.inv(cnd) @ (s_1 + s_2 @ trc)

        # solve the eigen system
        eigvec = np.linalg.eig(mat)[1]

        # evaluate the coefficients
        con = 4 * eigvec[0] * eigvec[2] - eigvec[1] ** 2
        eiv_pos = eigvec[:, np.nonzero(con > 0)[0]]
        coefs = np.concatenate((eiv_pos, trc @ eiv_pos)).ravel()
        names = [f"beta{i}" for i in range(len(coefs))]
        self.betas = pd.DataFrame(coefs, index=names, columns=["CART. COEFS"])

        # get the axes angles
        # ref: http://www.geom.uiuc.edu/docs/reference/CRC-formulas/node28.html
        a, c, b = self.betas.values.flatten()[:3]

        # get the axes angles
        if c == 0:
            raise ValueError("coefficient c = 0.")
        m0 = (b - a) / c
        m0 = (m0**2 + 1) ** 0.5 + m0
        if m0 == 0:
            raise ValueError("m0 = 0.")
        m1 = -1 / m0

        # We know that the two axes pass from the centre of the ellipsis
        # and we also know the angle of the major and minor axes.
        # Therefore the intercept of the fitting lines describing the two
        # axes can be found.
        x0, y0 = self.center
        i0 = y0 - x0 * m0
        i1 = y0 - x0 * m1

        # get the crossings between the two axes and the ellipsis
        p0_0, p0_1 = self.get_crossings(m=m0, i=i0)
        p1_0, p1_1 = self.get_crossings(m=m1, i=i1)

        # generate the two axes
        ax0 = _Axis(x=[p0_0[0], p0_1[0]], y=[p0_0[1], p0_1[1]])
        ax1 = _Axis(x=[p1_0[0], p1_1[0]], y=[p1_0[1], p1_1[1]])

        # sort the axes
        if ax0.length < ax1.length:
            ax0, ax1 = ax1, ax0

        # store the axes
        self.axis_major = ax0
        self.axis_minor = ax1

    def get_crossings(
        self,
        m: Union[int, float],
        i: Union[int, float],
    ):
        """
        get the crossings between the provided line and the ellipsis

        Parameters
        ----------
        m: float
            the slope of the axis line

        i: float
            the intercept of the axis line

        Returns
        -------
        p0, p1: tuple
            the coordinates of the crossing points. It returns None if
            the line does not touch the ellipsis.
        """
        a, b, c, d, e, f = self.betas.values.flatten()
        a_ = a + b * m + c * m**2
        b_ = b * i + 2 * m * i * c + d + e * m
        c_ = c * i**2 + e * i + f
        d_ = b_**2 - 4 * a_ * c_
        if d_ < 0:
            return (None, None), (None, None)
        e_ = 2 * a_
        if a_ == 0:
            return (None, None), (None, None)
        f_ = -b_ / e_
        g_ = (d_**0.5) / e_
        x0 = f_ - g_
        x1 = f_ + g_
        return (x0, x0 * m + i), (x1, x1 * m + i)

    def _solve(
        self,
        a: float,
        b: float,
        c: float,
    ):
        """
        obtain the solutions of a second order polynomial having form:
                a * x**2 + b * x + c = 0

        Parameters
        ----------
        a, b, c: float
            the coefficients of the equation.

        Returns
        -------
        x0, x1: float | None
            the roots of the polynomial. None is returned if the solution
            is impossible.
        """
        d = b**2 - 4 * a * c
        if d < 0:
            raise ValueError("b**2 - 4 * a * c < 0")
        k = (2 * a) ** (-1)
        i = -b * k
        j = k * d**0.5
        return float(i + j), float(i - j)

    def _get_roots(
        self,
        x: Union[float, int, None] = None,
        y: Union[float, int, None] = None,
    ):
        """
        obtain the roots of a second order polynomial having form:

                a * x**2 + b * x + c = 0

        Parameters
        ----------
        x: float | int | None
            the given x value.

        y: float | int | None
            the given y value.

        Returns
        -------
        x0, x1: float | None
            the roots of the polynomial. None is returned if the solution
            is impossible.
        """
        # get the coefficients
        a_, b_, c_, d_, e_, f_ = self.betas.values.flatten()
        if y is not None and x is None:
            y_ = float(y)
            a, b, c = a_, b_ * y_ + d_, f_ + c_ * y_**2 + e_ * y_
        elif x is not None and y is None:
            x_ = float(x)
            a, b, c = c_, b_ * x_ + e_, f_ + a_ * x_**2 + d_ * x_
        else:
            raise ValueError("Only one 'x' or 'y' must be provided.")

        # get the roots
        return self._solve(a, b, c)

    def is_inside(
        self,
        x: Union[int, float],
        y: Union[int, float],
    ):
        """
        check whether the point (x, y) is inside the ellipsis.

        Parameters
        ----------
        x: float
            the x axis coordinate

        y: float
            the y axis coordinate

        Returns
        -------
        i: bool
            True if the provided point is contained by the ellipsis.
        """
        y0, y1 = self(x=x).values.flatten()
        return bool((y0 is not None) & (y > min(y0, y1)) & (y <= max(y0, y1)))

    @property
    def center(self):
        """
        get the center of the ellipsis as described here:
        https://mathworld.wolfram.com/Ellipse.html

        Returns
        -------
        x0, y0: float
            the coordinates of the centre of the ellipsis.
        """
        a, b, c, d, e = self.betas.values.flatten()[:-1]
        den = b**2 - 4 * a * c
        x = float((2 * c * d - b * e) / den)
        y = float((2 * a * e - b * d) / den)
        return x, y

    @property
    def area(self):
        """
        the area of the ellipsis.

        Returns
        -------
        a: float
            the area of the ellipsis.
        """
        return float(np.pi * self.axis_major.length * self.axis_minor.length)

    @property
    def perimeter(self):
        """
        the (approximated) perimeter of the ellipsis as calculated
        by the "infinite series approach".
                P = pi * (a + b) * sum_{n=0...N} (h ** n / (4 ** (n + 1)))
        where:
            h = (a - b) ** 2 / (a ** 2 + b ** 2)
            a = axis major
            b = axis minor
            N = any natural number.

        Note:
        -----
        N is set such as the output measure no longer changes up to the
        12th decimal number.

        Returns
        -------
        p: float
            the approximated perimeter of the ellipsis.
        """
        a = self.axis_major.length / 2
        b = self.axis_minor.length / 2
        if a == 0 and b == 0:
            raise ValueError("a and b coefficients = 0.")
        h = (a - b) ** 2 / (a**2 + b**2)
        c = np.pi * (a + b)
        p_old = -c
        p = c
        n = 0
        q = 1
        while n == 0 or abs(p_old - p) > 1e-12:
            p_old = p
            n += 1
            q += h**n / 4**n
            p = c * q

        return float(p)

    @property
    def eccentricity(self):
        """
        return the eccentricity parameter of the ellipsis.
        """
        b = self.axis_minor.length / 2
        a = self.axis_major.length / 2
        if a == 0:
            raise ValueError("coefficient a = 0")
        return float(1 - b**2 / a**2) ** 0.5

    @property
    def foci(self):
        """
        return the coordinates of the foci of the ellipses.

        Returns
        -------
        f0, f1: tuple
            the coordinates of the crossing points. It returns None if
            the line does not touch the ellipsis.
        """
        a = self.axis_major.length / 2
        p = self.axis_major.angle
        x, y = a * self.eccentricity * np.array([np.cos(p), np.sin(p)])
        x0, y0 = self.center
        return (float(x0 - x), float(y0 - y)), (float(x0 + x), float(y0 + y))

    @property
    def domain(self):
        """
        return the domain of the ellipse.

        Returns
        -------
        x1, x2: float
            the x-axis boundaries of the ellipse.
        """

        # get the roots to for the 2nd order equation to be solved
        a_, b_, c_, d_, e_, f_ = self.betas.values.flatten()
        a = b_**2 - 4 * a_ * c_
        b = 2 * b_ * e_ - 4 * c_ * d_
        c = e_**2 - 4 * c_ * f_

        # solve the equation
        x0, x1 = np.sort(self._solve(a, b, c))
        return float(x0), float(x1)

    @property
    def codomain(self):
        """
        return the codomain of the ellipse.

        Returns
        -------
        y1, y2: float
            the y-axis boundaries of the ellipse.
        """
        # get the roots to for the 2nd order equation to be solved
        a_, b_, c_, d_, e_, f_ = self.betas.values.flatten()
        a = b_**2 - 4 * a_ * c_
        b = 2 * b_ * d_ - 4 * a_ * e_
        c = d_**2 - 4 * a_ * f_

        # solve the equation
        y0, y1 = np.sort(self._solve(a, b, c))
        return float(y0), float(y1)


class CircleRegression(LinearRegression):
    """
    generate a circle from the provided data in a least squares sense.

    References
    ----------
    https://lucidar.me/en/mathematics/least-squares-fitting-of-circle/

    Parameters
    ----------
    y:  (samples, dimensions) numpy array or pandas.DataFrame
        the array containing the dependent variable.

    x:  (samples, features) numpy array or pandas.DataFrame
        the array containing the indipendent variables.
    """

    def __init__(
        self,
        y: Union[np.ndarray, pd.DataFrame, list, int, float],
        x: Union[np.ndarray, pd.DataFrame, list, int, float],
    ):
        super().__init__(y=y, x=x)
        assert self.x.shape[1] == 1, "x can be unidimensional only"
        assert self.y.shape[1] == 1, "y can be unidimensional only"

    def _calculate_betas(self):
        """
        calculate the regression coefficients.
        """
        x = self.x.values.flatten()
        y = self.y.values.flatten()
        i = np.tile(1, len(y))
        a = np.vstack(np.atleast_2d(x, y, i)).T
        b = np.atleast_2d(x**2 + y**2).T
        ix = [f"beta{i}" for i in range(a.shape[1])]
        cl = ["CART. COEFS"]
        pinv = np.linalg.pinv
        self.betas = pd.DataFrame(pinv(a.T @ a) @ a.T @ b, index=ix, columns=cl)

    def _get_roots(
        self,
        x: Union[float, int, None] = None,
        y: Union[float, int, None] = None,
    ):
        """
        obtain the roots of a second order polynomial having form:
                a * x**2 + b * x + c = 0

        Parameters
        ----------
        x: Union[float, int, None] = None,
            the given x value.

        y: Union[float, int, None] = None,
            the given y value.

        Returns
        -------
        x0, x1: float | None
            the roots of the polynomial.
        """
        # get the coefficients
        x0, y0 = self.center
        r = self.radius
        if y is not None and x is None:
            a, b, c = 1, -2 * x0, x0**2 - r**2 + (float(y) - y0) ** 2
        elif x is not None and y is None:
            a, b, c = 1, -2 * y0, y0**2 - r**2 + (float(x) - x0) ** 2
        else:
            raise ValueError("Only one 'x' or 'y' must be provided.")

        # get the roots
        d = b**2 - 4 * a * c
        if d < 0:
            raise ValueError("b**2 - 4 * a * c < 0")
        if a == 0:
            raise ValueError("coefficient a = 0")
        return float((-b - d**0.5) / (2 * a)), float((-b + d**0.5) / (2 * a))

    def __call__(
        self,
        x: Union[np.ndarray, pd.DataFrame, list, int, float, None] = None,
        y: Union[np.ndarray, pd.DataFrame, list, int, float, None] = None,
    ):
        """
        predict the x given y or predict y given x.

        Parameters
        ----------
        x OR y: (samples, 1) numpy array or pandas.DataFrame
            the array containing the dependent variable.

        Returns
        -------
        y OR x: (samples, 2) numpy array or pandas.DataFrame
            the array containing the dependent variable.

        Note
        ----
        only x or y can be provided. None is returned if the provided value
        lies outside the ellipsis boundaries.
        """
        # check the entries
        assert x is not None or y is not None, "'x' or 'y' must be provided."
        assert x is None or y is None, "only 'x' or 'y' must be provided."
        if x is not None:
            v = self._simplify(x, "X")
            o = np.atleast_2d([self._get_roots(x=i) for i in v.values])
            cols = ["Y0", "Y1"]
        elif y is not None:
            v = self._simplify(y, "Y")
            o = np.atleast_2d([self._get_roots(y=i) for i in v.values])
            cols = ["X0", "X1"]
        else:
            raise ValueError("x or y must be not None")
        assert v.shape[1] == 1, "Only 1D arrays can be provided."
        return pd.DataFrame(o, columns=cols, index=v.index).astype(float)

    def is_inside(
        self,
        x: Union[int, float],
        y: Union[int, float],
    ):
        """
        check whether the point (x, y) is inside the ellipsis.

        Parameters
        ----------
        x: float
            the x axis coordinate

        y: float
            the y axis coordinate

        Returns
        -------
        i: bool
            True if the provided point is contained by the ellipsis.
        """
        y0, y1 = self(x=x).values.flatten()
        return bool((y0 is not None) & (y > min(y0, y1)) & (y <= max(y0, y1)))

    @property
    def radius(self):
        """
        get the radius of the circle.

        Returns
        -------
        r: float
            the radius of the circle.
        """
        a, b, c = self.betas.values.flatten()
        return float((4 * c + a**2 + b**2) ** 0.5) * 0.5

    @property
    def center(self):
        """
        get the center of the circle.

        Returns
        -------
        x0, y0: float
            the coordinates of the centre of the cicle.
        """
        a, b = self.betas.values.flatten()[:-1]
        return float(a * 0.5), float(b * 0.5)

    @property
    def area(self):
        """
        the area of the circle.

        Returns
        -------
        a: float
            the area of the circle.
        """
        return float(np.pi * self.radius**2)

    @property
    def perimeter(self):
        """
        the perimeter of the circle.

        Returns
        -------
        p: float
            the perimeter of the circle.
        """
        return float(2 * self.radius * np.pi)

    @property
    def domain(self):
        """
        return the domain of the circle.

        Returns
        -------
        x1, x2: float
            the x-axis boundaries of the circle.
        """
        x = self.center[0]
        r = self.radius
        return float(x - r), float(x + r)

    @property
    def codomain(self):
        """
        return the codomain of the circle.

        Returns
        -------
        y1, y2: float
            the y-axis boundaries of the circle.
        """
        y = self.center[1]
        r = self.radius
        return float(y - r), float(y + r)
