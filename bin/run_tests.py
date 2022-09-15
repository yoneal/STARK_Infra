import pytest

pytest_args = [
    '../lambda/test_cases',
    '-v',
    '--cov'
]
return_code = pytest.main(pytest_args)
exit(return_code)