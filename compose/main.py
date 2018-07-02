from composeproject import ComposeProject
import json

with open('compose/deplyment_with_createoption.json') as json_file:
    json_data = json.load(json_file)
    # custom_modules = json_data['modulesContent']['$edgeAgent']['properties.desired']['modules']
    proj = ComposeProject(json_data)
    proj.parse_services()
    print(proj.Services)
    proj.dump()
    # for name,config in custom_modules.items():
    #     print(name)
    #     create_options = config['settings']['createOptions']
    #     create_options = json.loads(create_options)
    #     proj = ComposeProject(create_options)
    #     proj.parse_services()
    #     print(proj.Services)
