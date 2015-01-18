#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
SwitchReport is copyright (c) 2014-2015, Ben Davies. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

@Filename: switchreport.py
@Author: Ben Davies
@Description: switchReport main class

'''

import os
import time
import datetime
from pysnmp.entity.rfc3413.oneliner import cmdgen

''' Debug Options '''
# from pysnmp import debug
# debug.setLogger(debug.Debug('msgproc'))
# debug options: all, io, msgproc, secmod, mibbuild

''' switchReport class '''
class switchReport(object):

    def __init__(self, ipAddress, snmpCommunityString, snmpPort, snmpVersion, outputType):

        ''' Debug options '''
        # @var integer dbg - {1=Debug. 0=No Debug}
        self.dbg = 0            

        ''' Initialising Constructor with required variables '''
        self.ipAddress = ipAddress
        self.snmpCommunityString = snmpCommunityString
        self.snmpVersion = snmpVersion
        self.snmpPort = snmpPort
        self.outputType = outputType

        ''' Debug: Console Print Input '''
        if self.dbg:
            self.printInput()

        ''' Function Calls to run program '''
        try:
            print("STATUS: Performing SNMP queries")
            systemName = self.getSNMPSysName()
            systemUpTime, sysUpTimeString = self.getSNMPSystemUpTime()
            self.getSNMPinterfacePortLastUse(systemUpTime,systemName,sysUpTimeString)
        except IOError as e:
            print "ERROR: IO Error"
        except ValueError:
            print "ERROR: Value Error"
        except IndexError:
            self.debug("Index Error. No data returned from SNMP Query")
            checkRes = self.hostCheckLinuxOS()
            print checkRes

    
    ''' Linux Ping check '''
    def hostCheckLinuxOS(self):

        print "Pinging..."
        if os.system('ping -c 1 %s' % self.ipAddress) == 0:
            return """
            ERROR: Ping test to %(ipA)s successful.

            Are SNMP Settings correct?
            - SNMP Community String: %(sCS)s
            - SNMP Version: %(sV)s
            """ % {'ipA': self.ipAddress, 'sCS': self.snmpCommunityString, 'sV': self.snmpVersion}       

        else:
            return "ERROR: Ping test to %s" % self.ipAddress + " failed, Host unreachable."


    ''' Debug function to confirm input'''
    def printInput(self):

        print('DEBUG: IP Address: %s' % self.ipAddress)
        print('DEBUG: SNMP Community: %s' % self.snmpCommunityString)
        print('DEBUG: SNMP Version: %s' % self.snmpVersion)
        print('DEBUG: SNMP Port: %s' % self.snmpPort)
        print('DEBUG: Output Type: %s' % self.outputType)

    ''' Obtain Switch System Name '''
    def getSNMPSysName(self):

        MIB = 'SNMPv2-MIB'
        sysNameVars = self.performSNMPQuery(MIB,'sysName')
        self.debug(sysNameVars)
        return sysNameVars[0][0][1]


    ''' Obtain Switch System Up Time '''   
    def getSNMPSystemUpTime(self):

        cmdGen = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
            cmdgen.CommunityData(self.snmpCommunityString),
            cmdgen.UdpTransportTarget((self.ipAddress, self.snmpPort)),
            cmdgen.MibVariable('.1.3.6.1.2.1.1.3.0')
        )
        self.debug(varBinds)
        sUT = float(varBinds[0][1])
        sysUpTimeReadable = self.convertTimeTickToReadable(sUT)
        self.debug("System Up Time: %s" % sysUpTimeReadable)
        return varBinds, sysUpTimeReadable


    ''' Obtain interface port uptime '''    
    def getSNMPinterfacePortLastUse(self, SysUpTime, systemName, sysUpTimeString):
   
        MIB = 'IF-MIB'
        ifIndexRes = self.performSNMPQuery(MIB,'ifIndex')
        ifDescrRes = self.performSNMPQuery(MIB,'ifDescr')
        ifOperStatusRes = self.performSNMPQuery(MIB,'ifOperStatus')
        ifLastChangeRes = self.performSNMPQuery(MIB,'ifLastChange')

        SwitchIP = "\nDevice IP Address: %s " % self.ipAddress + "\n"
        SwitchName = "Device Name: %s " %systemName + "\n"
        SwitchUpTime = "Device Up Time: %s " %sysUpTimeString + "\n"
        ReportGen = "Report Generated: %s" % time.ctime() + "\n"
        # Print network switch details and time
        DOC_HEADER = "SWITCHREPORT"
        DOC_DEVICEINFO =  SwitchIP + SwitchName + SwitchUpTime + ReportGen
        DOC_COLUMNHEADER = "Interface   |   Status  |   Status Duration"
        
        ''' Text file report selected'''
        if(self.outputType == "text"):

            print("STATUS: Compiling text based report")
            self.checkDirectory("text")
            fileTime = self.filenameTimeStamp()

            FILENAME = "SwitchReport_%s" % fileTime + "_%s" % self.ipAddress + "_%s" % systemName + ".txt"  
            PATH = "reports/text/"
            FULLPATH = os.path.join(PATH, FILENAME)           

            try:
                f = open(FULLPATH,"w")
                f.write(DOC_HEADER)
                f.write("\n")
                f.write(DOC_DEVICEINFO)
                f.write("\n")                
                f.write(DOC_COLUMNHEADER)
                
                for i in range(len(ifIndexRes)): 
                    # ifOperStatusRes
                    res = self.getPortStatus(int(ifOperStatusRes[i][0][1]))
                    # Works out ports uptime                 
                    portTimeSpan = float(SysUpTime[0][1]) - float(ifLastChangeRes[i][0][1])
                    pUT = self.convertTimeTickToReadable(portTimeSpan)
                    # Print port details to console
                    f.write("\n%s %s %s" %(ifDescrRes[i][0][1],res,pUT))
                print("STATUS: Report generated:\nSTATUS: %s" % FULLPATH)        
                f.close()
            except IOError:
                print "ERROR: Unable to access and create report path and filename"

        elif(self.outputType == "html"):

            print("STATUS: Compiling html based report")
            self.checkDirectory("html")
            fileTime = self.filenameTimeStamp()

            FILENAME = "SwitchReport_%s" % fileTime + "_%s" % self.ipAddress + "_%s" % systemName + ".html"  
            PATH = "reports/html/"
            FULLPATH = os.path.join(PATH, FILENAME)           

            HTML_TEMPLATE_TOP =  """
            <!DOCTYPE html>
            <html>
            <head>
            <title>SWITCHREPORT :: Take control of the edge</title>
            <meta charset="UTF-8">
             <style>
              table { border-collapse: collapse; border: solid thick; }
              colgroup, tbody { border: solid medium; }
              td { border: solid thin; height: 1.4em; text-align: center; padding-left: 5px; padding-right: 5px;}
              tr.rowred {background-color:#FF6347;}
             </style>
            </head>
            <body>
            <section>
            <h1>SwitchReport :: Take control of the edge</h1>
            <p>Scan complete and report generated below<br />
                """

            SwitchIP = "Switch IP Address: %s " % self.ipAddress + "<br />"
            SwitchName = "Switch Name: %s " %systemName + "<br />"
            SwitchUpTime = "Switch Up Time: %s " %sysUpTimeString + "<br />"
            ReportGen = "Report Generated: %s" % time.ctime() + "</p>"
            HTML_TEMPLATE_BLURB_TOP = SwitchIP + SwitchName + SwitchUpTime+ ReportGen
              
            HTML_TEMPLATE_BLURB_BTM = """
            </section>
            <section>
             <table>
             <thead>
              <tr>
               <th> Interface
               <th> Status
               <th> Duration
             <tbody>
             """
                 
            HTML_TEMPLATE_BTM = """
            </section>
            </table> 
            </body>
            </html>"""

            try:
                f = open(FULLPATH,"w")
                f.write(HTML_TEMPLATE_TOP)
                f.write(HTML_TEMPLATE_BLURB_TOP)
                f.write(HTML_TEMPLATE_BLURB_BTM)
                for i in range(len(ifIndexRes)): 
                    # ifOperStatusRes
                    res = self.getPortStatus(int(ifOperStatusRes[i][0][1]))
                    # Works out ports uptime                 
                    portTimeSpan = float(SysUpTime[0][1]) - float(ifLastChangeRes[i][0][1])
                    pUT = self.convertTimeTickToReadable(portTimeSpan)
                    # Compile string to write to file 
                    '''
                    #Table Row Arrangement:
                    #   <td> Interface Value
                    #   <td> Status Value
                    #   <td> Duration Value
                    '''
                    if res == 'Down':
                        String = "<tr><td> %s " % str(ifDescrRes[i][0][1]) + "<td> %s " % res + "<td> %s " % pUT
                    else:
                        String = "<tr class='rowred'><td> %s " % str(ifDescrRes[i][0][1]) + "<td> %s " % res + "<td> %s " % pUT
                    # Write current line to file
                    f.write(String)
                
                f.close()
                print("STATUS: Report generated:\nSTATUS: %s" % FULLPATH)
            except IOError:
                print "ERROR: Unable to access and create report path and filename"
            

        # Can only be console
        else:

            print("STATUS: Compiling console based report\n")
            print DOC_HEADER
            print DOC_DEVICEINFO
            print DOC_COLUMNHEADER
            
            for i in range(len(ifIndexRes)): 
                # ifOperStatusRes
                res = self.getPortStatus(int(ifOperStatusRes[i][0][1]))
                # Works out ports uptime                 
                portTimeSpan = float(SysUpTime[0][1]) - float(ifLastChangeRes[i][0][1])
                pUT = self.convertTimeTickToReadable(portTimeSpan)
                # Print port details to console
                print '%s %s %s' %(ifDescrRes[i][0][1],res,pUT)
                

    ''' Generic function to complete SNMP query with supplied OID '''  
    def performSNMPQuery(self, mib, objname):
    
            cmdGen = cmdgen.CommandGenerator()
            errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
                cmdgen.CommunityData(self.snmpCommunityString, mpModel=0),
                cmdgen.UdpTransportTarget((self.ipAddress, self.snmpPort)),
                cmdgen.MibVariable(mib, objname),
                lookupValues=True
            )
            if errorIndication:
                print("ERROR: %s " % errorIndication)
            else:
                if errorStatus:
                    print('ERROR: %s at %s' % (
                        errorStatus.prettyPrint(),
                        errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
                        )
                    )      
            return varBindTable


    ''' Obtains status per port '''                   
    def getPortStatus(self, portOperationalStatus):

        pOS = int(portOperationalStatus)
        if pOS == 1:
            res = 'Up'
        elif pOS == 2:
            res = 'Down'
        else:
            res = 'Unknown'
        return res


    ''' Converts Time Tick into Readable String '''
    def convertTimeTickToReadable(self, timeTick):
        
        # Days 8640000
        d, m = divmod(timeTick, 8640000)
        days = '%d days' % d,
        # Hours 360000
        d, m = divmod(m, 360000)
        hours = '%d hours' % d,
        d, m = divmod(m, 6000)
        # Minutes 6000
        minutes = '%d minutes' % d,
        concatString = days + hours + minutes   
        joinedString = ' '.join(concatString)  
        return joinedString


    ''' Check if reports directory exists '''
    def checkDirectory(self, directory):

        fullPath = "reports/" + "%s" % directory
        if not os.path.exists(fullPath):
            try:
                os.makedirs(fullPath)
            except OSError:
                print "ERROR: Unable to create directory. Check Permissions."


    ''' Create human readable timestamp to be used in the reports filename ''' 
    def filenameTimeStamp(self):

        timeSeconds = time.time()
        timeReadableString = datetime.datetime.fromtimestamp(timeSeconds).strftime('%y%m%d%H%M')
        return timeReadableString
        

    ''' Simple Debug Function to print errors if needed '''
    def debug(self, msg):
        if self.dbg:        
            print("DEBUG: %s" % msg) 
    
