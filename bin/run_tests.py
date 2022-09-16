import pytest

pytest_args = [
    '-v'
]
return_code = pytest.main(pytest_args)
exit(return_code)