"""
===============================================================================
 File Name   : jiraExtract.py
 Description : extract jira for data for specific assignee given in main
 Author      : Chami Abdellah (abdellah.chami_external@hse.com)
 Created     : 2025-09-07
 Last Updated: 2025-09-07
===============================================================================

 Change History:
 ------------------------------------------------------------------------------
 Date        Author             Description
 ----------  -----------------  ----------------------------------------------
 2025-09-07  Chami Abdellah          Initial version
===============================================================================
"""

from jira import JIRA
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

# Jira server options
jiraOptions = {'server': "https://xlibxli.atlassian.net/"}

# Jira client instance with authentication
jira = JIRA(options=jiraOptions, basic_auth=("abdellah.chami_external@hse.com", "ATATT3xFfGF0si73sVDjwDqcL97NLCSKcwlWvKKsfvYiuKJL6YLkrbwMFurskSN1XP35_vLuem-2BW_jchAYYaVu6srwDoHnAwMPycFEgMwe1QHc0ukxutt7N12aO-h4JzRmIsfV3GlGBe4d9LNSAvOFa3QEUDG8TJue7k0k7I5Df5FUD_kr8mk=F963BBD3"))


'''
function to extract history of issue
'''
def fetch_history(changelog):
    
    # uncomment to store data in CSV
    #list_history = []
    # base_path = Path("./issues_history")
    # file_name = key+".csv"
    # full_path = base_path / file_name

    # Print history details
    history_dict = dict()
    for history in changelog.histories:
        
        for item in history.items:
            if(item.field == "status"):

                # collect the time of each transition
                # used to calculate time that the user took in each transition
                match item.fromString:
                    case "In Progress":
                        history_dict["to In Progress"] = history.created
                    case "blocked (migrated)":
                        history_dict["to Blocked"] = history.created
                    case "code review":
                        history_dict["to Code Review"] = history.created

                match item.toString:
                    case "In Progress":
                        history_dict["from In Progress"] = history.created
                    case "blocked (migrated)":
                        history_dict["from Blocked"] = history.created
                    case "code review":
                        history_dict["from Code Review"] = history.created

    timming = dict()
    #calculate time for each status, 0 is default value
    if("from In Progress") in history_dict:
        InProgressTime = datetime.fromisoformat(history_dict["to In Progress"]) - datetime.fromisoformat(history_dict["from In Progress"])
        InProgressTime = str(InProgressTime.days) + " days, " + str(int(InProgressTime.seconds/3600)) + " hours"
    else:
        InProgressTime = 0
    if("from Code Review") in history_dict:
        codeReviewTime = datetime.fromisoformat(history_dict["to Code Review"]) - datetime.fromisoformat(history_dict["from Code Review"])
        codeReviewTime = str(codeReviewTime.days) + " days, " + str(int(codeReviewTime.seconds/3600)) + " hours"
    else:
        codeReviewTime = 0
    #fill dictionnary to be returned to main function
    timming["In_progress_Time"] = InProgressTime
    timming["Code_Review_Time"] = codeReviewTime

    #save data to csv file with the key as file name
    #list_history.append(history_dict)

    #uncomment to save time of status for each ticket.
    #df = pd.DataFrame(list_history)
    #df.to_csv(full_path,index=False)

    return timming
                
'''
main function used to extract data for the assignee 

in:
    assignee: name of the assignee jira user
'''
def StartExtraction(assigneName):
    
    list_issues = []

    # start time
    start_time = time.time()
    # fields to be extracted
    fields = "key,assignee,issuetype,summary,status,created,customfield_10002,parent"

    # extract issues for assignee and tickets with status is Done
    jql_req = f"assignee = '{assigneName}' AND status = Done"
    for singleIssue in jira.search_issues(jql_str=jql_req, maxResults=0,fields=fields, expand="changelog"): #fields=["assignee","key","summary","status","created",customfield_10002]
        #print(singleIssue.fields.status)
        dict_data = dict()
        if True:
            timming = fetch_history(singleIssue.changelog)
            dict_data["Assignee"]= singleIssue.fields.assignee
            dict_data["Key"] = singleIssue.key
            dict_data["Type"] = singleIssue.fields.issuetype
            dict_data["Issue Summary"] = singleIssue.fields.summary
            dict_data["Status"] = singleIssue.fields.status
            dict_data["created On"] = singleIssue.fields.created
            dict_data["In Progress Time"] = timming["In_progress_Time"]
            dict_data["Code Review Time"] = timming["Code_Review_Time"]
            if hasattr(singleIssue.fields, 'customfield_10002'):
                dict_data["Story points"] = singleIssue.fields.customfield_10002
            

            if hasattr(singleIssue.fields, 'parent'):
                dict_data["Parent"] = singleIssue.fields.parent.key 
                issue = jira.issue(dict_data["Parent"])
                dict_data["Parent Type"] = issue.fields.issuetype
                if issue is not None and hasattr(issue.fields, 'customfield_10002'):
                    dict_data["Parent Story points"] = issue.fields.customfield_10002
                #print(dict_data["Parent"])
            else:
                dict_data["Parent"] = ""        
                dict_data["Parent Story points"] = 0
         
            list_issues.append(dict_data)

    df = pd.DataFrame(list_issues)

    df.to_csv(assigneName+".csv",index=False)
    print("CSV exported")
    #get_customfields()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

