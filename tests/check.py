import ragas
import ragas.metrics
import inspect

# small comment: list available metrics in your version
# print(f"debug: ragas path: {ragas.__file__}\n")
# print(f"debug: available metrics in ragas.metrics:\n")
# for name, obj in inspect.getmembers(ragas.metrics):
#     if inspect.isclass(obj):
#         print(f"- {name}\n")


import pandas as pd

# Path to your CSV file with predicted resolutions
TICKET_CSV = "data/evaluation/ticket_evaluation_data1.csv"

# Load the CSV
df = pd.read_csv(TICKET_CSV)

# actual resolutions
actual_resolutions = [
    "Change the device type in the device configuration to match the physical MLFB 6ES7 214-1AG40-0XB0 and firmware V4.4. This resolves the hardware configuration inconsistent startup inhibit by matching the offline project to the physical unit.",
    "Modify firewall rules to allow TCP traffic on Port 502 and verify interface parameters. Error 80C8 in MB_CLIENT indicates a connection timeout which is resolved by ensuring the network path to IP 192.168.0.50 is open.",
    "Enable the 'New Potential Group' in the TIA Portal hardware configuration for Slot 4. This resolves the parameter assignment error by correctly matching the light-colored BaseUnit installed in the distributed I/O rack.",
    "Configure the DNS server IP address and Gateway IP in the CPU hardware properties. This allows the TMAIL_C instruction to resolve the mail server address 'smtp.office365.com' and clears the 80D3 status error.",
    "Optimize the program code to reduce scan time or increase the maximum cycle time in the CPU hardware properties. The CPU enters STOP mode because the user program execution time exceeded the configured 150ms cycle monitoring time.",
    "Update the CPU hardware configuration to include the correct external IP or hostname in the certificate Subject Alternative Name (SAN) settings. Re-generate the certificate to resolve the BadCertificateUriInvalid error caused by NAT.",
    "Inspect and secure all wiring terminals between the pressure transmitter and the analog input module. The 32767 overflow and 0xA202 wire break error are resolved by restoring the 4-20 mA current loop.",
    "Verify the target position at the MC_MoveAbsolute instruction and check the software limit switch values in the axis technology object configuration. Perform an MC_Reset to clear the 16#8001 error.",
    "Set the 'Automation License Manager' service to 'Automatic' and 'Start' it in Windows Services. Ensure firewall settings allow almservice.exe communication on Port 4410 so TIA Portal can validate licenses.",
    "Verify the SIMATIC Memory Card is configured as a 'Program Card' and perform a full software rebuild. This ensures the project utilizes the 4MB load memory capacity and resolves the 'Insufficient load memory' error."
]

# Fill the 'actual_resolution' column
df['actual_resolution'] = actual_resolutions

# Save back to CSV
df.to_csv(TICKET_CSV, index=False)

print(f"✅ Updated CSV saved at {TICKET_CSV}")

