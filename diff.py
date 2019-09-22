# diff tool to compare primavera vs jira
# all findings are provided with possible resolutions
import main as m
import shlog
import configparser
import jira_utils as ju
from jiracmd import Jira


# read config and get primavera login info
parser = configparser.ConfigParser()
with open('login') as configfile:
    parser.read_file(configfile)
primadict=parser['primavera-section']
primauser=primadict['user']
primapasswd=primadict['passwd']
primaserver=primadict['server']
# read jira info for verbose output
jiradict=parser['jira-section']
jiraproject = jiradict['project']
# read tool config
tool_dict = parser['tool-settings']
tool_log = tool_dict['loglevel']
loglevel=shlog.__dict__[tool_log]
assert type(loglevel) == type(1)
shlog.basicConfig(level=shlog.__dict__[tool_log])
shlog.verbose('Primavera connection will use:\nServer: ' + primaserver +
              '\nUser: ' + primauser + '\nPass: ' + '*'*len(primapasswd))# init jira connection
# init jira stuff
jcon = Jira('jira-section')
con = ju.get_con('jira-section')

shlog.verbose('Getting ticket IDs and activities due for export')
tickets = m.get_activity_tickets(primaserver, primauser, primapasswd)
step_tickets = m.get_step_tickets(primaserver, primauser, primapasswd)
synched = m.get_synched_activities(primaserver, primauser, primapasswd)
activities, steps = m.get_steps_activities(synched, primaserver, primauser, primapasswd)

# find activities not yet imported
shlog.normal('\n---CHECKING FOR ACTIVITIES NOT YET IMPORTED---')
for act in activities:
    if act not in tickets.keys():
        shlog.normal('Activity #' + str(act) + ' (' + activities[act]['Name'] + ')  is marked for export, but does '
                     'not have an assigned JIRA ID yet. main.py can create a ticket automatically')

# find steps without ids
shlog.normal('\n---CHECKING FOR STEPS NOT YET IMPORTED---')
for step in steps:
    if step not in step_tickets.keys():
        shlog.normal('Step ID #' + str(step) + ' (' + steps[step]['Name'] + ') belongs to an exportable activity #' +
                     str(steps[step]['ActivityObjectId']) +
                     ' (' + activities[int(steps[step]['ActivityObjectId'])]['Name'] + '), but does not have a JIRA ID'
                     ' yet. main.py can create a ticket automatically')

shlog.normal('\n---CHECKING FOR ACTIVITIES IMPORTED IMPROPERLY---')
for act in activities:
    issues, count = con.search_for_issue(activities[act]['Name'])
    # find steps with IDs without a corresponding ticket (different names?)
    if count == 0:
        shlog.normal('Could not find Activity "' + activities[act]['Name'] + '" in JIRA')
        # find unsyched tickets
        if act not in tickets.keys():
            shlog.normal('"' + activities[act]['Name'] + '" does not yet have an associated JIRA ID. '
                                                         'main.py can create a ticket automatically')
        else:
            shlog.normal('"' + activities[act]['Name'] + '" already has a JIRA ID associated with it (' + tickets[act] +')')
            # what will this do
            try:
                # if this suceeds, then the name needs to be synched manually
                jira_tix = con.get_issue(tickets[act])
                shlog.normal('Ticket ' + str(jira_tix) +  " already exists. Please check if it's technically the same "
                                                          "ticket and make the correction manually")
            except:
                # if this fails or returns nothing, then the issue needs to be created
                shlog.normal('The specified ticket ' + tickets[act] + ' does not exist. Please fix the JIRA ID record '
                                                                      'and/or have the main program create the ticket')

    if count == 1:
        # find cases where there is a properly named ticket, but no ticket entry
        if not(tickets.get(act, False)):
            shlog.normal('Ticket with name ' + activities[act]['Name'] + ' exists, but Activity ID #' + str(act) + ' does not '
                         'have a ticket record. Please add the record manually, or check if activities with '
                         'duplicate names exist')
        # find ticket records mismatches
        if str(tickets.get(act, issues[0].key)) != str(issues[0].key):
            shlog.normal('Activity ' + activities[act]['Name'] + ' has ticket listed as ' + tickets.get(act, False) +
                         ' in Primavera but JIRA returned ticket ' + issues[0].key + '. Please update the record in '
                                                                                     'Primavera if necessary.')
    if count > 1:
        shlog.normal('More than one ticket exist with name ' + activities[act]['Name'] + ':')
        for issue in issues:
            shlog.normal(issue.key)
        shlog.normal('Please resolve duplicate tickets')

shlog.normal('\n---CHECKING FOR STEPS IMPORTED IMPROPERLY---')
for step in steps:
    issues, count = con.search_for_issue(steps[step]['Name'])
    # find steps with IDs without a corresponding ticket (different names?)
    if count == 0:
        shlog.normal('Could not find Step "' + steps[step]['Name'] + '" in JIRA')
        # find unsyched tickets
        if step not in step_tickets.keys():
            shlog.normal('"' + steps[step]['Name'] + '" does not yet have an associated JIRA ID. '
                                                         'main.py can create a ticket automatically')
        else:
            shlog.normal('"' + steps[step]['Name'] + '" already has a JIRA ID associated with it (' + step_tickets[step] +')')
            # what will this do
            try:
                # if this suceeds, then the name needs to be synched manually
                jira_tix = con.get_issue(step_tickets[step])
                shlog.normal('Ticket ' + str(jira_tix) +  " already exists. Please check if it's technically the same "
                                                          "ticket and make the correction manually")
            except:
                # if this fails or returns nothing, then the issue needs to be created
                shlog.normal('The specified ticket ' + step_tickets[step] + ' does not exist. Please fix the JIRA ID record '
                                                                      'and/or have the main program create the ticket')

    if count == 1:
        # find cases where there is a properly named ticket, but no ticket entry
        if not(step_tickets.get(step, False)):
            shlog.normal('Ticket with name ' + steps[step]['Name'] + ' exists, but Step ID #' + str(step) + ' does not '
                         'have a ticket record. Please add the record manually, or check if steps with '
                         'duplicate names exist')
        # find ticket records mismatches
        if str(step_tickets.get(step, issues[0].key)) != str(issues[0].key):
            shlog.normal('Step ' + steps[step]['Name'] + ' has ticket listed as ' + step_tickets.get(step, False) +
                         ' in Primavera but JIRA returned ticket ' + issues[0].key + '. Please update the record in '
                                                                                     'Primavera if necessary.')
    if count > 1:
        shlog.normal('More than one ticket exist with name ' + steps[step]['Name'] + ':')
        for issue in issues:
            shlog.normal(issue.key)
        shlog.normal('Please resolve duplicate tickets')

    # check story pts mismatch
    if int(issues[0].fields.customfield_10532) != int(steps[step]['Weight']):
        shlog.normal('Step ' + steps[step]['Name'] + ' reported ' + str(issues[0].fields.customfield_10532) +
                     ' story points in JIRA, but ' + str(steps[step]['Weight']) + ' weight in Primavera')