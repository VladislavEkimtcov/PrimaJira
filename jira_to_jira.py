import configparser
import shlog
from jiracmd import Jira
import main as m


def jira_status_translator(source_status):
    if source_status in ['To Do', 'Open', 'System Change Control', 'Reopened', 'Backlog']:
        return 'To Do'
    if source_status in ['In Progress', 'Blocked', 'Waiting on User', 'Sleeping']:
        return 'In Progress'
    if source_status in ['Closed']:
        return 'Done'


# read config and get primavera login info
parser = configparser.ConfigParser()
with open('login') as configfile:
    parser.read_file(configfile)
primadict=parser['primavera-section']
primauser=primadict['user']
primapasswd=primadict['passwd']
primaserver=primadict['server']

# read jira info for verbose output
jiradict = parser['jira-section']
jiraproject = jiradict['project']
shlog.verbose('Primavera connection will use:\nServer: ' + primaserver +
              '\nUser: ' + primauser + '\nPass: ' + '*' * len(primapasswd))

# init source and target jiras
con = Jira('jira-section')
con_target = Jira('jira-target')


# read tool config
tool_dict = parser['tool-settings']
tool_log = tool_dict['loglevel']
loglevel=shlog.__dict__[tool_log]
assert type(loglevel) == type(1)
shlog.basicConfig(level=shlog.__dict__[tool_log])
tool_fixer = tool_dict['fix']
mppfile = tool_dict['mppfile']

if __name__ == '__main__':
    # the new world order
    import projectAPI as p
    c = p.ProjectInterface(mppfile)


    # get tasks
    tasks = c.fetch_tasks()
    for t in tasks:
        # sync ones with parallel tickets
        if t.Text1 != '' and t.Text2 != '':
            shlog.verbose("______________________")
            shlog.verbose("Processing task: " + t.Name)
            # quick remap to make code transfer easier
            ncsa_jira_id = t.Text2
            lsst_jira_id = t.Text1
            issue = con.get_issue(ncsa_jira_id)
            if issue:
                status = str(issue.fields.status)
                shlog.verbose('Processing ticket ' + ncsa_jira_id + ' with status ' + status)
                lsst_status = jira_status_translator(status)
                con_target.post_status(lsst_jira_id,lsst_status)
            else:
                # the issue is not present in JIRA
                shlog.verbose(ncsa_jira_id + " doesn't exist!")
                continue

# concerns: wontfix, LSST-2144//DM-18822