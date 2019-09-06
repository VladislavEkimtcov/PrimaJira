# jiracmd.py originally developed by Michael D Johnson
# https://github.com/Michael-D-Johnson/desdm-dash/blob/docker/app/jiracmd.py
#! /usr/bin/env python

import os
import sys
from jira.client import JIRA
import configparser
import shlog

# init logger
parser = configparser.ConfigParser()
with open('login') as configfile:
    parser.read_file(configfile)
tool_dict = parser['tool-settings']
tool_log = tool_dict['loglevel']
loglevel=shlog.__dict__[tool_log]
assert type(loglevel) == type(1)
shlog.basicConfig(level=shlog.__dict__[tool_log])

class Jira:
    def __init__(self,section):
        parser = configparser.ConfigParser()
        with open('login') as configfile:
            parser.read_file(configfile)
        jiradict=parser[section]
        jirauser=jiradict['user']
        jirapasswd=jiradict['passwd']
        jiraserver=jiradict['server']
        jira=JIRA(options={'server':jiraserver},basic_auth=(jirauser,jirapasswd))
        self.jira = jira
        self.server = jiraserver
        self.user = jirauser
        shlog.verbose('JIRA connection will use:\nServer: ' + jiraserver +
                      '\nUser: ' + jirauser + '\nPass: ' + '*'*len(jirapasswd))

    def search_for_issue(self,summary):
        jql = 'summary ~ "\\"%s\\""' % (summary)
        issue = self.jira.search_issues(jql)
        count = len(issue)
        return (issue,count)
 
    def search_for_parent(self,project,summary):
        jql = 'project = "%s" and summary ~ "%s"' % (project, summary)
        issue = self.jira.search_issues(jql)
        count = len(issue)
        return (issue,count)
   
    def get_issue(self,key):
        issue_info = self.jira.issue(key)
        return issue_info

    def create_jira_subtask(self,parent,summary,description,assignee):
        try:
            parent_issue = self.jira.issue(parent)
        except:
            warning= 'Parent issue %s does not exist!' % parent
            print(warning)
            sys.exit()

        subtask_dict = {'project':{'key':parent_issue.fields.project.key},
		    'summary': summary,
            # change the issue type if needed
		    'issuetype':{'name':'Story'},
		    'description': description,
		    'customfield_10536': parent_issue.key, # this is the epic link
		    'assignee':{'name': assignee}
		    }
        subtask = self.jira.create_issue(fields=subtask_dict)
        return subtask.key	

    def create_jira_ticket(self,project,summary,description,assignee):
        ticket_dict = {'project':{'key':project},
		    'customfield_10537': summary, # THIS MIGHT (READ: DOES 100%) CHANGE IN DIFFERENT JIRA INSTANCES
            'summary': summary,
		    'issuetype':{'name':'Epic'},
		    'description': description,
		    'assignee':{'name': assignee}
		    }	
        ticket = self.jira.create_issue(fields=ticket_dict)
        return ticket.key	

    def add_jira_comment(self,issue,comment):
        self.jira.add_comment(issue,comment)

