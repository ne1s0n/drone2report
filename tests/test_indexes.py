import numpy as np
import d2r.tasks.matrix_returning_indexes as mri

def test_basic_stub():
    """Check that NDVI runs without error on simple arrays, without actually checking the returned values."""
    red = np.array([[1, 2, 3], [4, 5, 6]])
    nir = np.array([[1, 2, 3], [4, 5, 6]])
    test_image = np.stack((red, nir), axis=2)
    channel_list = ['red', 'nir']

    result = mri.NDVI(test_image, channel_list)
    # Just check shape & finite values for now
    assert result.shape == nir.shape
    assert np.all(np.isfinite(result))

