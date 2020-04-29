import requests
import json
from pathlib import Path
import csv
import sys
from config import AsanaConfig

# Asana API base url
base_asana_url = 'https://app.asana.com/api/1.0/'

# Asana auth token
asana_auth_token = AsanaConfig.authtoken

# Record limit (max at 100)
limit = 50

# Asana workspace id
workspace = AsanaConfig.workspace

# If get_all_data is True, then the script will call Get User until all data is retrieved.
get_all_data = True
#get_all_data = False

# projects endpoint
url = base_asana_url + "projects?limit=" + str(limit) + "&workspace=" + workspace

headers = {
    'Authorization': asana_auth_token
}

# set path for current directory and file name for the Export file
data_folder = Path(".")
export_file = data_folder / "asana_projects.csv"
exportfile = open(export_file,"w+")

# set csv column header names (Project Name, Last Status)
column_list = ['Project Name','Status Title','Color','Body']

# set delimiter
csv_delim = '","'

# Join the values from the column list to build a csv title row with delimiters
column_headings = '"' + csv_delim.join(column_list) + '"'

exportfile.write(column_headings+'\n')

exportfile.close

# Set conditions for while loop. Used with pagination.
next = False
first = True
next_url = ""

# create an empty project id list


# while loop to control first and subsequent requests
while (next or first):
    # If next_url is defined, this is not the first time through the loop,
    # and we should have the next_url generated

    response_json = []

    # if this is the second (or greater) call

    if next:
        # Make the API call
        response = requests.request("GET", next_url, headers=headers)
        response_json = response.json()

        # parse link headers... find out what this means
        #response_links = requests.utils.parse_header_links(response.headers['Link'].rstrip('>').replace('>,<', ',<'))
        next_url = ""

        if (response.status_code == 200):
            #print('status 200')
            if(response_json['next_page']['uri'] is None):
                print("end of the file")
                print("Done")
                exit()
            next_url = response_json['next_page']['uri']
        else:
            print("died at NEXT")
            print(response.status_code)
            print(response_json)
            exit(1)

    if first:
        print('making first request')
        #make request to asana and record the response
        response = requests.request("GET", url, headers=headers)
        response_json = response.json()

        next = False


        if (response.status_code == 200):
            #print('status 200')
            next_url = response_json['next_page']['uri']
            first = False
            next = True
        else:
            print("died at FIRST")
            print(response.status_code)
            print(response_json)
            exit(1)

    # write the response to file
    for entry in response_json['data']:
        csv_record = []
        csv_record.append(entry['name'])
        #print(entry['name'])
        project_id = entry['gid'];

        # look up project by id and get status id
        # base_url + /projects/<id>/project_statuses
        project_url = base_asana_url + "projects/" + project_id + "/project_statuses"
        #print(project_url)
        response = requests.request("GET", project_url, headers=headers)

        project_json = response.json()

        if len(project_json['data']) < 1:
            continue
        if (response.status_code == 200):
            first_id = project_json['data'][0]['gid']

            #print(first_id)
            #exit()

        else:
            print("died at project_json")
            print("status:" + str(response.status_code))
            print(project_url)
            exit()

        # look up project status by id of first item
        # base_url + /project_statuses/<status id>
        #print(first_id)
        status_url = base_asana_url + 'project_statuses/' + first_id
        #print(status_url)

        response = requests.request("GET", status_url, headers=headers)

        status_json = response.json()

        status_get = status_json['data'];

        #print(status_get)
        status_title = status_get['title']
        status_color = status_get['color']
        status_body = status_get['text']

        csv_record.append(status_title)

        if(status_color is None):
            csv_record.append("no color")
        else:
            csv_record.append(status_color)

        csv_record.append(status_body)

        #print(csv_record)

        try:
            column_row = '"' + csv_delim.join(csv_record) + '"'

        except TypeError:
            print("There's a problem in column_row")
            print(csv_record)
        except:
            print("error...")
            raise
        #print(csv_record)
        exportfile = open(export_file,"a+")
        exportfile.write(column_row+'\n')
        exportfile.close

        #exit()

#print(response_json['next_page']['uri'])
print("Done")
exit()
