# Cost

Estimated monthly cost of the Azure platform, EU region (Sweden Central /
Germany West Central), at portfolio/demo volume. Figures are approximate and
in EUR.

## Recurring, cannot scale to zero

| Resource | SKU | ~ EUR / month running 24x7 |
|---|---|---|
| PostgreSQL Flexible Server | B_Standard_B1ms, 32 GB | ~15 |
| Container Registry | Basic | ~4 |
| **Subtotal (always-on)** | | **~19** |

## Scale-to-zero or usage-based (≈ 0 at demo volume)

| Resource | Notes |
|---|---|
| Container Apps (api / worker / ui) | Consumption plan, scale to zero; generous free monthly grant |
| Container Apps environment | No base charge |
| Log Analytics + App Insights | Free grant covers low-volume ingestion |
| Storage account (ADLS Gen2) | Cents |
| Key Vault (standard) | Per-operation, cents |
| Azure AI Search | Free tier, EUR 0 |
| Service Bus | Basic, per-operation pennies |
| Azure OpenAI | Pay per token; a resolution is ~EUR 0.005 |

## Controlling spend

The always-on cost is dominated by Postgres. The whole platform is
Terraform-managed, so `make infra-down` destroys everything and `make
infra-up` recreates it identically. Run the stack only while developing or
demoing; tear it down otherwise. Actual spend on the free credit stays in
single-digit euros.

## The scale-up path

Postgres B1ms is the cheapest burstable tier. Real production would move to a
General Purpose tier with high availability and a private endpoint; those cost
more and are deliberately out of scope for a solo demo.
