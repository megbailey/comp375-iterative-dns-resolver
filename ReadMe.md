# Iterative DNS Resolver
An iterative DNS resolver program that mimics the command line tool ```dig```.

DNS is an acroymn for Domain Name System which is the process of mapping a canonical name such as 'github.com' to an IP, an address your computer understands. Your computer handles domain name resolution behind the scenes every time you type in 'google.com' into your web browser - this program is meant to replicate that process.

From ICANN (Internet Corporation for Assigned Name), this is a map of the locations of 13 DNS root servers.

![Location of 13 DNS root servers](/images/dns-root-servers.png)

This program begins the domain name resolution process by querying the 13 root DNS servers for responses. Then, it slowly works down the DNS hiearchy until it finds an authorative response for the canonical name. DNS is the backbone of the internet. It is much easier to remember a canonical name than a bunch of IP addresses - Thanks DNS!

![DNS Hierarchy](/images/dns-hierarchy.png)

## Steps to run
Find the IP of a canonical name: 

```python resolver.py <CANONICAL-NAME>```

Find the IP of a canonical name's mail server:

```python resolver.py -m <CANONICAL-NAME>```

### Check my work! 
Enter in a trusted canonical name such as 'google.com' or 'sandiego.edu' and copy the response of the program. Then, enter in that IP into the search bar of your web browser.
