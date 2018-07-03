from compose.composeproject import ComposeProject
import json


def test_compose():
    with open('test_compose_resources/deplyment_with_createoption.json') as json_file:
        json_data = json.load(json_file)
        proj = ComposeProject(json_data)
        proj.parse_services()
        proj.dump('test_compose_resources/docker-compose_test.yml')
        actual_output  = open('test_compose_resources/docker-compose_test.yml', 'r').read()
        expected_output = open('test_compose_resources/docker-compose.yml', 'r').read()
        assert actual_output == expected_output
