import numpy as np
import pytest

import dask.array as da
from dask.array.utils import assert_eq, meta_from_array

asarrays = [np.asarray]

try:
    import sparse

    asarrays.append(sparse.COO.from_numpy)
except ImportError:
    pass

try:
    import cupy

    asarrays.append(cupy.asarray)
except ImportError:
    pass


@pytest.mark.parametrize("asarray", asarrays)
def test_meta_from_array(asarray):
    x = np.array(1)
    assert meta_from_array(x, ndim=1).shape == (0,)

    x = np.ones((1, 2, 3), dtype="float32")
    x = asarray(x)

    assert meta_from_array(x).shape == (0, 0, 0)
    assert meta_from_array(x).dtype == "float32"
    assert type(meta_from_array(x)) is type(x)

    assert meta_from_array(x, ndim=2).shape == (0, 0)
    assert meta_from_array(x, ndim=4).shape == (0, 0, 0, 0)
    assert meta_from_array(x, dtype="float64").dtype == "float64"
    assert meta_from_array(x, dtype=float).dtype == "float64"

    x = da.ones((1,))
    assert isinstance(meta_from_array(x), np.ndarray)

    assert meta_from_array(123) == 123
    assert meta_from_array("foo") == "foo"
    assert meta_from_array(np.dtype("float32")) == np.dtype("float32")


@pytest.mark.parametrize("meta", ["", "str", "", "str", b"", b"str"])
@pytest.mark.parametrize("dtype", [None, "bool", "int", "float"])
def test_meta_from_array_literal(meta, dtype):
    if dtype is None:
        assert meta_from_array(meta, dtype=dtype).dtype.kind in "SU"
    else:
        assert (
            meta_from_array(meta, dtype=dtype).dtype == np.array([], dtype=dtype).dtype
        )


def test_meta_from_array_type_inputs():
    x = meta_from_array(np.ndarray, ndim=2, dtype=np.float32)
    assert isinstance(x, np.ndarray)
    assert x.ndim == 2
    assert x.dtype == np.float32

    x = da.Array(
        {("x", 0, 0): (np.ones, (5, 5))},
        name="x",
        chunks=(5, 5),
        shape=(5, 5),
        meta=np.ndarray,
        dtype=float,
    )
    assert_eq(x, x)

    assert da.from_array(np.ones(5).astype(np.int32), meta=np.ndarray).dtype == np.int32


@pytest.mark.parametrize(
    "a,b",
    [
        (da.array([1]), 1.0),
        (da.array([1, 2]), [1.0, 2]),
        (da.array([1, 2]), np.array([1.0, 2])),
    ],
)
def test_assert_eq_checks_dtype(a, b):
    with pytest.raises(AssertionError, match="a and b have different dtypes"):
        assert_eq(a, b)

@pytest.mark.parametrize(
    "a,b",
    [
        (da.array([1]), da.array([[1]])),
        (da.array([0]), np.array([0, 1])),
        (da.array([]), da.array([1.1])),
    ],
)
def test_assert_eq_checks_shape(a, b):
   with pytest.raises(AssertionError, match="a and b have different shapes"):
      assert_eq(a, b)


@pytest.mark.parametrize(
    "a,b",
    [
        (da.array([1]), da.array([2])),
        (da.array([0, 1, 2]), np.array([0, 2, 1])),
        (da.array([1.3]), da.array([1.3001])),
        (da.array([1, 1, 1, 1.3]), np.array([1, 1, 1, 1.3001])),
        (da.array([[1.3]]), da.array([[1.3001]])),
        (da.array([1, 1, 1, 1.3]).sum(), 4.1),
        (1, 2)
    ],
)
def test_assert_eq_false(a, b):
   with pytest.raises(AssertionError, match="found values in 'a' and 'b' which differ by more than the allowed amount"):
      assert_eq(a, b)


@pytest.mark.parametrize(
    "a,b",
    [
        (da.array([1]), da.array([1])),
        (da.array([0, 1, 2]), np.array([0, 1, 2])),
        (da.array([1.3]), da.array([1.3])),
        (da.array([1, 1, 1, 1.3]), np.array([1, 1, 1, 1.3])),
        (da.array([[1.3]]), da.array([[1.3]])),
        (da.array([1, 1, 1, 1.3]).sum(), 4.3),
        (2, 2)
    ],
)
def test_assert_eq_true(a, b):
    assert assert_eq(a, b)
