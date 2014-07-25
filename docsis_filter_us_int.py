#!/usr/bin/python3
"""
    Name:       docsis_filter_us_in.py
    Version:    0.1
    Author:     JM, 18.07.14
    
    Zabbix per default can only accept one oid when performing a low level
    discovery. Then results can be filtered using a regex. However this is not
    enough. For example when only wanting upstream interfaces which are up, one
    needs 2 oids.
    
    Another issue is the naming of the graphs and items (once discovered). They
    will use the value of the requested OID (#SNMPVALUE).This script resolves
    this problem by returning a parameter list of snmp values for an interface
    (ifIndex,ifDescr, ifAlias). These parameters can the be placed in the titles
    as a placeholder ({#INT_DESCR}, {#INT_ALIAS}, {#INT_INDEX})
    
    This is POC that Zabbix can be extendend through an external script when
    using low level discovery. This script enhances the filter capabilites by
    using more than one oid. In this case only upstream interfaces which are up
    are returned.

    This script needs to be placed in the zabbix external script folder
"""
from pysnmp.entity.rfc3413.oneliner import cmdgen

def filter_table(snmp_table):
    """filters the snmpwalk results (snmp_table) to hold only upstream 
        interfaces which are in up state"""
    filter_on_ifType = ("129") # 129 = US interface
    filter_on_ifAdminState = ("1") #1:up, 2:down
    filtered_table = []
    for row in snmp_table:
        #print (row)
        #Filter credentials ifType:129 (upstream interface) and
        #ifAdminState: 1 (Up)
        if row[2] == filter_on_ifType and row[3] == filter_on_ifAdminState:
            filtered_table.append(row)

#    for row in filtered_table:
#        print (row )

    print_json(filtered_table)

def print_json(filtered_table):
    """returns table to zabbix by printing it to stdout in json"""
    #The last row of needs to be print without a comma!
    last_row = filtered_table.pop()
    json_output_last_line = (" { \"{#INT_INDEX}\":\"" + last_row[0] + "\","
                             " \"{#INT_ALIAS}\": \"" + last_row[1] + "\","
                             " \"{#INT_DESCR}\": \"" + last_row[4] + "\"}")
    print ("{")
    print ("\"data\":[")
    for row in filtered_table:
        ifIndex = row[0]
        ifAlias = row[1]
        ifDescr = row[4]
        json_output = (" { \"{#INT_INDEX}\":\"" + ifIndex + "\","
                       " \"{#INT_ALIAS}\": \"" + ifAlias + "\","
                       " \"{#INT_DESCR}\": \"" + ifDescr + "\"}, ")
        print (json_output)
    print (json_output_last_line)
    print ("]")
    print ("}")

def run():
    """
    Performs an snmpwalk using certain oids on destination host.
    The gathered data is stored in a table (varBindTable) which is organised in
    tuples of 2 (oid -> value). So all data from one interface first needs to
    extracted. This data (ifIndex, ifAlias, ifType, ifAdminState, ifDescr) is
    then entered as a table row (child) into a new table (parent)
	"""
    oid_ifIndex = (".1.3.6.1.2.1.2.2.1.1")
    oid_ifType = (".1.3.6.1.2.1.2.2.1.3")
    oid_ifAdminState = (".1.3.6.1.2.1.2.2.1.7")
    oid_ifAlias = (".1.3.6.1.2.1.31.1.1.1.18")
    oid_ifDescr = (".1.3.6.1.2.1.2.2.1.2")
    snmp_community = ("tbsro")
    dest_ip = ("10.10.10.50")
    dest_port = ("161")
    parent= []
    child = []

    #snmpwalk with oids on  dest_ip
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
        cmdgen.CommunityData(snmp_community),
        cmdgen.UdpTransportTarget((dest_ip, dest_port)),
        oid_ifIndex,
        oid_ifAlias,
        oid_ifType,
        oid_ifAdminState,
        oid_ifDescr,
    )
    #print data
    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
                )
            )
        else:
            """
            Transform the gathered snmp tuples (oid -> value) into table,  each
            row containing values per interface:
            ['7681', "b'Lab CM US A'", '129', '1', "b'Cable5/0/0-upstream0'"]
            ['7682', "b'Lab CM US B'", '129', '1', "b'Cable5/0/0-upstream1'"]
                """
            row_i = 1
            for varBindTableRow in varBindTable:
                for oid, val in varBindTableRow:

#                    print("%s = %s" % (oid.prettyPrint(), val.prettyPrint()))
#                    print("%s = %s" % (oid, val))

                    # converting to string instead of using prettyprint() causes
                    # the 'b to be lost (b'Muhen 2 VOD - US A)
                    if (row_i % 5 == 0):
                        child.append(str(val))
                        parent.append(child)
                        child = []
                        row_i+=1
                    else:
                        child.append(str(val))
                        row_i+=1
    filter_table(parent)

if __name__ == "__main__":
    run()