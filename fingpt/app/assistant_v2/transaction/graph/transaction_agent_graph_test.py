import os

from app.assistant_v2.transaction.graph.transaction_agent_graph import TransactionGraph


async def test_transaction_graph():
    graph = TransactionGraph()
    image_name = "transaction_graph.png"
    # Generate mermaid image for the graph, if it works, the test is passed
    (await graph.get_graph()).draw_mermaid_png(output_file_path=image_name)
    # check whether the file is created
    assert os.path.exists(image_name)
    # remove the file
    os.remove(image_name)
