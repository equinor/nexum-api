import pytest
from httpx import AsyncClient
from src.seed_database import GenerateUuid
from src.services.decision_tree.decision_tree_creator import DecisionTreeGraph
from src.dtos.decision_tree_dtos import EdgeUUIDDto
from src.session_manager import sessionmanager
from src.dependencies import get_project_service, get_structure_service

@pytest.mark.asyncio
async def test_decision_tree_endpoint(client: AsyncClient):
    project_id = GenerateUuid.as_uuid("dt_from_id_project")
    response = await client.get(f"/structure/{project_id}/DT")
    response = await client.get(f"/structure/{project_id}/decision_tree")
    assert response.status_code == 200, f"Failed to create decision tree: {response.text}"

@pytest.mark.asyncio
@pytest.mark.skip(reason="Skipping, need to redesign test due to different approach to utility.")
async def test_decision_tree():
    await sessionmanager.init_db()
    project_service = await get_project_service()
    structure_service = await get_structure_service()

    project_uuid = GenerateUuid.as_uuid("dt_from_id_project")
    dt_from_id = await structure_service.create_decision_tree(project_uuid)

    project_uuid2 = GenerateUuid.as_uuid("dt_project")
    issues = []
    edges = []
    async for session in sessionmanager.get_session():
        (
            issues,
            edges,
        ) = await project_service.get_influence_diagram_data(session, project_uuid2)
    root_id = GenerateUuid.as_uuid("dt_uncertainty_S")
    root_issue = next((issue for issue in issues if issue.id == root_id), None)
    assert root_issue != None

    decision_tree_graph = DecisionTreeGraph(root=root_issue.id)
    for issue in issues:
        await decision_tree_graph.add_node(issue.id)

    for edge in edges:
        tail_node = [x for x in issues if x.id==edge.tail_node.issue_id][0]
        head_node = [x for x in issues if x.id==edge.head_node.issue_id][0]
        ee = EdgeUUIDDto(tail=tail_node.id, head=head_node.id)
        await decision_tree_graph.add_edge(ee)

    no_nodes_id = dt_from_id.nx.number_of_nodes() # type: ignore
    no_edges_id = dt_from_id.nx.number_of_edges() # type: ignore

    no_nodes_dt = decision_tree_graph.nx.number_of_nodes() # type: ignore
    no_edges_dt = decision_tree_graph.nx.number_of_edges()  # type: ignore

    assert no_edges_id == no_edges_dt
    assert no_nodes_id == no_nodes_dt
