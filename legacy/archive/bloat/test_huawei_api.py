import logging
from huawei_api_client import HuaweiAPIClient

# Set up logging to print to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HuaweiAPIClientTest")

# API credentials and endpoint (replace with actual values if needed)
BASE_URL = "https://41.174.191.214:31127"
USERNAME = "cassava.ai"
PASSWORD = "#Pass123#"

# Network element for Bindura Hospital
BINDURA_HOSPITAL = "MSH-0112-Bindura Hospital"

if __name__ == "__main__":
    client = HuaweiAPIClient(BASE_URL, USERNAME, PASSWORD)
    logger.info("Testing API connectivity...")
    connectivity = client.test_connectivity()
    print("Connectivity Test Result:", connectivity)

    if connectivity["status"] == "success":
        logger.info("Testing authentication...")
        auth_result = client.authenticate()
        print("Authentication Result:", auth_result)

        if auth_result:
            logger.info("Sending LST UECOOPERATIONPARA command to Bindura Hospital...")
            try:
                result = client.execute_mml_command("LST UECOOPERATIONPARA;", [BINDURA_HOSPITAL])
                print("LST Command Result:", result)
            except Exception as e:
                print("Error executing LST command:", e)
        else:
            print("Authentication failed. Cannot run LST command.")
    else:
        print("API connectivity failed. Cannot proceed with tests.")
