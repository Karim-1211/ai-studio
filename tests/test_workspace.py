def test_workspace_contains_compact_knowledge_drawer(client):
    response = client.get("/")

    assert response.status_code == 200

    page = response.get_data(as_text=True)

    assert 'class="header compact-header"' in page
    assert 'id="knowledgeSelectionSummary"' in page
    assert 'id="documentPanelBody"' in page
    assert 'id="documentCloseButton"' in page
    assert 'id="chatKnowledgeTab"' in page
    assert 'id="globalKnowledgeTab"' in page


def test_workspace_contains_website_knowledge_controls(client):
    response = client.get("/")

    assert response.status_code == 200

    page = response.get_data(as_text=True)

    assert 'id="websiteUrlInput"' in page
    assert 'id="websiteAddButton"' in page
    assert 'id="websiteSourceList"' in page
    assert 'id="websiteSourceCount"' in page


def test_workspace_contains_attachment_composer_controls(client):
    page = client.get("/").get_data(as_text=True)

    assert 'id="attachmentInput"' in page
    assert 'id="attachmentButton"' in page
    assert 'id="attachmentPreviewList"' in page
    assert 'id="attachmentStatus"' in page
    assert '<textarea\n          id="prompt"' in page


def test_workspace_contains_social_knowledge_controls(client):
    page = client.get("/").get_data(as_text=True)

    assert 'id="socialUrlInput"' in page
    assert 'id="socialManualText"' in page
    assert 'id="socialAddButton"' in page
    assert 'id="socialSourceList"' in page
    assert 'id="socialSourceCount"' in page
