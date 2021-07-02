def test_package_import():
    import botcity.base as base
    assert base.__file__ != ""
