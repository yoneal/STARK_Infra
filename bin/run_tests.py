import pytest

pytest_args = [
    '-v',
    '--cov=lambda/test_cases'
]
return_code = pytest.main(pytest_args)
exit(return_code)