import logging
from huawei_api_client import HuaweiAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HuaweiAPIClientTest")

BASE_URL = "https://41.174.191.214:31127"
USERNAME = "cassava.ai"
PASSWORD = "#Pass123#"
BINDURA_HOSPITAL = "MSH-0112-Bindura Hospital"

if __name__ == "__main__":
    client = HuaweiAPIClient(BASE_URL, USERNAME, PASSWORD)
    logger.info("Testing API connectivity...")
    connectivity = client.authenticate()
    print("Authentication Result:", connectivity)

    if connectivity:
        # Test multiple LST commands to troubleshoot
        lst_commands = [
            "LST UECOOPERATIONPARA;",
            "LST UECOOPERATIONPARA:;",
            "LST PDSCHCFG;",
            "LST CELLBASIC;"
        ]
        
        for cmd in lst_commands:
            logger.info(f"Testing command: {cmd}")
            try:
                result = client.execute_mml_command(cmd, [BINDURA_HOSPITAL])
                print(f"SUCCESS - Command '{cmd}' Result:", result)
                break  # If one works, we found the right syntax
            except Exception as e:
                print(f"FAILED - Command '{cmd}' Error:", str(e))
                continue
    else:
        print("Authentication failed. Cannot run LST command.")
