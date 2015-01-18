#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SWITCHREPORT

Usage:
    sr.py -i IPADDR -c SNMPCOMM [-p SNMPPORT] [-v SNMPVER] [-o OUTPUT]
    sr.py --version
    sr.py --help

Arguments:
    IPADDR      IP address of destination host
    SNMPCOMM    SNMP Community String to be used
    SNMPPORT    SNMP Port [default: 161]
    SNMPVER     SNMP Version [default: 2] ( 1 | 2 )
    OUTPUT      Output file type [default: console] ( console | text | html )

Options:
    -h, --help        Display help information
    --version         Show the version and exit
    -i IPADDRESS      IP address of destination 
    -c SNMPCOMMUNITY  SNMP Community String
    -p SNMPPORT       SNMP Port 
    -v SNMPVERSION    SNMP Version 
    -o OUTPUT         Output file type 
"""
from docopt import docopt
import switchreport

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

@Filename: sr.py
@Author: Ben Davies
@Description: switchReport validation and control file

'''

def main(options):

    ''' Debug options '''
    # @var integer dbgr - {1=Debug. 0=No Debug}
    dbgr = 0         

    if dbgr:
        print("DEBUG: ----------")
        print(options)
        print("DEBUG: ----------")

    print("\nSTATUS: Processing...")

    """ IP Address """
    if options["-i"]:
        ipAddress = "{i}".format(i=options["-i"])

    """ SNMP Community """    
    if options["-c"]:
        snmpCommunity = "{c}".format(c=options["-c"])

    """ SNMP Port *Optional: Default 161* """
    if options["-p"]:
        snmpPort = "{p}".format(p=options["-p"])
    else:
        print("STATUS: SNMP port not specified. Default: 161")
        snmpPort = 161

    """ SNMP Version *Optional: Default 2* """
    if options["-v"]:
        snmpVersion = "{v}".format(v=options["-v"])
    else:
        print("STATUS: SNMP version not specified. Default: Version 2")
        snmpVersion = 2

    """ Output Type """
    if options["-o"]:
        outputType = "{o}".format(o=options["-o"])
    else:
        outputType = 'console'

    ''' Validate Input '''
    valid = validateMe(ipAddress, snmpCommunity, snmpPort, snmpVersion, outputType)
    okContinue = True
    for i in valid:
        if not i == None:
            okContinue = False
            print i

    ''' Validation passed continue with program operation '''
    if okContinue:
        print("STATUS: Validation complete")
        initiateSwitchReport(ipAddress, snmpCommunity, int(snmpPort), int(snmpVersion), outputType)


''' Validate each variable '''
def validateMe(ip,co,po,ve,ot):       
    
    def __validateIP_():
        
        octets = ip.split('.')
        if len(octets) != 4:
            return 'ERROR: Please enter a valid IP address: Missing Octet'
        for i in octets:
            if int(i) < 0 or int(i) > 255:
                return 'ERROR: Please enter a valid IP address: Octet out of range'
        return None

    def __validateSNMPCommString_():
        
        if not co:
            return 'ERROR: Please enter a valid Community String'
        return None

    def __validSNMPVersion_():

        try:
            isVersionAnInt = int(ve)
            if isVersionAnInt < 1 or isVersionAnInt > 3:
                return 'ERROR: Please enter an SNMP Version between 1 and 2'
            else:
                return None
        except ValueError:
            return 'ERROR: Please enter a valid SNMP Version'

    def __validSNMPPort_():
        
        try:
            isPortAnInt = int(po)
            return None
        except ValueError:
            return 'ERROR: Please enter a valid SNMP Port'

    def __validateOutputType_():

        # Pre validation tidy up to lowercase
        lot = ot.lower()
        
        if (lot == "text" or lot == "console" or lot == "html"):
            return None
        else:
            return 'ERROR: Please enter a valid output option or omit for console output'

    resIp = __validateIP_()
    resComm = __validateSNMPCommString_()
    resVer = __validSNMPVersion_()
    resPort = __validSNMPPort_()
    resOutput = __validateOutputType_()
    return resIp, resComm, resVer, resPort, resOutput

    
''' Create instance of PortPoke ''' 
def initiateSwitchReport(i,c,p,v,o):
    sr = switchreport.switchReport(i,c,p,v,o)

if __name__ == "__main__":
    options = docopt(__doc__, version='0.1.1')
    main(options)





