# 2. Pick the 5–6 domains that define the business

A warehouse can have thousands of tables. A business has maybe six things it fundamentally does. Start from the
business, not the catalog.

## Method

1. **One sentence:** "We make money by ___ from ___ when ___."
2. **Walk the value chain** from first touch to revenue to churn. Each hop is an event or entity.
3. **Group the hops into 5–6 domains.** Each domain has one *entity* (a noun) with one *unique id*.
4. **List the questions the business keeps asking.** Mark which domains each question crosses. Those crossings are the
   relationships you must validate first.

## Examples

| business | domains |
|---|---|
| Subscription SaaS | customer/account · subscription · billing/invoice · product usage events · support · marketing/acquisition |
| Marketplace | buyer · seller · listing · order/transaction · payment/payout · trust & safety |
| Retail / e-commerce | customer · product/catalog · order · inventory · fulfilment · marketing |
| Fintech | customer/KYC · account · transaction · card · risk/fraud · support |

## Output

Fill in [`DOMAINS.md`](../schemakit/templates/DOMAINS.template.md) (created by `schemakit init`).
Then find, per domain, the **anchor table**: the table whose grain *is* the entity (`customers`, `orders`, `subscriptions`).
Anchor tables get profiled first. Child/event tables come after.

## Sanity checks

- If you can't name the unique id of a domain's entity, you don't understand the domain yet.
- If two domains share an entity (customer appears in four), pick one as the **spine** (usually customer/account).
- 5–6 is a guide. More than ~8 means you're splitting too finely; fewer than 4 means you're hiding structure.
