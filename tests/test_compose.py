from compose.composeproject import ComposeProject
import json


def test_compose():
    with open('tests/test_compose_resources/deplyment_with_createoption.json') as json_file:
        json_data = json.load(json_file)
        proj = ComposeProject(json_data)
        proj.parse_services()
        proj.dump('tests/test_compose_resources/docker-compose_test.yml')
        test_output = open('tests/test_compose_resources/docker-compose_test.yml', 'r').read()
        standard_output = open('tests/test_compose_resources/docker-compose.yml', 'r').read()
        assert test_output == standard_output
