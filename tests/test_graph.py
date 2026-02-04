from graph import build_graph


def test_graph_builds():
    graph = build_graph()
    assert graph is not None
