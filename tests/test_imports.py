def test_core_imports():
    import app
    import graph
    import llm
    import ocr_utils


def test_agents_import():
    from agents.document_agent import document_agent
    from agents.matching_agent import matching_agent
    from agents.discrepancy_agent import discrepancy_agent
    from agents.resolution_agent import resolution_agent
