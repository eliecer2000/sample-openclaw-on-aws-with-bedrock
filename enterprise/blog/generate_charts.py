"""
ClawForge Blog — Chart & Diagram Generation v2
Uses `diagrams` library for architecture/flow diagrams (AWS icons).
Uses matplotlib for data visualizations.
Run: cd enterprise/blog && python3 generate_charts.py
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
os.makedirs(OUT, exist_ok=True)

# Dark theme colors
BG = '#0f1117'
CARD = '#1a1d27'
BORDER = '#2a2d3a'
PRIMARY = '#6366f1'
ORANGE = '#f97316'
GREEN = '#22c55e'
RED = '#ef4444'
YELLOW = '#f59e0b'
CYAN = '#06b6d4'
TEXT = '#e2e8f0'
MUTED = '#94a3b8'

def setup_dark(fig, ax):
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(CARD)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ['top','right']: ax.spines[spine].set_visible(False)
    for spine in ['bottom','left']: ax.spines[spine].set_color(BORDER)
    for label in ax.get_xticklabels() + ax.get_yticklabels(): label.set_color(MUTED)


# ============================================================
# Diagram 1: System Architecture (diagrams library)
# ============================================================
def diagram_system_architecture():
    from diagrams import Diagram, Cluster, Edge
    from diagrams.aws.compute import EC2
    from diagrams.aws.database import Dynamodb
    from diagrams.aws.storage import S3
    from diagrams.aws.ml import Bedrock
    from diagrams.aws.management import SystemsManager, Cloudwatch
    from diagrams.aws.security import IAM
    from diagrams.aws.network import CloudFront
    from diagrams.onprem.container import Docker
    from diagrams.onprem.client import Users
    from diagrams.saas.chat import Telegram, Slack, Discord
    from diagrams.programming.framework import React

    path = os.path.join(OUT, "02-system-architecture")

    with Diagram("ClawForge on AgentCore — System Architecture",
                 filename=path, show=False, direction="TB",
                 graph_attr={"bgcolor": "#0d1117", "fontcolor": "#e2e8f0",
                             "fontsize": "14", "pad": "0.5", "dpi": "150",
                             "rankdir": "TB"}):

        # Users
        with Cluster("User Channels", graph_attr={"bgcolor": "#1a1d2710", "style": "dashed", "color": "#2a2d3a"}):
            wa = Users("WhatsApp")
            tg = Telegram("Telegram")
            sl = Slack("Slack")
            dc = Discord("Discord")

        # Gateway
        with Cluster("EC2 Gateway (~$52/mo)", graph_attr={"bgcolor": "#1e293b", "color": "#3b82f6"}):
            gw = EC2("OpenClaw\nGateway\n:18789")
            router = EC2("Tenant\nRouter\n:8090")
            console = React("Admin Console\n:8099\n24 pages")

        # AgentCore
        with Cluster("Bedrock AgentCore Runtime", graph_attr={"bgcolor": "#1c1917", "color": "#f97316"}):
            with Cluster("Firecracker microVM (per tenant)", graph_attr={"bgcolor": "#27201a", "color": "#fb923c", "style": "dashed"}):
                entry = Docker("entrypoint.sh\nS3 sync + skills")
                server = Docker("server.py\nPlan A + Plan E")
                assembler = Docker("workspace_assembler\n3-layer SOUL merge")
                openclaw = Docker("OpenClaw CLI\n(unmodified)")

        # AWS Services
        with Cluster("AWS Services", graph_attr={"bgcolor": "#0f1117", "color": "#2a2d3a"}):
            dynamo = Dynamodb("DynamoDB\norg, audit, usage")
            s3 = S3("S3\nSOUL, skills\nmemory, knowledge")
            ssm = SystemsManager("SSM\ntenant→position\nAPI keys")
            bedrock = Bedrock("Bedrock\nNova 2 Lite\nSonnet, Pro")
            cw = Cloudwatch("CloudWatch\nagent logs")
            iam = IAM("IAM Roles\nleast privilege")

        # Edges
        wa >> Edge(color="#64748b") >> gw
        tg >> Edge(color="#64748b") >> gw
        sl >> Edge(color="#64748b") >> gw
        dc >> Edge(color="#64748b") >> gw

        gw >> Edge(label="derive tenant_id", color="#3b82f6") >> router
        router >> Edge(label="invoke", color="#f97316") >> entry

        entry >> server >> assembler >> openclaw

        openclaw >> Edge(color="#f97316") >> bedrock
        assembler >> Edge(color="#64748b", style="dashed") >> s3
        assembler >> Edge(color="#64748b", style="dashed") >> ssm
        server >> Edge(color="#64748b", style="dashed") >> dynamo
        server >> Edge(color="#64748b", style="dashed") >> cw
        console >> Edge(color="#64748b", style="dashed") >> dynamo
        console >> Edge(color="#64748b", style="dashed") >> s3

    print("  02-system-architecture.png")


# ============================================================
# Diagram 2: Request Flow — Sequence Style (diagrams library)
# ============================================================
def diagram_request_flow():
    from diagrams import Diagram, Cluster, Edge
    from diagrams.aws.compute import EC2
    from diagrams.aws.ml import Bedrock
    from diagrams.aws.management import SystemsManager
    from diagrams.aws.storage import S3
    from diagrams.onprem.container import Docker
    from diagrams.onprem.client import User

    path = os.path.join(OUT, "03-request-flow")

    with Diagram("Request Flow: Carol says 'Run git status'",
                 filename=path, show=False, direction="LR",
                 graph_attr={"bgcolor": "#0d1117", "fontcolor": "#e2e8f0",
                             "fontsize": "12", "pad": "0.4", "dpi": "150"}):

        carol = User("Carol\n(Finance)")
        gw = EC2("Gateway +\nTenant Router")
        ssm = SystemsManager("SSM\nemp-carol→pos-fa")

        with Cluster("Firecracker microVM", graph_attr={"bgcolor": "#1c1917", "color": "#f97316"}):
            asm = Docker("workspace\nassembler\nmerge 3 layers")
            srv = Docker("server.py\nPlan A inject")
            oc = Docker("OpenClaw CLI\nreads SOUL.md")

        bedrock = Bedrock("Bedrock\nNova 2 Lite")

        carol >> Edge(label="(1) 'Run git status'", color="#06b6d4") >> gw
        gw >> Edge(label="(2) tenant_id", color="#3b82f6") >> ssm
        ssm >> Edge(label="(3) pos-fa", color="#3b82f6", style="dashed") >> asm
        asm >> Edge(label="(4) SOUL merged", color="#f97316") >> srv
        srv >> Edge(label="(5) Plan A: DENY shell", color="#ef4444") >> oc
        oc >> Edge(label="(6) invoke", color="#f97316") >> bedrock
        bedrock >> Edge(label="(7) 'I can't use shell...'", color="#22c55e", style="bold") >> carol

    print("  03-request-flow.png")


# ============================================================
# Chart 1: Three-Layer SOUL (matplotlib — clean version)
# ============================================================
def chart_soul_layers():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.axis('off')

    layers = [
        (0.5, 4.0, 9, 1.1, 'LAYER 1: GLOBAL', '(IT Locked — CISO + CTO approval)', '#ef4444',
         'Company policies · Security red lines · Data handling rules\n"Never share customer PII. Never execute rm -rf."'),
        (0.5, 2.5, 9, 1.1, 'LAYER 2: POSITION', '(Department Admin managed)', '#3b82f6',
         'Role expertise · Tool permissions · Knowledge scope\n"You are a Finance Analyst. Use excel-gen, not shell."'),
        (0.5, 1.0, 9, 1.1, 'LAYER 3: PERSONAL', '(Employee self-service)', '#22c55e',
         'Communication preferences · Custom instructions\n"I prefer concise answers. Always use TypeScript."'),
    ]

    for x, y, w, h, title, subtitle, color, desc in layers:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                             facecolor=color + '12', edgecolor=color, linewidth=2.5)
        ax.add_patch(box)
        ax.text(x + 0.4, y + 0.78, title, fontsize=13, fontweight='bold', color=color, family='sans-serif')
        ax.text(x + 0.4 + len(title)*0.12, y + 0.78, f'  {subtitle}', fontsize=9, color=MUTED, family='sans-serif')
        ax.text(x + 0.4, y + 0.15, desc, fontsize=9.5, color='#b0b8c8', linespacing=1.4)

    # Merge arrow
    for y in [3.9, 2.4]:
        ax.annotate('', xy=(5, y), xytext=(5, y + 0.1),
                    arrowprops=dict(arrowstyle='->', color=ORANGE, lw=2))

    # Result box
    result = FancyBboxPatch((2.5, -0.15), 5, 0.7, boxstyle="round,pad=0.1",
                            facecolor=ORANGE + '20', edgecolor=ORANGE, linewidth=2)
    ax.add_patch(result)
    ax.text(5, 0.2, 'MERGED SOUL.md  →  what OpenClaw reads', fontsize=11,
            fontweight='bold', color=ORANGE, ha='center', family='sans-serif')

    ax.annotate('', xy=(5, 0.55), xytext=(5, 0.9),
                arrowprops=dict(arrowstyle='->', color=ORANGE, lw=2.5))

    ax.set_xlim(0, 10)
    ax.set_ylim(-0.5, 5.5)
    fig.tight_layout(pad=0.5)
    fig.savefig(f'{OUT}/01-soul-three-layers.png', dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print("  01-soul-three-layers.png")


# ============================================================
# Chart 4: Cost Comparison (matplotlib bar chart)
# ============================================================
def chart_cost_comparison():
    fig, ax = plt.subplots(figsize=(9, 4))
    setup_dark(fig, ax)

    products = ['ChatGPT Team\n(20 users)', 'Microsoft Copilot\n(20 users)', 'ClawForge\non AgentCore']
    costs = [500, 600, 65]
    colors = ['#475569', '#475569', ORANGE]

    bars = ax.barh(products, costs, color=colors, height=0.55, edgecolor='none')
    for bar, cost, color in zip(bars, costs, colors):
        ax.text(bar.get_width() + 15, bar.get_y() + bar.get_height()/2,
                f'${cost}/mo', va='center', fontsize=12, fontweight='bold',
                color=ORANGE if cost == 65 else MUTED)

    ax.set_xlabel('Monthly Cost (20 AI Agents)', color=MUTED, fontsize=10)
    ax.set_title('Enterprise AI Agent Cost Comparison', color=TEXT, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlim(0, 780)
    ax.invert_yaxis()

    # Savings callout
    ax.annotate('85% cheaper', xy=(65, 2), xytext=(300, 2.35),
                fontsize=15, fontweight='bold', color=GREEN,
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=2),
                ha='center')

    fig.tight_layout()
    fig.savefig(f'{OUT}/04-cost-comparison.png', dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print("  04-cost-comparison.png")


# ============================================================
# Diagram 5: Permission Pipeline (diagrams library)
# ============================================================
def diagram_permission_pipeline():
    from diagrams import Diagram, Cluster, Edge
    from diagrams.aws.database import Dynamodb
    from diagrams.onprem.client import User
    from diagrams.onprem.container import Docker
    from diagrams.aws.security import IAM

    path = os.path.join(OUT, "05-permission-system")

    with Diagram("Permission Enforcement: Plan A + Plan E",
                 filename=path, show=False, direction="LR",
                 graph_attr={"bgcolor": "#0d1117", "fontcolor": "#e2e8f0",
                             "fontsize": "12", "pad": "0.4", "dpi": "150"}):

        msg = User("Message In\nCarol: 'Run git status'")

        with Cluster("Pre-Execution", graph_attr={"bgcolor": "#1c1917", "color": "#ef4444"}):
            plan_a = IAM("PLAN A\nSOUL.md injection\nDENY: shell")

        with Cluster("LLM Processing", graph_attr={"bgcolor": "#1c1917", "color": "#f97316"}):
            llm = Docker("OpenClaw + Bedrock\nSelf-enforces\nSOUL rules")

        with Cluster("Post-Execution", graph_attr={"bgcolor": "#0d2818", "color": "#22c55e"}):
            plan_e = IAM("PLAN E\nResponse audit\nScan blocked tools")
            audit = Dynamodb("DynamoDB\nAudit trail\nAI Insights")

        msg >> Edge(color="#06b6d4") >> plan_a
        plan_a >> Edge(label="allowed", color="#22c55e") >> llm
        plan_a >> Edge(label="BLOCKED", color="#ef4444", style="dashed") >> audit
        llm >> Edge(color="#f97316") >> plan_e
        plan_e >> Edge(color="#22c55e") >> audit

    print("  05-permission-system.png")


# ============================================================
# Chart 6: RBAC Scoping (matplotlib — clean)
# ============================================================
def chart_rbac_scoping():
    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.axis('off')

    roles = [
        ('ADMIN', '#ef4444', 'Zhang San\nIT Admin', 
         '• All 20 employees\n• All 22 agents\n• All 13 departments\n• Full settings\n• 19 admin pages'),
        ('MANAGER', '#f59e0b', 'Lin Xiaoyu\nProduct Dept Head',
         '• Product dept only (3)\n• Own dept agents\n• BFS sub-dept rollup\n• No settings page\n• 18 admin pages'),
        ('EMPLOYEE', '#22c55e', 'Carol Zhang\nFinance Analyst',
         '• Own data only\n• Portal: Chat\n• Profile, Usage\n• Skills, Requests\n• 5 portal pages'),
    ]

    for i, (label, color, name, desc) in enumerate(roles):
        x = 0.3 + i * 3.3
        box = FancyBboxPatch((x, 0.3), 2.8, 3.5, boxstyle="round,pad=0.12",
                             facecolor=color + '08', edgecolor=color, linewidth=2.5)
        ax.add_patch(box)
        ax.text(x + 1.4, 3.5, label, fontsize=14, fontweight='bold', color=color, ha='center', family='monospace')
        ax.text(x + 1.4, 2.9, name, fontsize=10, color=TEXT, ha='center', linespacing=1.3)
        ax.text(x + 0.3, 0.6, desc, fontsize=9, color=MUTED, linespacing=1.6, va='bottom')

    # Scope arrows
    for x in [3.1, 6.4]:
        ax.annotate('', xy=(x + 0.2, 2.0), xytext=(x, 2.0),
                    arrowprops=dict(arrowstyle='->', color=MUTED, lw=2))
        ax.text(x + 0.1, 2.3, 'scope\nnarrows', fontsize=7, color=MUTED, ha='center')

    ax.set_xlim(0, 10.2)
    ax.set_ylim(0, 4.2)
    fig.tight_layout(pad=0.3)
    fig.savefig(f'{OUT}/06-rbac-scoping.png', dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print("  06-rbac-scoping.png")


# ============================================================
# Generate all
# ============================================================
if __name__ == '__main__':
    print("Generating ClawForge blog charts v2...")
    chart_soul_layers()
    diagram_system_architecture()
    diagram_request_flow()
    chart_cost_comparison()
    diagram_permission_pipeline()
    chart_rbac_scoping()
    print(f"\nDone! Charts in {OUT}/")
