def pytest_addoption(parser):
    parser.addoption("--allow-real-hardware", action="store_true", default=False)
    parser.addoption("--target-serial", action="store", default=None)
    parser.addoption("--image-path", action="store", default=None)

def pytest_configure(config):
    config.addinivalue_line("markers", "real_hardware: mark test as real hardware test")
