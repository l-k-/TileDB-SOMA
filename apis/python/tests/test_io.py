import numpy as np
import pyarrow as pa
import pytest
from scipy import sparse as sp

import tiledbsoma as soma
import tiledbsoma.io as somaio
from tiledbsoma import _factory
from tiledbsoma.options._tiledb_create_options import TileDBCreateOptions


@pytest.fixture
def src_matrix(request):
    format, shape, density = request.param
    if format == "dense":
        return (
            np.random.default_rng()
            .standard_normal(np.prod(shape), dtype=np.float32)
            .reshape(shape)
        )

    return sp.random(10, 89, density=density, format=format, dtype=np.float32)


@pytest.mark.parametrize(
    "tdb_create_options",
    [
        TileDBCreateOptions(write_X_chunked=False, goal_chunk_nnz=10000),
        TileDBCreateOptions(write_X_chunked=False, goal_chunk_nnz=100000),
        TileDBCreateOptions(write_X_chunked=True, goal_chunk_nnz=10000),
        TileDBCreateOptions(write_X_chunked=True, goal_chunk_nnz=100000),
        TileDBCreateOptions(write_X_chunked=True, remote_cap_nbytes=100000),
    ],
)
@pytest.mark.parametrize(
    "src_matrix",
    [
        ("dense", (10, 100), 1),
        ("dense", (1103, 107), 1),
        ("csc", (10, 89), 0.01),
        ("csr", (10, 89), 0.01),
        ("csc", (1001, 899), 0.3),
        ("csr", (1001, 899), 0.3),
    ],
    indirect=True,
)
def test_io_create_from_matrix_Dense_nd_array(tmp_path, tdb_create_options, src_matrix):
    """
    Test soma.io.from_matrix to a DenseNDArray.

    Cases:
    * src matrix is:  csc, csr, ndarray
    * _tiledb_platform_config.write_X_chunked: True or False
    * src_array bigger or smaller than _tiledb_platform_config.goal_chunk_nnz
    """
    somaio.create_from_matrix(
        soma.DenseNDArray,
        tmp_path.as_posix(),
        src_matrix,
        platform_config={"tiledb": {"create": tdb_create_options}},
    ).close()
    with _factory.open(tmp_path.as_posix()) as snda:
        assert snda.ndim == src_matrix.ndim

        read_back = snda.read((slice(None), slice(None))).to_numpy()

        if isinstance(src_matrix, np.ndarray):
            assert np.array_equal(read_back, src_matrix)
        else:
            assert np.array_equal(read_back, src_matrix.toarray())


@pytest.mark.parametrize(
    "tdb_create_options",
    [
        TileDBCreateOptions(write_X_chunked=False, goal_chunk_nnz=10000),
        TileDBCreateOptions(write_X_chunked=False, goal_chunk_nnz=100000),
        TileDBCreateOptions(write_X_chunked=True, goal_chunk_nnz=10000),
        TileDBCreateOptions(write_X_chunked=True, goal_chunk_nnz=100000),
    ],
)
@pytest.mark.parametrize(
    "src_matrix",
    [
        ("dense", (10, 100), 1),
        ("dense", (1103, 107), 1),
        ("csc", (10, 89), 0.01),
        ("csr", (10, 89), 0.01),
        ("csc", (1001, 899), 0.3),
        ("csr", (1001, 899), 0.3),
        ("csc", (10, 89), 0.00),  # yes, completely empty as corner case
        ("csr", (10, 89), 0.00),  # yes, completely empty as corner case
    ],
    indirect=True,
)
def test_io_create_from_matrix_Sparse_nd_array(
    tmp_path, tdb_create_options, src_matrix
):
    """
    Test soma.io.from_matrix to a SparseNDArray.

    Cases:
    * src matrix is:  csc, csr, ndarray
    * _tiledb_platform_config.write_X_chunked: True or False
    * src_array bigger or smaller than _tiledb_platform_config.goal_chunk_nnz
    """
    somaio.create_from_matrix(
        soma.SparseNDArray,
        tmp_path.as_posix(),
        src_matrix,
        platform_config={"tiledb": {"create": tdb_create_options}},
    ).close()

    with _factory.open(tmp_path.as_posix()) as snda:
        assert snda.ndim == src_matrix.ndim

        tbl = pa.concat_tables(snda.read((slice(None), slice(None))).tables())
        read_back = sp.csr_matrix(
            (
                tbl.column("soma_data").to_numpy(),
                (
                    tbl.column("soma_dim_0").to_numpy(),
                    tbl.column("soma_dim_1").to_numpy(),
                ),
            ),
            shape=src_matrix.shape,
        )

        # fast equality check using __ne__
        assert (sp.csr_matrix(src_matrix) != read_back).nnz == 0


@pytest.mark.parametrize(
    "num_rows",
    [0, 1, 2, 3, 4, 10, 100, 1_000, 10_000],
)
@pytest.mark.parametrize(
    "cap_nbytes",
    [1, 100, 1_000, 10_000],
)
def test_write_arrow_table(tmp_path, num_rows, cap_nbytes):
    """
    Additional focus-testing for tiledbsoma.io._write_arrow_table
    """

    schema = pa.schema(
        [
            ("foo", pa.int32()),
            ("bar", pa.float64()),
        ]
    )

    pydict = {}
    pydict["soma_joinid"] = list(range(num_rows))
    pydict["foo"] = [(e + 1) * 10 for e in range(num_rows)]
    pydict["bar"] = [(e + 1) / 25 for e in range(num_rows)]

    opt = soma.TileDBCreateOptions(remote_cap_nbytes=cap_nbytes)
    uri = tmp_path.as_posix()
    expect_error = cap_nbytes == 1 and num_rows > 0  # Not enough room for even one row

    with soma.DataFrame.create(uri, schema=schema) as sdf:
        table = pa.Table.from_pydict(pydict)
        if expect_error:
            with pytest.raises(soma.SOMAError):
                somaio.ingest._write_arrow_table(table, sdf, opt)
        else:
            somaio.ingest._write_arrow_table(table, sdf, opt)

    if not expect_error:
        with soma.DataFrame.open(uri) as sdf:
            pdf = sdf.read().concat().to_pandas()
            assert list(pdf["foo"]) == pydict["foo"]
