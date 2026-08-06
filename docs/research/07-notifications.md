# Notification & action channels

**Question asked:** should we use IFTTT for email/WhatsApp delivery?
**Answer: no.** It's architecturally excluded, and there's a better native path.

---

## Why IFTTT is out

Two hard blockers:

1. **IFTTT is not one of Snowflake's five allowlisted webhook providers.** A
   `NOTIFICATION INTEGRATION ... TYPE = WEBHOOK` only accepts URLs matching **Slack**
   (`hooks.slack.com`), **Microsoft Teams**, **PagerDuty** (`events.pagerduty.com/v2/enqueue`),
   **Jira**, or **ServiceNow**. There is no generic webhook target.
2. **Reaching an arbitrary URL needs an External Access Integration**, and EAI is
   **disabled on trial accounts**.

So Snowflake cannot call `maker.ifttt.com` at all on our setup. The only way to involve IFTTT
would be an external poller service, which adds a dependency, a demo failure mode, and pulls
architecture out of Snowflake — the opposite of what the rules reward.

---

## ✅ Recommended

| Role | Channel | Why |
|---|---|---|
| **Primary** | **Slack** via Snowflake's native webhook integration | Allowlisted, zero external infra, in-platform |
| **Secondary** | **Telegram Bot API** | Free, fast setup, reaches a phone |
| **In-app** | Streamlit approval console | The actual human-in-the-loop surface |

**Slack app-approval risk is neutralised by creating your own free workspace** — you're the owner,
so there's no approval gate. Note the free plan caps 10 app installs, one webhook is permanently
bound to one channel, and incoming webhooks **cannot DM users** (that needs a bot token with
`chat:write`).

**Telegram caveat, verbatim from their docs:** *"Bots can't start conversations with users. A user
must either add them to a group or send them a message first."* You get `chat_id` only from an
inbound update. Clean workaround: a `t.me/<bot>?start=<token>` deep link. Rate limits: 1/s per
chat, 20/min per group.

---

## The critical architectural constraint

**Snowflake cannot *receive* an inbound webhook.** That means Slack interactive approve/reject
buttons are impossible — they'd need a public endpoint we can't host on a trial.

**Therefore the approval loop is:**
```
Streamlit approval console → writes decision to PENDING_ACTIONS
                           → Stream on that table
                           → Triggered Task executes
```
Everything stays inside the governed perimeter, and it uses Streamlit — one of the four
bonus-credit technologies.

---

## Reference: what each option actually costs (verified Aug 2026)

### Email
| Provider | Reality |
|---|---|
| **Snowflake native** | ✅ Works, but **only to verified Snowflake users in the same account.** Not arbitrary addresses. Fine for a demo. |
| **SendGrid** | ⭐ **Best if you need arbitrary external addresses.** The only provider needing **no DNS at all** — Single Sender Verification is one click, ~5–10 min. But the permanent free tier is gone: 100/day for **60 days**, then $19.95/mo. |
| **Resend** | ❌ **Cannot send to arbitrary recipients on free tier.** Verbatim: *"You can only send testing emails to your own email address… To send emails to other recipients, please verify a domain"* → 403. |
| **Mailgun** | ⚠️ Sandbox capped at **5 authorized recipients**. Custom domain needs SPF/DKIM/MX, 24–48h propagation. `o:testmode` messages are **not delivered but still billed**. |
| **Postmark** | ⚠️ Requires **human account approval** before sending outside your own domains ("under 24h weekdays"). Fine for a week, fatal on two days. |

### WhatsApp / SMS
| Provider | Reality |
|---|---|
| **Twilio WhatsApp Sandbox** | ✅ The only realistic WhatsApp option. **Unlimited joiners**, free-form text and media permitted inside the 24h customer-service window. ⚠️ **3-day rejoin expiry is the main live-demo hazard** — rehearse it. |
| **Twilio SMS** | ❌ **Effectively unusable on trial.** Custom message bodies are blocked — trial SMS must use pre-defined templates. Also A2P 10DLC registration required for US long codes. |
| **Meta WhatsApp Cloud API** | ⚠️ **The 1,000 free service conversations/month is GONE** (folded into per-message billing July 2025). Test number exists, no payment method needed, 250 unique customers/24h. **Business verification takes up to 14 business days** — never put it on the critical path. |

### Chat
| Provider | Reality |
|---|---|
| **Slack incoming webhooks** | ✅ Free, minutes to set up. Cannot DM users. Webhook URL is the entire credential — treat as a secret. |
| **Discord webhooks** | ✅ Free. Cannot DM users, channel posts only. URL is the entire credential, no auth header. |
| **Telegram Bot API** | ✅ Free, fastest path. Requires the one-time inbound `/start`. |

### Automation middleware (all rejected)
IFTTT, Zapier, Make.com, n8n, Pipedream — all require Snowflake to reach an arbitrary URL, which
EAI blocks on trial. Even with EAI they'd add a dependency and pull logic out of Snowflake.

---

## Implementation note

Put the webhook secret fragment in a Snowflake `SECRET` of type `GENERIC_STRING`, reference the
literal `SNOWFLAKE_WEBHOOK_SECRET` placeholder in `WEBHOOK_URL`, and wrap any user/model content in
`SANITIZE_WEBHOOK_CONTENT()` so a crafted message can't leak the secret.

Unified send call (handles email, webhooks, cloud queues):
```sql
CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
  SNOWFLAKE.NOTIFICATION.TEXT_PLAIN('Exception EX-0042 requires approval'),
  SNOWFLAKE.NOTIFICATION.EMAIL_INTEGRATION_CONFIG(
    'warrant_email_int', 'Warrant: approval required', ARRAY_CONSTRUCT('you@example.com')
  )
);
```

## ⚠️ Unverified — test in hour 1
**Whether webhook notification integrations work on trial accounts at all.** The documented trial
restriction names "external network access" (the EAI feature); webhook notification integrations
are a *different* object type and no doc confirms either way. Fallback if blocked: native email to
internal users + the Streamlit inbox, which is sufficient for the demo.
