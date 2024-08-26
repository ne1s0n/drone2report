#placeholder so that the automated pytest action in github does not complain
def inc(x):
    return x + 1


def test_answer():
    assert inc(3) == 4
