'''
DNS Resolver
COMP 375

This program should take one argument, the domain name to be resolved to an
ip. There is an optional -m flag that will have the program look for the mail
exchange assigned to the server.

Author 1: Matthew Roth mroth@sandiego.edu
Author 2: Megan Bailey meganbailey@sandiego.edu
'''

#imports
import sys
import socket
import random
from struct import *
import base64

#function given to us by Dr. Sat
def stringToNetwork(orig_string):
    """
    Converts a standard string to a string that can be sent over
    the network.

    Args:
        orig_string (string): the string to convert

    Returns:
        bytes: The network formatted string (as bytes)

    Example:
        stringToNetwork('www.sandiego.edu.edu') will return
          (3)www(8)sandiego(3)edu(0)
    """
    ls = orig_string.split('.')
    toReturn = b""
    for item in ls:
        formatString = "B"
        formatString += str(len(item))
        formatString += "s"
        toReturn += pack(formatString, len(item), item.encode())
    toReturn += pack("B", 0)
    return toReturn

#function given to us by Dr. Sat
def networkToString(response, start):
    """
    Converts a network response string into a human readable string.

    Args:
        response (string): the entire network response message
        start (int): the location within the message where the network string
            starts.

    Returns:
        string: The human readable string.

    Example:  networkToString('(3)www(8)sandiego(3)edu(0)', 0) will return
              'www.sandiego.edu'
    """

    toReturn = ""
    position = start
    length = -1
    while True:
        length = unpack("!B", response[position:position+1])[0]
        if length == 0:
            position += 1
            break

        # Handle DNS pointers (!!)
        elif (length & 1 << 7) and (length & 1 << 6):
            b2 = unpack("!B", response[position+1:position+2])[0]
            offset = 0
            for i in range(6) :
                offset += (length & 1 << i)
            for i in range(8):
                offset += (b2 & 1 << i)
            dereferenced = networkToString(response, offset)[0]
            return toReturn + dereferenced, position + 2

        formatString = str(length) + "s"
        position += 1
        toReturn += unpack(formatString, response[position:position+length])[0].decode()
        toReturn += "."
        position += length
    return toReturn[:-1], position
    
#Function given to us by Dr. Sat
def constructQuery(ID, hostname, qtype):
    """
    Constructs a DNS query message for a given hostname and ID.

    Args:
        ID (int): ID # for the message
        hostname (string): What we're asking for

    Returns: 
        string: "Packed" string containing a valid DNS query message
    """
    flags = 0 # 0 implies basic iterative query

    # one question, no answers for basic query
    num_questions = 1
    num_answers = 0
    num_auth = 0
    num_other = 0

    # "!HHHHHH" means pack 6 Half integers (i.e. 16-bit values) into a single
    # string, with data placed in network order (!)
    header = pack("!HHHHHH", ID, flags, num_questions, num_answers, num_auth,
            num_other)

    qname = stringToNetwork(hostname)
   # qtype = 1 # request A type
    remainder = pack("!HH", qtype, 1)
    query = header + qname + remainder
    return query

def sendAndReceive(hostname, destination, qtype):   
    """
    Opens a socket and sends the query through the socket

    Args:
        hostname(string): the domain name that we are looking for
        destination(string): the IP address or cname that we are sending the
        request to.
        qtype: a flag for handling mail servers

    Returns: 
        string: the bitestream of the response from the socket
    """
    #constructing a query with a random id
    random_id = random.randint(0, 65535)
    query = constructQuery(random_id, hostname, qtype)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)   # socket should timeout after 5 seconds
    try:
            sock.sendto(query,(destination, 53))
            qresp = sock.recv(4096)
            sock.close()
            return qresp
    except socket.timeout as e:
            #print("Exception: ", e)
            print("The connection has timed out. ")


def main(argv=None):
    """
    Function that handles all of the recursive calls for the program
    Args:
        hostname(string): the domain name that we are looking for
        -m: a flag to let the program know that we are searching for a mail
        server

    Returns: 
        a print to the terminal
    """
 

    
    mailFlag = False
    #checking for invalid usage
    if len(sys.argv) < 2:
        print("Usage:")
        print("python resolver.py <hostname>")
        print("or")
        print("python resolver.py -m <hostname>")
        print("The -m gets the mail exchange record")
        exit(1)
    #checking for the mail flag
    elif sys.argv[1] == "-m":
        mailFlag = True
        hostname = sys.argv[2]
    #otherwise grabbing the domain name we are looking for
    else:
        hostname = sys.argv[1]
    #opening the file of root servers
    rootfile = open("root-servers.txt", "r")
    
    #parsing the root servers file into
    root_servers = []
    for line in rootfile:
        root_servers.append(line.strip())
    rootfile.close()
    #the call that kicks of the recursion to resolve the domain name
    try:
        final_ip_address = recursiveResolver(hostname, root_servers, root_servers, mailFlag)
        print("\nRESOLVED: " + hostname + "     -->     " + str(final_ip_address) + "\n")
    except:
        print("Not a real host. Please try again.")

def recursiveResolver(hostname, servers_to_query, root_servers, mailFlag): 
    """
    Function that recursively calls itself depending on certain results of
    parseQResp
    Args:
        hostname(string): the domain name that we are looking for
        servers_to_query: the list of current servers the next recursion
        should look through
        root_servers: The list of root servers to look through if the
        servers_to_query is empty
        mailFlag: a flag to let the program know that we are searching for a mail
        server

    Returns: 
        a final string(ip address) to be returned to main to be printed
    """
 
    #getting the amount of servers to put through the for loop
    num_servers = len(servers_to_query)
    for i in range (0, num_servers):
        temp_server = servers_to_query[i]
        print("Querying: " + str(temp_server))
        #sending a different query if the mailflag is thrown
        if mailFlag == True:
            qresp = sendAndReceive(hostname, temp_server, 15)
        else:
            qresp = sendAndReceive(hostname, temp_server, 1)
        #the first recursive call to get our next_action
        new_servers_to_query, next_action = parseQResp(qresp, hostname)
        
        if next_action == 1: #base case - hostname resolved
            final_ip_address = new_servers_to_query[0] 
            return final_ip_address
       
        elif next_action == 2: #parseQresp returns ip_addresses
            return recursiveResolver(hostname, new_servers_to_query, root_servers, mailFlag)

        elif next_action == 3: #MX
            mail_exchange = new_servers_to_query[0]
            return mail_exchange

        elif next_action == 4: #CNAME
            return recursiveResolver(new_servers_to_query[0], root_servers, root_servers, mailFlag)
            
        elif next_action == 5: #SOA
            print("SOA")
            exit(1)

def parseQResp(qresp, hostName):
        """
        Function that parses the bitstreams and gets all of the essential
        information
        from the receiving packets and dictates the next action

        Args:
        qresp: the result of the query that we are parsing
        hostName(string): the domain name(or ip) that we are looking for

        Returns: 
        Either a list of new servers to query or a single ip address. Both of
        these options are returned with a next action for recursiveResolver()
        """
 
        #hardcoded types
        A_type = 0x0001
        CNAME_type = 0x0005
        SOA_type = 0x0006
        MX_type = 0x000F
        AAA_type = 0x001c

        #popping the identity, flags, and number of resource records
        ident = unpack("!H", qresp[0:2])[0]
        flags = unpack("!H", qresp[2:4])[0]
        answerRRs = unpack("!H", qresp[6:8])[0]
        authorityRRs = unpack("!H", qresp[8:10])[0]
        additionalRRs = unpack("!H", qresp[10:12])[0]
        #creating our lists to put records into and return
        answer_list = []
        authority_list = []
        additional_list = []
        
        #bitmasking the flags to get the authority flag
        authflag = flags & 0x400
        hostName = ''
        #getting the query hostname
        hostName, queryIndex = networkToString(qresp, 12)
        #getting the query type
        queryType = unpack("!H", qresp[queryIndex:queryIndex+2])[0]
        queryIndex+=2
        clas = unpack("!H", qresp[queryIndex:queryIndex+2])[0]
        queryIndex += 2
        mailFlag = False
        soaFlag = False
        #Iterating through the answer resource records and parsing their data
        #into our answer list
        for i in range (0, answerRRs):
            answer_name, queryIndex = networkToString(qresp, queryIndex)
            answer_type = unpack('!H', qresp[queryIndex:queryIndex+2])[0] 
            queryIndex += 2
            answer_class = unpack('H', qresp[queryIndex:queryIndex+2])[0]
            #checking if we get a CNAME, and returning it so that we can
            #re-run through recursiveResolver
            if answer_type == CNAME_type:
                queryIndex += 8
                primary_name, queryIndex = networkToString(qresp, queryIndex)
                answer_list.append(primary_name)
                return answer_list, 4
            else:
                queryIndex += 8
            #grabbing the IP from an A type
            if (answer_type == A_type):
                ip_address = unpack('!I', qresp[queryIndex:queryIndex+4])[0]
                answer_list.append(socket.inet_ntoa(pack('!L', ip_address)))
                queryIndex += 4
            #grabbing the answer name for the mail exchange and setting
            #our flag to true
            if (answer_type == MX_type):
                queryIndex += 2
                mail_server, queryIndex = networkToString(qresp, queryIndex)
                answer_list.append(mail_server)
                mailFlag = True

        #Iterating through the authority resource records and parsing their
        #data into our authority list
        for i in range (0, authorityRRs):
        
            queryIndex += 2
            authority_type = unpack('!H', qresp[queryIndex:queryIndex+2])[0]
            queryIndex += 2 
            authority_class = unpack('!H', qresp[queryIndex:queryIndex+2])[0] 
            queryIndex += 8
            #if the authority is an SOA, we return it immediately
            if authority_type == SOA_type:
                authority_name, queryIndex = networkToString(qresp, queryIndex)
                authority_list.append(authority_name)
                return authority_list, 5
            
            else:
                authority_name, queryIndex = networkToString(qresp, queryIndex)
                authority_list.append(authority_name)

        #Iterating through the additional resource records and parsing their
        #data into our additional list
        for i in range (0, additionalRRs):
            #handling the bane of all exceptions
            try: 
                additional_name, queryIndex = networkToString(qresp, queryIndex)
            except UnicodeDecodeError:
                queryIndex += 2
            additional_type = unpack('!H', qresp[queryIndex:queryIndex+2])[0]
            queryIndex += 2
            additional_class = unpack('!H', qresp[queryIndex:queryIndex+2])[0]
            queryIndex += 6
            additional_data_length = unpack('!H', qresp[queryIndex:queryIndex+2])[0]
            queryIndex += 2
            #Adding A types into the list
            if additional_name in authority_list and not mailFlag:
                if additional_type == A_type:
                    ip_address = unpack('!I', qresp[queryIndex:queryIndex+4])[0]
                    queryIndex += 4
                    additional_list.append(socket.inet_ntoa(pack('!L', ip_address)))
                else:
                    queryIndex += additional_data_length
            #catching stuff if there is no answer and returning it all the way
            #to the top. <.gov patch>
            elif (additional_name in answer_list) or (additional_name in authority_list):
                if additional_type == A_type:
                    ip_address = unpack('!I',qresp[queryIndex:queryIndex+4])[0]
                    queryIndex+=4
                    additional_list.append(socket.inet_ntoa(pack('!L',ip_address)))
                    return additional_list, 1
            
            else:
                queryIndex += additional_data_length
        #returning results if they didn't return in the previouse loops
        if answerRRs > 0:
            return answer_list, 1
        elif (answerRRs < 0) and (authorityRRs > 0):
            return authority_list, 2
        elif authorityRRs > 0:
            return authority_list, 2
        elif additional > 0:
            return additional_list, 2

if __name__ == "__main__":
    sys.exit(main())

