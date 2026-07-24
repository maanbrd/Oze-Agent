from api.routes.decisions import router


def test_decisions_api_exposes_get_only():
    methods = {
        method
        for route in router.routes
        for method in (route.methods or set())
    }
    assert methods <= {"GET"}
