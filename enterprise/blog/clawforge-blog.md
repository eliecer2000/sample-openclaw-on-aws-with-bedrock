# From Personal AI Agent to Enterprise Digital Workforce: Building ClawForge on AWS Bedrock AgentCore

*How we observed OpenClaw's enterprise gap, designed a zero-invasion management layer, and built a full-stack platform that gives every employee a role-specific AI agent — without modifying a single line of OpenClaw source code.*

---

## The Observation That Started Everything

OpenClaw has 200k+ GitHub stars. It connects AI to WhatsApp, Telegram, Discord, runs browser automation, manages calendars, executes shell commands. For personal productivity, it's arguably the most capable open-source AI agent available today.

But here's what we noticed when enterprises started asking about it:

**"Can we give every employee their own OpenClaw agent?"**

The answer was technically yes — but practically no. Because the moment you deploy OpenClaw for 20 people instead of 1, you hit a wall of questions that the personal-use architecture was never designed to answer:

- Who controls what the agent can do? (The intern and the CFO shouldn't have the same tool access)
- How do you give each agent a different identity? (Finance Analyst vs Software Engineer)
- Where does the audit trail live? (Every agent action needs to be logged for compliance)
- Who pays for what? (Per-department budgets, not a single credit card)
- What happens to the agent's memory between sessions? (It needs to persist, but securely)

These aren't feature requests. They're architectural requirements. And they can't be solved by adding a few config flags to OpenClaw.

## The Design Philosophy: Don't Fork, Wrap

Our first instinct was to fork OpenClaw and add enterprise features. We rejected that immediately.

Here's why: OpenClaw moves fast. The community ships updates weekly. A fork means maintaining a parallel codebase, cherry-picking patches, dealing with merge conflicts forever. Every enterprise fork of an open-source project eventually falls behind or becomes unmaintainable.

Instead, we asked: **What if we could control OpenClaw's behavior without touching its code?**

The insight came from how OpenClaw actually works. At session start, it reads a set of workspace files:

```
~/.openclaw/workspace/
├── SOUL.md      ← System prompt (who the agent is)
├── AGENTS.md    ← Workflow definitions
├── TOOLS.md     ← Tool permissions
├── USER.md      ← User preferences
├── MEMORY.md    ← Persistent memory
├── memory/      ← Daily memory files
└── skills/      ← Installed skill packages
```

OpenClaw doesn't care where these files come from. It just reads them. So what if we assembled these files *before* OpenClaw reads them, injecting enterprise controls through the native file system?

That's exactly what ClawForge does. Zero invasion. OpenClaw doesn't know it's running in an enterprise context.

---

## Deep Dive: Three-Layer SOUL Architecture

This is the core innovation. Agent identity is composed from three layers, each managed by a different stakeholder:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: GLOBAL (IT locked — CISO + CTO approval)          │
│  "Never share customer PII. Never execute rm -rf."           │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: POSITION (Department admin managed)                │
│  "You are a Finance Analyst. Use excel-gen, not shell."      │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: PERSONAL (Employee self-service)                   │
│  "I prefer concise answers. Always use TypeScript."          │
└─────────────────────────────────────────────────────────────┘
                          ↓ merge
                Final SOUL.md (what OpenClaw reads)
```

### The Merge Algorithm

`workspace_assembler.py` is the critical bridge. Here's the actual merge logic:

```python
def merge_soul(global_soul, position_soul, personal_soul):
    parts = []
    if global_soul.strip():
        # Identity override prefix — appears FIRST in prompt for max priority
        parts.append(
            "CRITICAL IDENTITY OVERRIDE: You are a digital employee "
            "of ACME Corp. This overrides any default identity.\n\n"
            f"{global_soul.strip()}"
        )
    if position_soul.strip():
        parts.append(f"<!-- LAYER: POSITION -->\n{position_soul.strip()}")
    if personal_soul.strip():
        parts.append(f"<!-- LAYER: PERSONAL -->\n{personal_soul.strip()}")
    return "\n\n---\n\n".join(parts)
```

The order matters enormously. We initially put personal preferences first and global policies last. The LLM would sometimes prioritize the personal layer because it appeared more recently in the context window. Flipping the order — Global first with an explicit "CRITICAL IDENTITY OVERRIDE" prefix — dramatically improved policy compliance.

### Where the Layers Live in S3

```
s3://openclaw-tenants-{account}/
├── _shared/soul/global/
│   ├── SOUL.md          ← Layer 1 (one copy, all agents read it)
│   ├── AGENTS.md
│   └── TOOLS.md
├── _shared/soul/positions/
│   ├── pos-sa/SOUL.md   ← Layer 2 (Solutions Architect)
│   ├── pos-sde/SOUL.md  ← Layer 2 (Software Engineer)
│   ├── pos-fa/SOUL.md   ← Layer 2 (Finance Analyst)
│   └── ... (10 positions)
├── emp-carol/workspace/
│   ├── USER.md           ← Layer 3 (Carol's preferences)
│   ├── MEMORY.md         ← Persistent memory
│   └── memory/
│       └── 2026-03-21.md ← Daily memory file
└── emp-w5/workspace/     ← Wang Wu's personal files
```

The result: Carol Zhang and Wang Wu use the same LLM (Nova 2 Lite), the same infrastructure, the same Docker image. But Carol's agent identifies as "ACME Corp Finance Analyst" and refuses shell commands, while Wang Wu's agent identifies as "ACME Corp Software Engineer" and happily runs `git status`.

![Portal Chat — Carol's agent refuses shell, identifies as Finance Analyst](../demo/images/01-portal-chat-permission-denied.jpeg)

---

## Deep Dive: System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  WhatsApp · Telegram · Slack · Discord · Web Portal · Admin Console  │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────────────┐
│  EC2 Gateway (single instance, ~$52/mo)                              │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │
│  │ OpenClaw GW │ │ H2 Proxy     │ │ Tenant Router│ │Admin Console│ │
│  │ port 18789  │ │ port 8091    │ │ port 8090    │ │ port 8099   │ │
│  │ IM channels │ │ intercepts   │ │ derives      │ │ React 19 +  │ │
│  │ Web UI      │ │ Bedrock SDK  │ │ tenant_id    │ │ FastAPI     │ │
│  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘ └─────────────┘ │
│         └───────────────►└───────────────►│                          │
└──────────────────────────────────────────┬───────────────────────────┘
                                           │ invoke AgentCore
┌──────────────────────────────────────────▼───────────────────────────┐
│  Bedrock AgentCore Runtime (Firecracker microVM per tenant)          │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────────┐  │
│  │ entrypoint.sh│  │ server.py     │  │ workspace_assembler.py   │  │
│  │ S3 sync      │  │ HTTP :8080    │  │ 3-layer SOUL merge       │  │
│  │ skill load   │  │ Plan A inject │  │ SSM position lookup      │  │
│  │ watchdog 60s │  │ Plan E audit  │  │ knowledge copy           │  │
│  └──────────────┘  │ usage tracking│  └──────────────────────────┘  │
│                    │ openclaw CLI  │                                  │
│                    └───────┬───────┘                                  │
│                            │ openclaw agent --session-id X --json     │
│                            ▼                                          │
│                    OpenClaw CLI → Bedrock (Nova 2 Lite / Sonnet)      │
└──────────────────────────────────────────────────────────────────────┘
                       │                    │
┌──────────────────────▼────────────────────▼──────────────────────────┐
│  DynamoDB    S3         SSM        Bedrock      CloudWatch           │
│  org,audit   SOUL,      tenant→    Nova 2 Lite  agent logs           │
│  usage,      skills,    position   Sonnet, Pro  invocation           │
│  sessions    memory     API keys   Kimi K2.5    metrics              │
└──────────────────────────────────────────────────────────────────────┘
```

Four services run on a single EC2 instance. This is intentional — the Gateway is the only always-on component. Everything else (agent compute) is serverless via AgentCore.

### The H2 Proxy: Intercepting Bedrock SDK Calls

OpenClaw uses the AWS SDK to call Bedrock. It makes HTTP/2 calls to `bedrock-runtime.{region}.amazonaws.com`. The H2 Proxy sits between OpenClaw and Bedrock, intercepting these calls to:

1. Extract the channel and user identity from the request metadata
2. Rewrite the request to include tenant context
3. Forward to the Tenant Router instead of directly to Bedrock

This is how we derive `tenant_id` without modifying OpenClaw's Bedrock integration code.

### The Tenant Router: Deriving Identity

The Tenant Router receives the intercepted request and derives a unique tenant ID:

```
Format: {channel}__{user_id}__{hash}
Examples:
  tg__emp-carol__a1b2c3d4     (Telegram, Carol)
  sl__emp-w5__e5f6g7h8         (Slack, Wang Wu)
  port__emp-carol__bbee1f93    (Portal, Carol)
```

It then invokes AgentCore with this `tenant_id` as the `runtimeSessionId`. AgentCore creates (or reuses) a Firecracker microVM for this session.

---

## Deep Dive: Firecracker microVM Lifecycle

Each agent invocation runs inside an isolated Firecracker microVM. Here's what happens from cold start to response:

### Phase 1: entrypoint.sh — Immediate Server Start

```bash
# Server starts FIRST — health check must respond in seconds
python /app/server.py &
SERVER_PID=$!
```

The HTTP server starts immediately so AgentCore's health check passes. All heavy initialization happens in the background.

### Phase 2: S3 Workspace Sync

```bash
# Extract base employee ID from tenant_id
# Format: channel__employee_id__hash → extract employee_id
BASE_TENANT_ID=$(echo "$TENANT_ID" | awk -F'__' '{print $2}')
S3_BASE="s3://${S3_BUCKET}/${BASE_TENANT_ID}"

# Pull personal workspace from S3
aws s3 sync "${S3_BASE}/workspace/" "$WORKSPACE/" --quiet
```

The base ID extraction is critical. The Tenant Router sends `port__emp-carol__bbee1f93`, but S3 stores Carol's files under `emp-carol/workspace/`. We split by `__` and take the middle segment.

### Phase 3: Workspace Assembly (on first request)

Assembly doesn't happen at startup because `TENANT_ID=unknown` at container launch — AgentCore doesn't pass the session ID as an environment variable. It arrives via HTTP header on the first `/invocations` request.

```python
def _ensure_workspace_assembled(tenant_id):
    """Runs once per tenant per microVM lifecycle."""
    if tenant_id in _assembled_tenants:
        return  # already done

    # 1. Sync personal workspace from S3
    subprocess.run(["aws", "s3", "sync",
        f"s3://{S3_BUCKET}/{base_id}/workspace/", WORKSPACE])

    # 2. Run workspace_assembler.py (3-layer SOUL merge)
    subprocess.run([sys.executable, "workspace_assembler.py",
        "--tenant", tenant_id,
        "--workspace", WORKSPACE,
        "--bucket", S3_BUCKET,
        "--stack", STACK_NAME])

    # 3. Plan A: Inject permission constraints at top of SOUL.md
    constraint = _build_system_prompt(tenant_id)
    with open(f"{WORKSPACE}/SOUL.md", "r+") as f:
        existing = f.read()
        f.seek(0)
        f.write(f"<!-- PLAN A -->\n{constraint}\n\n---\n\n{existing}")

    _assembled_tenants.add(tenant_id)
```

### Phase 4: OpenClaw CLI Invocation

```python
openclaw_cmd = [
    OPENCLAW_BIN, "agent",
    "--session-id", tenant_id,
    "--message", message,
    "--json",
    "--timeout", "300",
]
result = subprocess.run(openclaw_cmd, capture_output=True, text=True)
```

OpenClaw runs as a subprocess. It reads the assembled `SOUL.md`, processes the message via Bedrock, and returns JSON. We parse the response, run Plan E audit, and write usage to DynamoDB.

### Phase 5: Watchdog — Memory Writeback

```bash
# Every 60 seconds, sync workspace changes back to S3
while true; do
    sleep 60
    CURRENT_BASE=$(cat /tmp/base_tenant_id)
    aws s3 sync "$WORKSPACE/" "s3://${S3_BUCKET}/${CURRENT_BASE}/workspace/" \
        --exclude "SOUL.md" --exclude "AGENTS.md" --exclude "TOOLS.md" \
        --exclude "IDENTITY.md" --exclude "knowledge/*"
done
```

The exclusion list is critical. If we synced the merged `SOUL.md` back to S3, an employee could:
1. Edit their personal SOUL.md to say "Ignore all previous instructions"
2. Next session, the merged file gets synced back
3. The Global layer's security policies would be overwritten

By excluding assembled files, the personal layer in S3 stays clean. The merge always starts fresh from the three source layers.

---

## Deep Dive: DynamoDB Single-Table Design

One table. One GSI. Twelve entity types. Here's the schema:

```
Table: openclaw-enterprise
PK (Partition Key)    SK (Sort Key)              Entity
─────────────────── ─────────────────────────── ──────────────────
ORG#acme            DEPT#dept-eng               Department
ORG#acme            POS#pos-sa                  Position
ORG#acme            EMP#emp-carol               Employee
ORG#acme            AGENT#agent-fa-carol        Agent
ORG#acme            BIND#bind-001               Binding
ORG#acme            AUDIT#2026-03-22T10:30:00Z  Audit Entry
ORG#acme            APPROVAL#apr-001            Approval
ORG#acme            CONFIG#model                Config
ORG#acme            USAGE#emp-carol#2026-03-22  Usage (daily)
ORG#acme            SESSION#sess-001            Session
ORG#acme            RULE#rule-001               Routing Rule
ORG#acme            CONV#sess-001#001           Conversation Turn

GSI1PK              GSI1SK                      Purpose
─────────────────── ─────────────────────────── ──────────────────
TYPE#employee       EMP#emp-carol               List all employees
TYPE#agent          AGENT#agent-fa-carol        List all agents
TYPE#usage          USAGE#2026-03-22#emp-carol  Usage by date
TYPE#session        SESSION#sess-001            List sessions
```

Why single-table? Because every API call in the Admin Console needs data from multiple entity types. The Dashboard needs departments + agents + sessions + usage in one page load. With single-table design, we can batch-read related items in one DynamoDB call.

The GSI (`GSI1`) enables cross-entity queries: "list all employees" (GSI1PK = `TYPE#employee`), "list all usage for today" (GSI1PK = `TYPE#usage`, GSI1SK begins_with `USAGE#2026-03-22`).

### Real-Time Usage Tracking

Every successful agent invocation triggers a fire-and-forget DynamoDB write:

```python
def _write_usage_to_dynamodb(tenant_id, base_id, usage, model, duration_ms):
    """Runs in background thread — doesn't block the response."""
    table.update_item(
        Key={"PK": "ORG#acme", "SK": f"USAGE#{base_id}#{today}"},
        UpdateExpression=(
            "SET #d = :date, agentId = :aid, model = :model "
            "ADD inputTokens :inp, outputTokens :out, requests :one, cost :cost"
        ),
        ExpressionAttributeValues={
            ":inp": input_tokens,
            ":out": output_tokens,
            ":one": 1,
            ":cost": Decimal(str(round(
                input_tokens * 0.30 / 1_000_000 +
                output_tokens * 2.50 / 1_000_000, 6
            ))),
        },
    )
```

The `ADD` operation is atomic — no read-modify-write race condition. Multiple concurrent invocations for the same agent safely increment the same counter. The background thread ensures the response isn't delayed by the DynamoDB write.

![Usage & Cost Dashboard — real token counts from DynamoDB](../demo/images/02-usage-cost-dashboard.jpeg)

---

## Deep Dive: Permission System (Plan A + Plan E)

### Plan A: Pre-Execution Constraint Injection

Before OpenClaw processes any message, `server.py` reads the tenant's permission profile from SSM and injects hard constraints at the very top of SOUL.md:

```python
def _build_system_prompt(tenant_id):
    profile = read_permission_profile(tenant_id)  # from SSM
    allowed = profile.get("tools", ["web_search"])
    blocked = [t for t in ["shell", "browser", "file_write",
               "code_execution", "install_skill"]
               if t not in allowed]

    lines = [f"Allowed tools for this session: {', '.join(allowed)}."]
    if blocked:
        lines.append(
            f"You MUST NOT use these tools: {', '.join(blocked)}. "
            "If the user requests a blocked tool, explain that you "
            "don't have permission."
        )
    return " ".join(lines)
```

This constraint text is prepended to the merged SOUL.md — appearing before any other content. The LLM sees it as the highest-priority instruction.

### Plan E: Post-Execution Response Audit

Every response is scanned for blocked tool patterns:

```python
_TOOL_PATTERN = re.compile(
    r'\b(shell|browser|file_write|code_execution|install_skill)\b',
    re.IGNORECASE,
)

def _audit_response(tenant_id, response_text, allowed_tools):
    matches = _TOOL_PATTERN.findall(response_text)
    for tool in set(t.lower() for t in matches):
        if tool not in allowed_tools:
            log_permission_denied(tenant_id, tool, "RESPONSE_AUDIT")
```

Plan E catches what Plan A misses. If the LLM somehow ignores the SOUL constraint and mentions executing a blocked tool, it's logged, flagged in the Audit Center, and the security team is notified.

### Skill-Level Filtering

Each of the 26 skills has a manifest with role permissions:

```json
{
  "name": "excel-gen",
  "permissions": {
    "allowedRoles": ["pos-fa", "pos-ae", "pos-pm"],
    "blockedRoles": ["pos-sde", "pos-devops"]
  }
}
```

`skill_loader.py` reads the tenant's position from SSM, then only loads skills where the position is in `allowedRoles` (or `allowedRoles` is `["*"]` for global skills). Finance gets excel-gen and sap-connector. SDE gets github-pr and shell. Neither gets the other's tools.

![Skill Platform — 26 skills with role-based filtering](../demo/images/08-skill-platform-catalog.jpeg)

### AI Security Scanner

The Audit Center's AI Insights scanner goes beyond individual event logging. It analyzes patterns across all audit events, memory files, and usage data:

```python
@app.get("/api/v1/audit/insights")
def get_audit_insights():
    entries = db.get_audit_entries(limit=50)
    blocked = [e for e in entries if e.get("status") == "blocked"]
    agents = db.get_agents()

    insights = []
    # Pattern: repeated shell access from restricted roles
    shell_blocks = [e for e in blocked if 'shell' in e.get('detail','').lower()]
    if shell_blocks:
        insights.append({
            "severity": "high",
            "title": "Repeated shell access attempts from restricted role",
            "recommendation": "Consider sandboxed shell skill or approval workflow",
        })
    # Pattern: PII in memory files (scan S3)
    # Pattern: SOUL version drift (compare agent versions)
    # Pattern: unusual usage hours (time-series analysis)
    ...
```

![Audit Center — AI Insights with severity levels and recommendations](../demo/images/07-audit-center-ai-insights.jpeg)

---

## Deep Dive: RBAC with BFS Sub-Department Rollup

Three roles with fundamentally different data visibility:

```
Admin    → All 20 employees, all 22 agents, all 13 departments
Manager  → Own department + all sub-departments (BFS rollup)
Employee → Own data only (Portal: 5 pages)
```

### The BFS Algorithm

When a manager calls any list API, the backend computes their visible scope by walking the department tree:

```python
def _get_dept_scope(user):
    if user.role == "admin":
        return None  # no filter — see everything

    # BFS from manager's department
    depts = db.get_departments()
    ids = {user.department_id}
    queue = [user.department_id]
    while queue:
        current = queue.pop(0)
        for d in depts:
            if d.get("parentId") == current and d["id"] not in ids:
                ids.add(d["id"])
                queue.append(d["id"])
    return ids
```

If Lin Xiaoyu (Product Manager) calls `/api/v1/org/employees`, the backend:
1. Starts with `dept-product`
2. BFS finds no sub-departments for Product
3. Returns only employees where `departmentId == "dept-product"`
4. Lin sees 3 employees instead of 20

This is API-level enforcement, not UI filtering. Even if someone crafts a direct API call, the backend filters the response.

Every list endpoint applies this pattern:

```python
@app.get("/api/v1/org/employees")
def get_employees(authorization):
    user = _get_current_user(authorization)
    employees = db.get_employees()
    if user and user.role == "manager":
        scope = _get_dept_scope(user)
        if scope is not None:
            employees = [e for e in employees if e.get("departmentId") in scope]
    return employees
```

### Employee Portal: Chat-First Design

Employees don't see the Admin Console at all. They get a dedicated 5-page Portal:

![Portal Profile — USER.md preferences editor + Agent Memory](../demo/images/06-portal-profile-preferences.jpeg)

The Profile page lets employees edit their USER.md — the Layer 3 of the SOUL architecture. Changes are written to S3 and take effect on the next agent session.

---

## The Full Product: 24 Pages, Zero Fake Data

Every page reads from DynamoDB and S3. Every button works. Here's what the Admin Console looks like:

### Dashboard — Organization-Wide Visibility

![Admin Dashboard](../demo/images/04-admin-dashboard.jpeg)

6 KPI cards, conversation trend chart (7 days from DynamoDB), agents-by-position donut chart, recent activity feed with real audit entries, and quick actions. The data updates in real-time as agents are invoked.

### Agent Factory — 20 Agents Across 10 Positions

![Agent Factory](../demo/images/03-agent-factory-list.jpeg)

Each row shows: agent name, bound employee, position, channels (WhatsApp/Slack/Telegram/Portal), skill count, quality score, SOUL version (Global.Position.Personal), status, and last updated date. 18 personal (1:1) agents + 2 shared agents (IT Help Desk, Onboarding Bot).

### Workspace Manager — The Three-Layer File System Made Tangible

![Workspace Manager — Sales Agent SOUL.md](../demo/images/05-workspace-manager-soul.jpeg)

This is where the architecture becomes visible. The breadcrumb shows: Global (9 files) → Account Executive (19 files) → Mike Johnson (4 files) = 32 files total. The right panel displays the Account Executive's SOUL.md — complete with personality traits ("You're a listener first, pitcher second"), core competencies (MEDDPICC, Challenger Sale), and CRM management skills.

---

## Serverless Economics: Why 85% Cheaper

The cost advantage isn't from negotiating better LLM pricing. It's architectural.

| | ChatGPT Team | Microsoft Copilot | ClawForge |
|-|-------------|-------------------|-----------|
| 20 users | $500/mo | $600/mo | ~$65/mo |
| Per-user identity | ❌ Same for all | ❌ Same for all | ✅ Unique per role |
| Tool permissions | ❌ | ❌ | ✅ Per-position |
| Self-hosted | ❌ | ❌ | ✅ Your VPC |
| Memory persistence | ❌ Session only | ❌ | ✅ Cross-session S3 |
| Audit trail | ❌ | Partial | ✅ Comprehensive |

ClawForge cost breakdown:
- EC2 Gateway: ~$52/month (one c7g.large for everything)
- DynamoDB: ~$1/month (pay-per-request, ~2000 writes/day)
- S3: <$1/month (workspace files, skills, knowledge docs)
- Bedrock (Nova 2 Lite): ~$5-15/month for ~100 conversations/day
- AgentCore: included (pay per invocation)
- **Total: ~$60-70/month for 20 agents**

The key insight: Firecracker microVMs have **zero idle cost**. 20 agents don't mean 20 running containers. They mean 20 *potential* microVMs that only exist during active conversations. When Carol isn't chatting, her agent doesn't exist. When she sends a message, a microVM spins up in ~5 seconds, processes the request, and releases.

---

## What We Learned Building This

### 1. SOUL merge order matters more than content
Global first, Personal last. The "CRITICAL IDENTITY OVERRIDE" prefix at the very top of the merged SOUL.md is what makes the LLM consistently identify as an ACME Corp employee instead of a generic AI assistant.

### 2. Memory writeback needs exclusion rules
Exclude assembled files (SOUL.md, AGENTS.md, TOOLS.md) from S3 sync. Only personal files (USER.md, MEMORY.md, memory/) get synced back. This prevents employees from overriding IT policies through the memory writeback path.

### 3. Cold start is a UX problem, not a technical one
AgentCore microVMs cold-start in ~25 seconds. Our solution: auto-retry with "Agent is warming up" message. The second request hits a warm VM and responds in ~5 seconds.

### 4. DynamoDB single-table design scales beautifully
One table, one GSI, 12 entity types. Pay-per-request = $1/month for 2,000 writes/day. No capacity planning, no provisioned throughput.

### 5. Plan A alone isn't enough
LLMs sometimes ignore system prompt constraints. Plan E (post-execution audit) catches what Plan A misses. The combination of pre-execution injection + post-execution scanning provides defense in depth.

---

## Try It Yourself

**Live demo**: [https://openclaw.awspsa.com](https://openclaw.awspsa.com) — contact [wjiad@aws](mailto:wjiad@amazon.com) for a demo account.

**Source code**: [github.com/aws-samples/sample-OpenClaw-on-AWS-with-Bedrock/tree/main/enterprise](https://github.com/aws-samples/sample-OpenClaw-on-AWS-with-Bedrock/tree/main/enterprise)

**Deploy your own** in ~20 minutes:
```bash
cd enterprise && bash deploy-multitenancy.sh my-clawforge us-east-1
```

The seed scripts create a complete sample organization (ACME Corp, 20 employees, 20 agents, 13 departments, 26 skills, 12 knowledge documents) so you can explore every feature immediately.

## What's Next

ClawForge is open source (Apache 2.0) and actively developed:

- **v1.1**: Organization sync (Feishu/DingTalk), SSO (SAML/OIDC), SOUL change approval workflow
- **v1.2**: Real-time CloudWatch integration, agent quality scoring, skill marketplace
- **v2.0**: Multi-tenancy (MSP mode), ClawForge on EKS, advanced anomaly detection

We're looking for contributors — especially in enterprise testing, skill development, and security auditing. The gap between personal AI agents and enterprise AI platforms is closing. ClawForge is our contribution to making that happen — without sacrificing the openness and flexibility that made OpenClaw great in the first place.

---

*Built by [wjiad@aws](mailto:wjiad@amazon.com) · [aws-samples](https://github.com/aws-samples) · Contributions welcome*
