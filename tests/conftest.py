"""Shared pytest fixtures and configuration for photogrammetry_importer tests."""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_blender_context():
    """Mock Blender context object."""
    context = MagicMock()
    context.scene = MagicMock()
    context.collection = MagicMock()
    context.view_layer = MagicMock()
    return context


@pytest.fixture
def mock_blender_operator():
    """Mock Blender operator object."""
    operator = MagicMock()
    operator.report = MagicMock()
    return operator


@pytest.fixture
def sample_camera_data():
    """Sample camera data for testing."""
    return {
        "id": 0,
        "model": "PINHOLE",
        "width": 1920,
        "height": 1080,
        "params": [1000.0, 1000.0, 960.0, 540.0],
    }


@pytest.fixture
def sample_image_data():
    """Sample image data for testing."""
    return {
        "id": 0,
        "qvec": [0.7071, 0.0, 0.7071, 0.0],
        "tvec": [1.0, 2.0, 3.0],
        "camera_id": 0,
        "name": "image_001.jpg",
        "xys": [],
        "point3D_ids": [],
    }


@pytest.fixture
def sample_point3d_data():
    """Sample 3D point data for testing."""
    return {
        "id": 0,
        "xyz": [1.0, 2.0, 3.0],
        "rgb": [255, 128, 0],
        "error": 0.5,
        "image_ids": [0, 1],
        "point2D_idxs": [0, 0],
    }


@pytest.fixture
def mock_preferences():
    """Mock addon preferences."""
    prefs = MagicMock()
    prefs.default_width = 1920
    prefs.default_height = 1080
    prefs.default_focal_length = 50.0
    prefs.default_sensor_width = 36.0
    prefs.default_pp_x = 0.5
    prefs.default_pp_y = 0.5
    prefs.add_camera_motion_as_animation = False
    prefs.add_image_planes = False
    prefs.image_plane_transparency = 0.5
    prefs.add_image_plane_emission = True
    prefs.image_plane_emission_strength = 1.0
    prefs.use_default_depth = True
    prefs.default_depth = 1.0
    prefs.import_depth_maps_as_point_cloud = False
    prefs.add_point_cloud_color_emission = True
    prefs.point_cloud_color_emission_strength = 1.0
    return prefs


@pytest.fixture
def sample_ply_content():
    """Sample PLY file content for testing."""
    return """ply
format ascii 1.0
element vertex 3
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
0.0 0.0 0.0 255 0 0
1.0 0.0 0.0 0 255 0
0.0 1.0 0.0 0 0 255
"""


@pytest.fixture
def sample_colmap_model_dir(temp_dir):
    """Create a sample COLMAP model directory structure."""
    model_dir = temp_dir / "colmap_model"
    model_dir.mkdir()
    
    (model_dir / "cameras.txt").write_text(
        "# Camera list with one line of data per camera:\n"
        "#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n"
        "1 PINHOLE 1920 1080 1000 1000 960 540\n"
    )
    
    (model_dir / "images.txt").write_text(
        "# Image list with two lines of data per image:\n"
        "#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n"
        "#   POINTS2D[] as (X, Y, POINT3D_ID)\n"
        "1 0.7071 0 0.7071 0 1 2 3 1 image_001.jpg\n"
        "\n"
    )
    
    (model_dir / "points3D.txt").write_text(
        "# 3D point list with one line of data per point:\n"
        "#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)\n"
        "1 1.0 2.0 3.0 255 128 0 0.5 1 0\n"
    )
    
    return model_dir


@pytest.fixture
def mock_log():
    """Mock logging function."""
    return MagicMock()


@pytest.fixture(autouse=True)
def setup_python_path():
    """Ensure the project root is in Python path."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_bpy():
    """Mock the bpy module for tests that don't run inside Blender."""
    bpy_mock = MagicMock()
    bpy_mock.data = MagicMock()
    bpy_mock.data.objects = MagicMock()
    bpy_mock.data.cameras = MagicMock()
    bpy_mock.data.collections = MagicMock()
    bpy_mock.data.images = MagicMock()
    bpy_mock.data.meshes = MagicMock()
    bpy_mock.context = MagicMock()
    bpy_mock.ops = MagicMock()
    bpy_mock.props = MagicMock()
    bpy_mock.types = MagicMock()
    bpy_mock.utils = MagicMock()
    
    sys.modules['bpy'] = bpy_mock
    yield bpy_mock
    
    if 'bpy' in sys.modules:
        del sys.modules['bpy']


@pytest.fixture
def mock_mathutils():
    """Mock the mathutils module for tests that don't run inside Blender."""
    mathutils_mock = MagicMock()
    mathutils_mock.Vector = MagicMock()
    mathutils_mock.Matrix = MagicMock()
    mathutils_mock.Quaternion = MagicMock()
    mathutils_mock.Euler = MagicMock()
    
    sys.modules['mathutils'] = mathutils_mock
    yield mathutils_mock
    
    if 'mathutils' in sys.modules:
        del sys.modules['mathutils']