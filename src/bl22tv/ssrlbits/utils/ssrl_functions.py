# ssrlbits/utils/ssrl_functions.py
import socket
import ipaddress

def host_on_ssrl_subnet() -> bool:
    """
    Returns True if the current host is on the SSRL network/subnet.
    Adjust the subnet range to match your beamline.
    """
    try:
        # Get all IP addresses of this host
        host_ips = [ipaddress.ip_address(i[4][0]) for i in socket.getaddrinfo(socket.gethostname(), None)]
        # Define your SSRL subnet(s)
        ssrl_subnets = [
            ipaddress.ip_network("134.79.0.0/16"),      # main SLAC/SSRL campus network
            ipaddress.ip_network("192.168.22.0/23"),    # actual BL22 experimental subnet (22.0–23.255)
        ]
        # Check if any host IP is in the SSRL subnet
        return any(ip in net for ip in host_ips for net in ssrl_subnets)
    except Exception as e:
        print(f"host_on_ssrl_subnet check failed: {e}")
        return False

