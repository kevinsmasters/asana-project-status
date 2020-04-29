import requests
import json
from pathlib import Path
import csv
import datetime
import dateutil.relativedelta
import sys
import time

# Define Okta API base URL
base_okta_url = "https://etaconic.oktapreview.com"

# Define the API token required by Okta
okta_apikey = "00qOgQusuT2FjzAolH6BhsrjBV1TTbTluqKDTl8fU6"

# Define record limit (200 is the maximum accepted by Okta)
limit = 200

# If get_all_data is True, then the script will call Get User until all data is retrieved.
get_all_data = True
#get_all_data = False

# Define the Okta Users endpoint
url = base_okta_url + "/api/v1/users" + "?limit=" + str(limit)

# CSV - JSON Response Mapping
# ADD OTHER OKTA ATTRIBUTES OR CHANGE THE ORDER OF COLUMNS FOR THE CSV BELOW
column_list = ["id","firstName","lastName","displayName","login","email","lastLogin"]

# Construct the headers
headers = {
  'content-type': 'application/json',
	'Authorization': 'SSWS ' + okta_apikey
}

# Setup path for current directory and file name for the Export file
data_folder = Path(".")
export_file = data_folder / "okta_user_list.csv"
exportfile = open(export_file,"w+")
export_xfile = data_folder / "okta_user_list-Taco.csv"
exportxfile = open(export_xfile,"w+")

# Join the values from the column list to build a CSV title row, with delimeters
#col_headings = '"' + '", "'.join(column_list) + '"'
#exportfile.write(col_headings+'\n')
csv_delim = '","'

# Set conditions for while loop. Used with pagination.
next = False
first = True
next_url = ""

user_idlist = []
now = datetime.datetime.now()
# previous six months
less_six = now - dateutil.relativedelta.relativedelta(months=6)

# last 30 days
one_month = now - dateutil.relativedelta.relativedelta(days=40)

# While loop use to control first and subsequent requests
while (next or first):

	# If next_url is defined, this is not the first time through the loop,
	# and we should have the next_url generated from Okta

	response_json = []

	# If this is the second (or greater) call to Get Users

	if next:
		# Make the API call
		response = requests.request("GET", next_url, headers=headers)
		response_json = response.json()

		# Parse the LINK headers from the response.
		response_links = requests.utils.parse_header_links(response.headers['Link'].rstrip('>').replace('>,<', ',<'))
		next_url = ""

		# Look for the 'next' url in the response links.
		for linkobj in response_links:
			if linkobj['rel'] == 'next':
				next_url = linkobj['url']
				next = True
			else:
				next = False

	# If this is the first call to Get Users
	if first:

		# Make the request to Okta and record the response
		response = requests.request("GET", url, headers=headers)
		response_json = response.json()

		# Parse the LINK headers from the response.
		if (response.status_code == 200):
			response_links = requests.utils.parse_header_links(response.headers['Link'].rstrip('>').replace('>,<', ',<'))
			next_url = ""
			for linkobj in response_links:
				#print(linkobj['rel'])
				if linkobj['rel'] == 'next':
					next_url = linkobj['url']
					next = True

			# Turn off first flag so that the next option is selected on subsequent loops
			first = False

		else:
			print("died at FIRST")
			print(response.status_code)
			print(response_json)
			exit(1)

	# write the response to file
	for entry in response_json:

		# Build the CSV row
		csv_record = []

		# Loop through in column in the column list
		for col in column_list:
			# If we can find column in profile object append it
			if col in entry['profile']:
				csv_record.append(entry['profile'][col])

			# Else if we can find column in root object append it
			elif col in entry:
                # ignore people that never logged in
				if entry['lastLogin'] is None:
                    # TODO: find out if this can be done better without writing crap we'll eliminate later...
					csv_record.append('No Login')
				else:

                    # filter out people that haven't logged in within the past 6 months

					login_date = entry['lastLogin']
					login_date = login_date.split('T')
					login_date = login_date[0]
					login_date = datetime.datetime.strptime(login_date, '%Y-%m-%d')

					if login_date < one_month:
                        # TODO: this also, must be a way to exit from an if loop without writing garbage
                        #print("Login is within the past six months")
						csv_record.append('No Login')
					else:
                        #print("Login was from more than six months ago")
						csv_record.append(entry[col])

			# Else if we can't find, write a dash to preserve column format
			else:

				csv_record.append("-")

		# Write the CSV row to the file
		#print(csv_record)
		csv_line = '"' + csv_delim.join( csv_record ) + '"'
		#now = datetime.datetime.now()
		#date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
		#csv_line += ',"'+date_time+'"'

		if (csv_line.lower().find('login') == -1):
			#exportfile.write("%s\n" % (csv_line))
			usr_line = csv_line.split(',')
			user_id = usr_line[0]
			user_id = user_id.replace('"','')
			user_idlist.append(user_id)


	# If we don't want to get all data (i,e we only want 'limit' records), exit the loop.

	if get_all_data == False:
		break

#print(user_idlist)
#for userid in user_idlist:
	#print("This guy: "+ userid)
since_date = str(one_month)
since_date = since_date.replace(" ","T")
newcolumn_list = ["email","displayName","num_logins"]

newcol_headings = '"' + csv_delim.join(newcolumn_list) + '"'

exportfile.write(newcol_headings+'\n')
exportxfile.write(newcol_headings+'\n')

def write_user(userid):
    newurl = base_okta_url + "/api/v1/logs" + "?q=" + userid
    #newurl += '&since=' + since_date + "Z"
    newurl += '&since=2019-11-01T00:00:00Z&until=2019-11-31T00:00:00Z'
    newurl += '&filter=eventType eq "user.session.start"&limit=' + str(limit)

    thecount = 0
    tnext = False

    tfirst = True

    tnext_url = ""

    new_response_json = []

    response = requests.request("GET", newurl, headers=headers)

    new_response_json = response.json()
    if (response.status_code == 200):
        #print('good json')
        response_links = requests.utils.parse_header_links(response.headers['Link'].rstrip('>').replace('>,<', ',<'))
        tnext_url = ""
        for linkobj in response_links:
            if linkobj['rel'] == 'next':
                tnext_url = linkobj['url']
                tnext = True
        tfirst = False
        #print(new_response_json)
        #print(len(new_response_json))
        #exit(1)
    else:
        print("died at NEXT")
        print("status:" + str(response.status_code))
        print(new_response_json)
        exit(1)

    if len(new_response_json) > 0:
        name = new_response_json[0]["actor"]["displayName"]
        print(name)
        for entry in new_response_json:
        	thecount += 1
        	name = entry["actor"]["displayName"]
        	email = entry["actor"]["alternateId"]
        	#print(name)
        	#print(thecount)

        print(thecount)

        time.sleep(7)

        newcol_item = [email,name,str(thecount)]
        newcol_row = '"' + csv_delim.join( newcol_item ) + '"'

        if (newcol_row.lower().find('taconic.com') == -1):

            exportfile.write(newcol_row+'\n')

        else:
            exportxfile.write(newcol_row+'\n')

        exportfile.close
        exportxfile.close
    else:
        return
#print(newurl)
userarr = ["00udustn2e91Lsn1s0h7","00ub08cs2bZ6aqwcT0h7","00ub08dz1fUCCiLwl0h7","00ub08e9qkfJ3XATS0h7","00ud9rxlhlHC6GMSO0h7"]

for user in user_idlist:
    #print(user)
    write_user(user)

#write_user("00ub08cs2bZ6aqwcT0h7")
print("Done.")

# TODOS:
## Turn last bit into a function
## Call that function on each id in id_list
## Write each return to the export file
