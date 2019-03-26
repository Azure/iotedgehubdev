import os
from dotenv import load_dotenv

workingdirectory = os.getcwd()
filename = os.path.join(workingdirectory, '.env')
if os.path.exists(filename):
    load_dotenv(filename)
    print('env file loaded from {0}'.format(filename))
